"""Workbook Importer Service for Dan Budgeting Excel Sheets.

Extracts budget configuration, monthly utility records, peer expense ledgers,
groceries remittances, and holiday lists from local Excel workbooks (.xlsx)
and seeds the local application storage without exposing private data to Git.
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import openpyxl

from .decimal_utils import to_decimal, round_up_excel, round_currency
from .storage import StorageService

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

        return {
            "version": "1.0.0",
            "imported_at": datetime.now().isoformat(),
            "source_file": self.workbook_path.name,
            "salary": salary,
            "schedule": schedule,
            "bills": bills,
            "settlements": settlements,
            "groceries": groceries,
        }

    def _parse_holidays(self, wb: openpyxl.Workbook) -> List[Dict[str, Any]]:
        """Parse 'Holidays' sheet into holiday records."""
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
            is_regular = "regular" in law_type.lower()

            if date_str and name:
                holidays.append({
                    "date": date_str,
                    "name": name,
                    "type": "regular" if is_regular else "special",
                    "law_type": law_type,
                })
        return holidays

    def _parse_schedule(self, wb: openpyxl.Workbook, holidays: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract daily teaching schedule and allowance rates from 'Current Budget' or '📊 Dashboard'."""
        daily_units = {"Mon": "0", "Tue": "0", "Wed": "0", "Thu": "0", "Fri": "0", "Sat": "0", "Sun": "0"}
        hourly_rate = "198.85"
        daily_food = "200.00"
        daily_transpo = "55.00"

        if "Current Budget" in wb.sheetnames:
            ws = wb["Current Budget"]
            # Row 3 col 5 has salary/hr (e.g. 198.85)
            rate_val = ws.cell(3, 5).value
            if rate_val:
                hourly_rate = str(to_decimal(rate_val))

            # Row 4 col 7..13 has daily units for Mon..Sun
            # Check row 3 headers: MON, TUES, WED...
            day_map = [("Mon", 7), ("Tue", 8), ("Wed", 9), ("Thu", 10), ("Fri", 11), ("Sat", 12), ("Sun", 13)]
            for day_key, col_idx in day_map:
                u_val = ws.cell(4, col_idx).value
                if u_val is not None:
                    daily_units[day_key] = str(to_decimal(u_val))

            # Transpo rate row 9 col 7
            t_val = ws.cell(9, 7).value
            if t_val:
                daily_transpo = str(to_decimal(t_val))

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
        """Parse tenant utility records and monthly historical charges from 'Monthly Bills'."""
        tenants: List[str] = ["Dan", "Jaco", "Troy"]
        my_tenant_name = "Dan"
        items: List[Dict[str, Any]] = []
        history: List[Dict[str, Any]] = []

        if "Monthly Bills" not in wb.sheetnames:
            return {"tenants": tenants, "my_tenant_name": my_tenant_name, "items": items, "history": history}

        ws = wb["Monthly Bills"]
        # Row 2 headers: Month, Rent, Water, Electricity, Internet, Total Utils w/ int, Total, Dan, Jaco, Troy...
        headers = [str(ws.cell(2, c).value or "").strip() for c in range(1, ws.max_column + 1)]

        # Extract tenant names from column 8 onwards
        detected_tenants: List[str] = []
        tenant_col_indices: Dict[str, int] = {}
        for c_idx in range(8, len(headers) + 1):
            name = str(ws.cell(2, c_idx).value or "").strip()
            if name and name not in ["Total", "Month", "Total Utils w/ int"]:
                detected_tenants.append(name)
                tenant_col_indices[name] = c_idx

        if detected_tenants:
            tenants = detected_tenants

        # Iterate data rows (historical months)
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
            total = str(to_decimal(ws.cell(r, 7).value or 0))

            # Active tenants for this month
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
                "total": total,
                "active_tenants": active_for_month,
            })

        # Latest row becomes the active items template
        if history:
            latest = history[-1]
            active_tenants = latest.get("active_tenants", tenants)
            items = [
                {"name": "Rent", "category": "Rent", "total_amount": latest["rent"], "is_active": True, "active_tenants": active_tenants},
                {"name": "Water", "category": "Water", "total_amount": latest["water"], "is_active": True, "active_tenants": active_tenants},
                {"name": "Electricity", "category": "Electricity", "total_amount": latest["electricity"], "is_active": True, "active_tenants": active_tenants},
                {"name": "Internet", "category": "Internet", "total_amount": latest["internet"], "is_active": True, "active_tenants": active_tenants},
            ]

        return {
            "tenants": tenants,
            "my_tenant_name": my_tenant_name,
            "items": items,
            "history": history,
        }

    def _parse_calumpang(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Extract peer expense ledger from 'Calumpang'."""
        peer_name = "Troy"
        dan_ratio = "0.50"
        items: List[Dict[str, Any]] = []

        if "Calumpang" not in wb.sheetnames:
            return {"peer_name": peer_name, "dan_ratio": dan_ratio, "items": items}

        ws = wb["Calumpang"]
        # Row 1 headers: Item, Price, div/2 troy ...
        for r in range(2, ws.max_row + 1):
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

        return {
            "peer_name": peer_name,
            "dan_ratio": dan_ratio,
            "items": items,
        }

    def _parse_mama_groceries(self, wb: openpyxl.Workbook) -> Dict[str, Any]:
        """Extract grocery items and deductions from 'Mama Groceries'."""
        recipient_name = "Mama"
        items: List[Dict[str, Any]] = []
        deductions: List[Dict[str, Any]] = []

        if "Mama Groceries" not in wb.sheetnames:
            return {"recipient_name": recipient_name, "items": items, "deductions": deductions}

        ws = wb["Mama Groceries"]
        # Rows 6+ contain items in Col 2 (Item), Col 3 (Count), Col 4 (Price), Col 5 (Subtotal), Col 6 (Note)
        # Col 9 (Deduction Item), Col 10 (Deduction Price)
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

            # Check deductions in cols 9 & 10
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
