"""Bi-Weekly Schedule and Living Budget API Bridge."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

from app.api.base import BaseAPI
from app.core.calendar_engine import (
    calculate_cutoff_units,
    generate_philippine_holidays,
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
            }
            for h in holidays
        ])
