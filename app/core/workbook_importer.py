"""Workbook Importer Service for Dan Budgeting Excel Sheets.

Extracts budget configuration, monthly utility records, peer expense ledgers,
groceries remittances, apartment expenses, dentist tracker, chore chart,
pajah toga rentals, and holiday lists from local Excel workbooks (.xlsx)
and seeds the local application storage without exposing private data to Git.
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openpyxl

from .decimal_utils import to_decimal, round_up_excel, round_currency, quantize_currency, ZERO
from .bills_engine import calculate_ytd_summary
from .settlement_engine import calculate_master_settlement_matrix
from .apt_expenses_engine import (
    ExpenditureItem,
    SubtotalItem,
    ExpeditionItem,
    calculate_house_expenditures,
    calculate_application_expenses,
    calculate_dentist_tracker,
    calculate_expedition_expenses,
)
from .storage import StorageService
from .chores_engine import ChoreEngine, ChoreEntry
from .pajah_engine import PajahOwnerRecord, calculate_pajah_summary



logger = logging.getLogger(__name__)

DEFAULT_WORKBOOK_PATH = Path("references/Dan BudgetingV3.xlsx")


class WorkbookImporter:
    """Imports user data from Dan Budgeting Excel workbook into the application state."""

    def __init__(self, workbook_path: Optional[str | Path] = None):
        self.workbook_path = Path(workbook_path or DEFAULT_WORKBOOK_PATH)

    def exists(self) -> bool:
        """Check if the source workbook exists locally."""
        return self.workbook_path.exists() and self.workbook_path.is_file()

    def import_to_storage(self, storage: Optional[StorageService] = None) -> Tuple[bool, str]:
        """Parse the workbook and write the resulting data to local storage."""
        if not self.exists():
            return False, f"Workbook not found at {self.workbook_path}"

        try:
            data = self.parse_workbook()
            target_storage = storage or StorageService()
            success = target_storage.save_data(data, create_backup=True)
            if success:
                return True, f"Successfully imported workbook data from {self.workbook_path.name}"
            return False, "Failed to persist imported data to local storage"
        except Exception as e:
            logger.exception("Error importing workbook: %s", e)
            return False, f"Import error: {str(e)}"

    def parse_workbook(self) -> Dict[str, Any]:
        """Parse all known sheets in the workbook into a clean structured dict."""
        wb = openpyxl.load_workbook(self.workbook_path, data_only=True)

        holidays = self._parse_holidays(wb)
        schedule = self._parse_schedule(wb, holidays)
        bills = self._parse_monthly_bills(wb)
        settlements = self._parse_calumpang(wb)
        groceries = self._parse_mama_groceries(wb)
        salary = self._parse_salary_profile(wb, schedule)
        apt_expenses = self._parse_apt_expenses(wb)
        chores = self._parse_chores(wb)
        pajah = self._parse_pajah(wb)
        budget_extras = self._parse_budget_extras(wb)

        return {
            "version": "1.0.0",
            "imported_at": datetime.now().isoformat(),
            "source_file": self.workbook_path.name,
            "salary": salary,
            "schedule": schedule,
            "bills": bills,
            "settlements": settlements,
            "groceries": groceries,
            "apt_expenses": apt_expenses,
            "chores": chores,
            "pajah": pajah,
            "budget_extras": budget_extras,
        }

    def _parse_holidays(self, wb: openpyxl.Workbook) -> List[Dict[str, Any]]:
        """Parse 'Holidays' sheet into holiday records (21 entries)."""
        holidays: List[Dict[str, Any]] = []
        if "Holidays" not in wb.sheetnames:
            return holidays

        ws = wb["Holidays"]
        for r in range(2, ws.max_row + 1):
            date_val = ws.cell(r, 1).value
            if not date_val:
                continue

            date_str = ""
            if isinstance(date_val, (datetime, date)):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val).strip()

            name = str(ws.cell(r, 3).value or "").strip()
            law_type = str(ws.cell(r, 4).value or "").strip()
            scope = str(ws.cell(r, 5).value or "Nationwide").strip()
            is_regular = "regular" in law_type.lower()

            if date_str and name:
                holidays.append({
                    "date": date_str,
                    "name": name,
                    "type": "regular" if is_regular else "special",
                    "law_type": law_type,
                    "scope": scope,
                })
        return holidays

    def _parse_schedule(self, wb: openpyxl.Workbook, holidays: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract daily teaching schedule and allowance rates from 'Current Budget'."""
        daily_units = {"Mon": "0", "Tue": "0", "Wed": "0", "Thu": "0", "Fri": "0", "Sat": "0", "Sun": "0"}
        hourly_rate = "198.85"
        daily_food = "200.00"
        daily_transpo = "55.00"

        if "Current Budget" in wb.sheetnames:
            ws = wb["Current Budget"]
            rate_val = ws.cell(3, 5).value
            if rate_val:
                hourly_rate = str(to_decimal(rate_val))

            day_map = [("Mon", 7), ("Tue", 8), ("Wed", 9), ("Thu", 10), ("Fri", 11), ("Sat", 12), ("Sun", 13)]
            for day_key, col_idx in day_map:
                u_val = ws.cell(4, col_idx).value
                if u_val is not None:
                    daily_units[day_key] = str(to_decimal(u_val))

            t_val = ws.cell(9, 7).value
            if t_val:
                daily_transpo = str(to_decimal(t_val))

            f_val = ws.cell(10, 7).value
            if f_val:
                daily_food = str(to_decimal(f_val))

        return {
            "hourly_rate": hourly_rate,
            "daily_units": daily_units,
            "daily_food_rate": daily_food,
            "daily_transport_rate": daily_transpo,
            "holidays": holidays,
        }

    def _parse_salary_profile(self, wb: openpyxl.Workbook, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Extract baseline monthly salary information."""
        monthly_basic = "30000.00"
        allowances = "0.00"

        if "Current Budget" in wb.sheetnames:
            ws = wb["Current Budget"]
            total_cash = ws.cell(8, 2).value
            if total_cash:
                monthly_basic = str(to_decimal(total_cash))

        return {
            "monthly_basic": monthly_basic,
            "allowances": allowances,
            "hourly_rate": schedule.get("hourly_rate", "198.85"),
            "employment_type": "private",
            "overtime": "0.00",
            "night_diff": "0.00",
            "custom_deductions": [],
        }

    def _parse_monthly_bills(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Parse tenant utility records, rolling averages, and latest month recipient table."""
        tenants: List[str] = ["Dan", "Jaco", "Troy"]
        my_tenant_name = "Dan"
        items: List[Dict[str, Any]] = []
        history: List[Dict[str, Any]] = []
        latest_breakdown: List[Dict[str, Any]] = []

        if "Monthly Bills" not in wb.sheetnames:
            return {"tenants": tenants, "my_tenant_name": my_tenant_name, "items": items, "history": history, "latest_breakdown": latest_breakdown}

        ws = wb["Monthly Bills"]
        headers = [str(ws.cell(2, c).value or "").strip() for c in range(1, ws.max_column + 1)]

        detected_tenants: List[str] = []
        tenant_col_indices: Dict[str, int] = {}
        for c_idx in range(8, len(headers) + 1):
            name = str(ws.cell(2, c_idx).value or "").strip()
            if name and name not in ["Total", "Month", "Total Utils w/ int", "LATEST MONTH BREAKDOWN", "Name", "Total per person", "Status"]:
                detected_tenants.append(name)
                tenant_col_indices[name] = c_idx

        if detected_tenants:
            tenants = detected_tenants

        for r in range(3, ws.max_row + 1):
            month_val = ws.cell(r, 1).value
            if not month_val:
                continue

            month_str = ""
            if isinstance(month_val, (datetime, date)):
                month_str = month_val.strftime("%Y-%m-%d")
            else:
                month_str = str(month_val).strip()

            rent = str(to_decimal(ws.cell(r, 2).value or 0))
            water = str(to_decimal(ws.cell(r, 3).value or 0))
            electricity = str(to_decimal(ws.cell(r, 4).value or 0))
            internet = str(to_decimal(ws.cell(r, 5).value or 0))
            utils_with_fee = str(to_decimal(ws.cell(r, 6).value or 0))
            total = str(to_decimal(ws.cell(r, 7).value or 0))
            per_person = str(to_decimal(ws.cell(r, 11).value or 0))
            status_val = str(ws.cell(r, 12).value or "").strip()

            active_for_month = []
            for t_name, c_idx in tenant_col_indices.items():
                cell_val = str(ws.cell(r, c_idx).value or "").strip().lower()
                if cell_val in ["true", "1", "yes", "paid", "y"]:
                    active_for_month.append(t_name)

            if not active_for_month and tenants:
                active_for_month = list(tenants)

            history.append({
                "date": month_str,
                "rent": rent,
                "water": water,
                "electricity": electricity,
                "internet": internet,
                "utils_with_fee": utils_with_fee,
                "total": total,
                "per_person": per_person,
                "status": status_val if status_val else ("Paid" if to_decimal(total) > ZERO else "Pending"),
                "active_tenants": active_for_month,
            })

        if history:
            latest = history[-1]
            active_tenants = latest.get("active_tenants", tenants)
            items = [
                {"name": "Rent", "category": "Rent", "total_amount": latest["rent"], "is_active": True, "active_tenants": active_tenants},
                {"name": "Water", "category": "Water", "total_amount": latest["water"], "is_active": True, "active_tenants": active_tenants},
                {"name": "Electricity", "category": "Electricity", "total_amount": latest["electricity"], "is_active": True, "active_tenants": active_tenants},
                {"name": "Internet", "category": "Internet", "total_amount": latest["internet"], "is_active": True, "active_tenants": active_tenants},
            ]

        # Parse Latest Month Breakdown (N3:Q6)
        # N4: Dan, O4: Rent 2500, P4: Utilities -, Q4: Total Bills 2500
        # N5: Jaco, O5: -, P5: -, Q5: -
        # N6: Troy, O6: 2500, P6: 3175, Q6: 5675
        for r in range(4, 7):
            name = str(ws.cell(r, 14).value or "").strip()
            if name:
                r_val = ws.cell(r, 15).value
                u_val = ws.cell(r, 16).value
                tot_val = ws.cell(r, 17).value
                latest_breakdown.append({
                    "name": name,
                    "rent_to_tita_beth": str(to_decimal(r_val) if str(r_val).strip() != "-" else Decimal("0.00")),
                    "utilities_to_dan": str(to_decimal(u_val) if str(u_val).strip() != "-" else Decimal("0.00")),
                    "total_bills": str(to_decimal(tot_val) if str(tot_val).strip() != "-" else Decimal("0.00")),
                })

        ytd_summary = calculate_ytd_summary(history)

        return {
            "tenants": tenants,
            "my_tenant_name": my_tenant_name,
            "items": items,
            "history": history,
            "latest_breakdown": latest_breakdown,
            "ytd_summary": ytd_summary,
        }

    def _parse_calumpang(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Extract all Calumpang blocks: Troy 50/50, Monji, Con, DJ Gastos, and Master Matrix."""
        peer_name = "Troy"
        dan_ratio = "0.50"
        items: List[Dict[str, Any]] = []
        dj_gastos: List[Dict[str, Any]] = []
        master_matrix: Dict[str, Any] = {"troy": [], "jaco": [], "dan": []}

        if "Calumpang" not in wb.sheetnames:
            return {"peer_name": peer_name, "dan_ratio": dan_ratio, "items": items, "dj_gastos": dj_gastos, "master_matrix": master_matrix}

        ws = wb["Calumpang"]
        # Troy 50/50 items (A2:C25)
        for r in range(2, 26):
            desc = str(ws.cell(r, 1).value or "").strip()
            price_val = ws.cell(r, 2).value
            if not desc or price_val is None:
                continue

            price_dec = to_decimal(price_val)
            if price_dec <= Decimal("0"):
                continue

            dan_share = round_up_excel(price_dec / Decimal("2"), 0)
            peer_share = round_currency(price_dec - dan_share)

            items.append({
                "id": f"calumpang_{r}",
                "description": desc,
                "total_amount": str(price_dec),
                "dan_share": str(dan_share),
                "peer_share": str(peer_share),
                "paid_by": "Dan",
                "status": "pending",
                "date": datetime.now().strftime("%Y-%m-%d"),
            })

        # DJ GASTOS (A34:B59)
        for r in range(34, 60):
            item_desc = str(ws.cell(r, 1).value or "").strip()
            item_price = ws.cell(r, 2).value
            if item_desc and str(item_desc) != "0" and item_price is not None:
                p_dec = to_decimal(item_price)
                if p_dec > Decimal("0"):
                    dj_gastos.append({
                        "item": item_desc,
                        "price": str(p_dec),
                    })

        # Master Matrix (M2:U25)
        # M: Troy amount, N: Troy !Paid?, O: Troy note
        # P: Jaco amount, Q: Jaco !Paid?, R: Jaco note
        # S: Dan amount, T: Dan Paid, U: Dan note
        for r in range(2, 24):
            # Troy items
            tm_amt = ws.cell(r, 13).value
            if tm_amt is not None and str(tm_amt).strip() != "":
                amt_dec = to_decimal(tm_amt)
                if amt_dec > ZERO:
                    master_matrix["troy"].append({
                        "amount": str(amt_dec),
                        "is_paid": bool(ws.cell(r, 14).value),
                        "note": str(ws.cell(r, 15).value or "").strip(),
                    })
            # Jaco
            jm_amt = ws.cell(r, 16).value
            if jm_amt is not None and str(jm_amt).strip() != "":
                amt_dec = to_decimal(jm_amt)
                if amt_dec > ZERO:
                    master_matrix["jaco"].append({
                        "amount": str(amt_dec),
                        "is_paid": bool(ws.cell(r, 17).value),
                        "note": str(ws.cell(r, 18).value or "").strip(),
                    })
            # Dan
            dm_amt = ws.cell(r, 19).value
            if dm_amt is not None and str(dm_amt).strip() != "":
                amt_dec = to_decimal(dm_amt)
                if amt_dec > ZERO:
                    master_matrix["dan"].append({
                        "amount": str(amt_dec),
                        "is_paid": bool(ws.cell(r, 20).value),
                        "note": str(ws.cell(r, 21).value or "").strip(),
                    })

        spotify_val = to_decimal(ws.cell(24, 13).value or "57.40")
        utils_val = to_decimal(ws.cell(25, 13).value or "3175.00")

        calculated_matrix = calculate_master_settlement_matrix(
            troy_entries=master_matrix["troy"],
            jaco_entries=master_matrix["jaco"],
            dan_entries=master_matrix["dan"],
            spotify_amount=spotify_val,
            troy_utilities=utils_val,
        )
        calculated_matrix["raw_entries"] = master_matrix


        return {
            "peer_name": peer_name,
            "dan_ratio": dan_ratio,
            "items": items,
            "dj_gastos": dj_gastos,
            "master_matrix": calculated_matrix,
        }


    def _parse_mama_groceries(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Extract grocery items and deductions from 'Mama Groceries'."""
        recipient_name = "Mama"
        items: List[Dict[str, Any]] = []
        deductions: List[Dict[str, Any]] = []

        if "Mama Groceries" not in wb.sheetnames:
            return {"recipient_name": recipient_name, "items": items, "deductions": deductions}

        ws = wb["Mama Groceries"]
        for r in range(6, ws.max_row + 1):
            item_desc = str(ws.cell(r, 2).value or "").strip()
            item_subtotal = ws.cell(r, 5).value or ws.cell(r, 4).value
            if item_desc and item_subtotal is not None:
                amt = to_decimal(item_subtotal)
                if amt > Decimal("0"):
                    items.append({
                        "id": f"grocery_{r}",
                        "description": item_desc,
                        "amount": str(amt),
                        "note": str(ws.cell(r, 6).value or "").strip(),
                    })

            ded_desc = str(ws.cell(r, 9).value or "").strip()
            ded_amt = ws.cell(r, 10).value
            if ded_desc and ded_amt is not None:
                damt = to_decimal(ded_amt)
                if damt > Decimal("0"):
                    deductions.append({
                        "id": f"deduction_{r}",
                        "description": ded_desc,
                        "amount": str(damt),
                        "note": "",
                    })

        return {
            "recipient_name": recipient_name,
            "items": items,
            "deductions": deductions,
        }

    def _parse_apt_expenses(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Extract all 6 sub-ledgers from 'Apt Expenses'."""
        house_items: List[Dict[str, Any]] = []
        app_items: List[Dict[str, Any]] = []
        dentist_billed: List[Dict[str, Any]] = []
        dentist_deductibles: List[Dict[str, Any]] = []
        snr_items: List[Dict[str, Any]] = []
        lorraine_items: List[Dict[str, Any]] = []
        expedition_items: List[Dict[str, Any]] = []

        if "Apt Expenses" not in wb.sheetnames:
            return {
                "house": house_items,
                "application": app_items,
                "dentist_billed": dentist_billed,
                "dentist_deductibles": dentist_deductibles,
                "snr": snr_items,
                "lorraine": lorraine_items,
                "expedition": expedition_items,
            }

        ws = wb["Apt Expenses"]

        # 1. House Expenditures (R3:R22)
        for r in range(3, 23):
            item = str(ws.cell(r, 1).value or "").strip()
            price = ws.cell(r, 3).value
            if item and price is not None and to_decimal(price) > ZERO:
                c = to_decimal(ws.cell(r, 2).value or 1)
                p = to_decimal(price)
                d = to_decimal(ws.cell(r, 4).value or 0)
                tot = (c * p) - d
                house_items.append({
                    "item": item,
                    "count": str(c),
                    "price": str(p),
                    "discount": str(d),
                    "total_price": str(quantize_currency(tot)),
                    "note": str(ws.cell(r, 6).value or "").strip(),
                })

        # 2. Application Expenses (R35:R41)
        for r in range(35, 42):
            lbl = str(ws.cell(r, 1).value or "").strip()
            p_val = ws.cell(r, 3).value
            if lbl and p_val is not None:
                c = to_decimal(ws.cell(r, 2).value or 1)
                p = to_decimal(p_val)
                app_items.append({
                    "label": lbl,
                    "count": str(c),
                    "price": str(p),
                    "subtotal": str(quantize_currency(c * p)),
                    "note": str(ws.cell(r, 5).value or "").strip(),
                })

        # 3. Dentist Billed (R46:R53)
        for r in range(46, 54):
            lbl = str(ws.cell(r, 1).value or "").strip()
            p_val = ws.cell(r, 3).value
            if lbl and p_val is not None and to_decimal(p_val) > ZERO:
                c = to_decimal(ws.cell(r, 2).value or 1)
                p = to_decimal(p_val)
                dentist_billed.append({
                    "label": lbl,
                    "count": str(c),
                    "price": str(p),
                    "subtotal": str(quantize_currency(c * p)),
                    "note": str(ws.cell(r, 5).value or "").strip(),
                })

        # Dentist Deductibles (R58:R64)
        for r in range(58, 65):
            lbl = str(ws.cell(r, 1).value or "").strip()
            p_val = ws.cell(r, 3).value
            if lbl and p_val is not None and to_decimal(p_val) != ZERO:
                c = to_decimal(ws.cell(r, 2).value or 1)
                p = to_decimal(p_val)
                dentist_deductibles.append({
                    "label": lbl,
                    "count": str(c),
                    "price": str(p),
                    "subtotal": str(quantize_currency(c * p)),
                    "note": str(ws.cell(r, 5).value or "").strip(),
                })

        # 4. SnR (R71:R78)
        for r in range(71, 79):
            lbl = str(ws.cell(r, 1).value or "").strip()
            p_val = ws.cell(r, 3).value
            if lbl and p_val is not None and to_decimal(p_val) > ZERO:
                snr_items.append({
                    "label": lbl,
                    "count": str(to_decimal(ws.cell(r, 2).value or 1)),
                    "price": str(to_decimal(p_val)),
                    "subtotal": str(quantize_currency(to_decimal(ws.cell(r, 2).value or 1) * to_decimal(p_val))),
                    "note": str(ws.cell(r, 5).value or "").strip(),
                })

        # 5. Lorraine (R115:R121)
        for r in range(115, 122):
            lbl = str(ws.cell(r, 1).value or "").strip()
            p_val = ws.cell(r, 3).value
            if lbl and p_val is not None and to_decimal(p_val) > ZERO:
                lorraine_items.append({
                    "label": lbl,
                    "count": str(to_decimal(ws.cell(r, 2).value or 1)),
                    "price": str(to_decimal(p_val)),
                    "subtotal": str(quantize_currency(to_decimal(ws.cell(r, 2).value or 1) * to_decimal(p_val))),
                    "note": str(ws.cell(r, 5).value or "").strip(),
                })

        # 6. Expedition (R128:R134)
        for r in range(128, 135):
            lbl = str(ws.cell(r, 1).value or "").strip()
            p_val = ws.cell(r, 3).value
            div_val = ws.cell(r, 6).value or 1
            if lbl and p_val is not None and to_decimal(p_val) > ZERO:
                c = to_decimal(ws.cell(r, 2).value or 1)
                p = to_decimal(p_val)
                div = to_decimal(div_val)
                sub = round_up_excel((p * c) / div, 0)
                expedition_items.append({
                    "label": lbl,
                    "count": str(c),
                    "price": str(p),
                    "divisor": str(div),
                    "subtotal": str(sub),
                    "note": str(ws.cell(r, 5).value or "").strip(),
                })

        house_summary = calculate_house_expenditures([
            ExpenditureItem(item=it["item"], count=to_decimal(it["count"]), price=to_decimal(it["price"]), discount=to_decimal(it["discount"]), note=it["note"])
            for it in house_items
        ])
        app_summary = calculate_application_expenses([
            SubtotalItem(label=it["label"], count=to_decimal(it["count"]), price=to_decimal(it["price"]), note=it["note"])
            for it in app_items
        ])
        dentist_summary = calculate_dentist_tracker(
            billed=[SubtotalItem(label=it["label"], count=to_decimal(it["count"]), price=to_decimal(it["price"]), note=it["note"]) for it in dentist_billed],
            deductibles=[SubtotalItem(label=it["label"], count=to_decimal(it["count"]), price=to_decimal(it["price"]), note=it["note"]) for it in dentist_deductibles],
            app_expenses_subtotal=to_decimal(app_summary["subtotal"]),
        )
        expedition_summary = calculate_expedition_expenses([
            ExpeditionItem(label=it["label"], count=to_decimal(it["count"]), price=to_decimal(it["price"]), divisor=to_decimal(it["divisor"]), note=it["note"])
            for it in expedition_items
        ])

        return {
            "house": house_items,
            "house_expenditures": house_summary,
            "application": app_items,
            "application_expenses": app_summary,
            "dentist_billed": dentist_billed,
            "dentist_deductibles": dentist_deductibles,
            "dentist_tracker": {
                "total_billed": str(dentist_summary.total_billed),
                "total_paid": str(dentist_summary.total_paid),
                "pure_dentist_remaining": str(dentist_summary.pure_dentist_remaining),
                "combined_grand_total": str(dentist_summary.combined_grand_total),
                "payments_made_count": dentist_summary.payments_made_count,
                "progress_pct": str(dentist_summary.progress_pct),
                "progress_bar": dentist_summary.progress_bar,
                "billed_items": dentist_summary.billed_items,
                "deductible_items": dentist_summary.deductible_items,
            },
            "snr": snr_items,
            "lorraine": lorraine_items,
            "expedition": expedition_summary,
            "raw_expedition_items": expedition_items,
        }


    def _parse_chores(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Extract chore entries and daily assignee initials from 'Chore Chart'."""
        chores_data = []
        if "Chore Chart" not in wb.sheetnames:
            return {"month": "2026-07", "entries": chores_data}

        ws = wb["Chore Chart"]
        # Rows 5..9 (Kitchen), 11..13 (Living Room), 15..17 (Bedroom), 19..20 (Bathroom), 22..24 (Maintenance)
        zone_ranges = [
            ("Kitchen", 5, 9),
            ("Living Room", 11, 13),
            ("Bedroom", 15, 17),
            ("Bathroom", 19, 20),
            ("Maintenance", 22, 24),
        ]

        for zone_name, r_start, r_end in zone_ranges:
            for r in range(r_start, r_end + 1):
                freq = str(ws.cell(r, 1).value or "").strip()
                name = str(ws.cell(r, 2).value or "").strip()
                if not name:
                    continue

                daily_assign = {}
                # Columns 3..33 for days 1..31
                for d in range(1, 32):
                    col_idx = d + 2
                    val = str(ws.cell(r, col_idx).value or "").strip().upper()
                    if val:
                        daily_assign[str(d)] = val

                chores_data.append({
                    "zone": zone_name,
                    "chore_name": name,
                    "frequency": freq,
                    "daily_assignments": daily_assign,
                })

        entries = [
            ChoreEntry(
                zone=item["zone"],
                chore_name=item["chore_name"],
                frequency=item["frequency"],
                daily_assignments=item["daily_assignments"],
            )
            for item in chores_data
        ]
        return ChoreEngine(entries=entries, month_str="2026-07").get_summary()

    def _parse_pajah(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Extract graduation toga rental tracking from 'Pajah Rent'."""
        if "Pajah Rent" not in wb.sheetnames:
            return calculate_pajah_summary([])

        ws = wb["Pajah Rent"]
        owners_records = []
        for r in range(2, 10):
            owner = str(ws.cell(r, 1).value or "").strip()
            if not owner:
                continue
            owned = int(ws.cell(r, 2).value or 1)
            p_pictorial = to_decimal(ws.cell(r, 3).value or 500)
            p_grad = to_decimal(ws.cell(r, 4).value or 650)
            dan_addon = to_decimal(ws.cell(r, 5).value or 100)
            rent_count = int(to_decimal(ws.cell(r, 9).value or 0))

            owners_records.append(
                PajahOwnerRecord(
                    owner_name=owner,
                    owned=owned,
                    price_pictorial=p_pictorial,
                    price_grad=p_grad,
                    dan_addon=dan_addon,
                    active_rentals=rent_count,
                )
            )

        return calculate_pajah_summary(owners_records)

    def _parse_budget_extras(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Extract Additionals and Payables from 'Current Budget'."""
        additionals = []
        payables = []

        if "Current Budget" not in wb.sheetnames:
            return {"additionals": additionals, "payables": payables}

        ws = wb["Current Budget"]

        # Additionals (B26:B31)
        for r in range(26, 32):
            lbl = str(ws.cell(r, 1).value or "").strip()
            amt = ws.cell(r, 2).value
            if lbl and amt is not None and to_decimal(amt) > ZERO:
                additionals.append({
                    "label": lbl,
                    "amount": str(to_decimal(amt)),
                })

        # Payables (P4:R29)
        for r in range(4, 30):
            item_name = str(ws.cell(r, 16).value or "").strip()
            price_val = ws.cell(r, 17).value
            if item_name and str(item_name) != "0" and price_val is not None and to_decimal(price_val) > ZERO:
                payables.append({
                    "item": item_name,
                    "price": str(to_decimal(price_val)),
                })

        return {"additionals": additionals, "payables": payables}
