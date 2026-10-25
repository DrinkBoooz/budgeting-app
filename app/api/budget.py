"""Bi-Weekly Schedule and Living Budget API Bridge."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

from app.api.base import BaseAPI
from app.core.calendar_engine import (
    calculate_cutoff_units,
    calculate_unified_budget_pipeline,
    generate_philippine_holidays,
    fetch_external_philippine_holidays,
    Holiday,
)
from app.core.decimal_utils import to_decimal


class BudgetAPI(BaseAPI):
    """API endpoints for teaching schedule, cutoff accumulation, and living budget."""

    def compute_cutoff_schedule(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute bi-weekly cutoff units, workdays, and living expenses."""
        try:
            year = int(payload.get("year", date.today().year))
            month = int(payload.get("month", date.today().month))
            daily_units = payload.get("daily_units", {})
            hourly_rate = to_decimal(payload.get("hourly_rate", "198.85"))
            daily_food = to_decimal(payload.get("daily_food_rate", "200.00"))
            daily_transpo = to_decimal(payload.get("daily_transport_rate", "150.00"))

            holidays_payload = payload.get("holidays", [])
            custom_holidays: List[Holiday] = []
            for h in holidays_payload:
                d_str = h.get("date", "")
                if d_str:
                    try:
                        d_obj = date.fromisoformat(d_str)
                        custom_holidays.append(
                            Holiday(
                                date=d_obj,
                                name=h.get("name", "Holiday"),
                                law_type=h.get("law_type", "Regular Holiday"),
                                scope=h.get("scope", "Nationwide"),
                                is_active=bool(h.get("is_active", True)),
                            )
                        )
                    except ValueError:
                        pass

            if not custom_holidays:
                custom_holidays = generate_philippine_holidays(year)

            breakdown = calculate_cutoff_units(
                year=year,
                month=month,
                daily_units=daily_units,
                hourly_rate=hourly_rate,
                daily_food_rate=daily_food,
                daily_transport_rate=daily_transpo,
                holidays=custom_holidays,
            )

            res = {
                "year": breakdown.year,
                "month": breakdown.month,
                "cutoff1": {
                    "working_days": breakdown.cutoff1_working_days,
                    "total_units": str(breakdown.cutoff1_total_units),
                    "gross_pay": str(breakdown.cutoff1_gross_pay),
                    "living_budget": str(breakdown.cutoff1_living_budget),
                },
                "cutoff2": {
                    "working_days": breakdown.cutoff2_working_days,
                    "total_units": str(breakdown.cutoff2_total_units),
                    "gross_pay": str(breakdown.cutoff2_gross_pay),
                    "living_budget": str(breakdown.cutoff2_living_budget),
                },
                "monthly_totals": {
                    "working_days": breakdown.monthly_working_days,
                    "total_units": str(breakdown.monthly_total_units),
                    "gross_pay": str(breakdown.monthly_gross_pay),
                    "living_budget": str(breakdown.monthly_living_budget),
                },
                "lost_units_due_to_holidays": str(breakdown.lost_units_due_to_holidays),
                "lost_cash_due_to_holidays": str(breakdown.lost_cash_due_to_holidays),
                "one_week_base_allowance": str(breakdown.one_week_base_allowance),
                "full_month_allowance": str(breakdown.full_month_allowance),
                "day_breakdowns": [
                    {
                        "day_name": d["day_name"],
                        "units_per_day": str(d["units_per_day"]),
                        "c1_workdays": d["c1_workdays"],
                        "c2_workdays": d["c2_workdays"],
                        "c1_units": str(d["c1_units"]),
                        "c2_units": str(d["c2_units"]),
                        "total_month_units": str(d["total_month_units"]),
                    }
                    for d in breakdown.raw_payload.get("day_breakdowns", [])
                ],
            }
            return self.success(res)
        except Exception as e:
            return self.error(f"Failed to calculate cutoff schedule: {str(e)}")

    def compute_additionals_and_payables(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Current Budget Money After Additionals and Payables.

        Money after Utility = Net Salary - Living Expenses - Monthly Bills
        Money after Additionals = Money after Utility + SUM(Additionals)
        Money after Payables = Money after Additionals - SUM(Payables)
        """
        try:
            money_after_utility = to_decimal(payload.get("money_after_utility", 0))
            additionals_list = payload.get("additionals", [])
            payables_list = payload.get("payables", [])

            total_additionals = sum(
                (to_decimal(a.get("amount", 0)) for a in additionals_list),
                Decimal("0")
            )
            total_payables = sum(
                (to_decimal(p.get("amount", 0)) for p in payables_list),
                Decimal("0")
            )

            money_after_additionals = money_after_utility + total_additionals
            money_after_payables = money_after_additionals - total_payables

            return self.success({
                "money_after_utility": str(money_after_utility),
                "total_additionals": str(total_additionals),
                "money_after_additionals": str(money_after_additionals),
                "total_payables": str(total_payables),
                "money_after_payables": str(money_after_payables),
                "additionals": additionals_list,
                "payables": payables_list,
            })
        except Exception as e:
            return self.error(f"Failed to calculate additionals and payables: {str(e)}")


    def get_default_holidays(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch statutory holidays for a given year."""
        year = int(payload.get("year", date.today().year))
        holidays = generate_philippine_holidays(year)
        return self.success([
            {
                "date": h.date.isoformat(),
                "name": h.name,
                "law_type": h.law_type,
                "scope": h.scope,
                "is_active": h.is_active,
            }
            for h in holidays
        ])

    def sync_external_holidays(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch holidays from external public calendar API (Nager.Date / PH Gov) with fallback."""
        try:
            year = int(payload.get("year", date.today().year))
            holidays, source = fetch_external_philippine_holidays(year)
            return self.success({
                "year": year,
                "source": source,
                "count": len(holidays),
                "holidays": [
                    {
                        "date": h.date.isoformat(),
                        "name": h.name,
                        "law_type": h.law_type,
                        "scope": h.scope,
                        "is_active": getattr(h, "is_active", True),
                    }
                    for h in holidays
                ],
            })
        except Exception as e:
            return self.error(f"Failed to sync external holidays: {str(e)}")


    def compute_unified_budget(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute the unified Schedule -> Pinasweldo -> Current Budget pipeline."""
        try:
            year = int(payload.get("year", date.today().year))
            month = int(payload.get("month", date.today().month))
            daily_units = payload.get("daily_units", {})
            hourly_rate = to_decimal(payload.get("hourly_rate", "198.85"))
            daily_food = to_decimal(payload.get("daily_food_rate", "300.00"))
            daily_transpo = to_decimal(payload.get("daily_transport_rate", "165.00"))

            holidays_payload = payload.get("holidays", [])
            custom_holidays: List[Holiday] = []
            for h in holidays_payload:
                d_str = h.get("date", "")
                if d_str:
                    try:
                        d_obj = date.fromisoformat(d_str)
                        custom_holidays.append(
                            Holiday(
                                date=d_obj,
                                name=h.get("name", "Holiday"),
                                law_type=h.get("law_type", "Regular Holiday"),
                                scope=h.get("scope", "Nationwide"),
                                is_active=bool(h.get("is_active", True)),
                            )
                        )
                    except ValueError:
                        pass

            if not custom_holidays:
                custom_holidays = generate_philippine_holidays(year)

            breakdown = calculate_cutoff_units(
                year=year,
                month=month,
                daily_units=daily_units,
                hourly_rate=hourly_rate,
                daily_food_rate=daily_food,
                daily_transport_rate=daily_transpo,
                holidays=custom_holidays,
            )

            tax_mode = str(payload.get("tax_mode", "pinasweldo_private"))
            tax_split_method = str(payload.get("tax_split_method", "equal_split"))
            living_expense_option = str(payload.get("living_expense_option", "one_week"))
            rent_perceived = to_decimal(payload.get("rent_perceived", "2500.00"))
            utilities_perceived = to_decimal(payload.get("utilities_perceived", "3175.00"))
            additionals = payload.get("additionals", [
                {"label": "September", "amount": "4000.00"},
                {"label": "additional transfer", "amount": "4700.00"},
            ])
            payables = payload.get("payables", [])
            include_13th_month = bool(payload.get("include_13th_month", False))
            months_worked_13th = to_decimal(payload.get("months_worked_13th", 12))
            custom_tax_rate = to_decimal(payload.get("custom_tax_rate", 0))

            unified_res = calculate_unified_budget_pipeline(
                cutoff_breakdown=breakdown,
                tax_mode=tax_mode,
                tax_split_method=tax_split_method,
                living_expense_option=living_expense_option,
                rent_perceived=rent_perceived,
                utilities_perceived=utilities_perceived,
                additionals=additionals,
                payables=payables,
                include_13th_month=include_13th_month,
                months_worked_13th=months_worked_13th,
                custom_tax_rate=custom_tax_rate,
            )

            return self.success(unified_res)
        except Exception as e:
            return self.error(f"Failed to compute unified budget: {str(e)}")
