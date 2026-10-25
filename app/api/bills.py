"""Monthly Bills and Roommate Utility Cost Splitting API Bridge."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List

from app.api.base import BaseAPI
from app.core.bills_engine import (
    calculate_bill_split,
    calculate_rolling_utility_average,
    calculate_total_bills_summary,
    calculate_recipient_breakdown,
    COLOR_TOKENS,
    UtilityBill,
)
from app.core.decimal_utils import to_decimal


class BillsAPI(BaseAPI):
    """API endpoints for monthly bills, multi-occupant splitting, and rolling averages."""

    def compute_bills_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute multi-tenant bill splitting and totals."""
        try:
            bills_data = payload.get("bills", [])
            my_tenant_name = payload.get("my_tenant_name", "Dan")
            round_up = bool(payload.get("round_up", False))

            bills: List[UtilityBill] = []
            for b in bills_data:
                bills.append(
                    UtilityBill(
                        name=b.get("name", "Utility"),
                        category=b.get("category", "General"),
                        total_amount=to_decimal(b.get("total_amount", 0)),
                        is_active=bool(b.get("is_active", True)),
                        active_tenants=b.get("active_tenants", []),
                    )
                )

            summary = calculate_total_bills_summary(
                bills=bills,
                my_tenant_name=my_tenant_name,
                round_up=round_up,
            )

            # Format response
            res = {
                "grand_total": str(summary.grand_total),
                "my_total_share": str(summary.my_total_share),
                "active_bills_count": summary.active_bills_count,
                "bills": [
                    {
                        "name": b["name"],
                        "category": b["category"],
                        "total_amount": str(b["total_amount"]),
                        "active_tenants": b["active_tenants"],
                        "my_share": str(b["my_share"]),
                        "splits": {k: str(v) for k, v in b["splits"].items()},
                    }
                    for b in summary.raw_payload.get("bills", [])
                ],
            }
            return self.success(res)
        except Exception as e:
            return self.error(f"Failed to calculate bills summary: {str(e)}")

    def compute_recipient_breakdown(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Latest Month Breakdown: Rent (Tita Beth) vs Utilities (Dan) with color tokens."""
        try:
            rent_amount = to_decimal(payload.get("rent_amount", "7000.00"))
            utilities_amount = to_decimal(payload.get("utilities_amount", "3175.00"))
            tenants = payload.get("tenants", ["Dan", "Jaco", "Troy"])
            rent_payers = payload.get("rent_payers", ["Dan", "Troy"])
            utils_payers = payload.get("utils_payers", ["Troy"])
            custom_overrides = payload.get("custom_overrides")

            rows = calculate_recipient_breakdown(
                rent_amount=rent_amount,
                utilities_amount=utilities_amount,
                tenants=tenants,
                rent_payers=rent_payers,
                utils_payers=utils_payers,
                custom_overrides=custom_overrides,
            )

            return self.success({
                "rows": [
                    {
                        "name": r.name,
                        "rent_to_tita_beth": str(r.rent_to_tita_beth),
                        "utilities_to_dan": str(r.utilities_to_dan),
                        "total_bills": str(r.total_bills),
                        "color_hex": r.color_hex,
                    }
                    for r in rows
                ],
                "color_tokens": COLOR_TOKENS,
            })
        except Exception as e:
            return self.error(f"Failed to calculate recipient breakdown: {str(e)}")

    def compute_rolling_averages(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate 3-month rolling averages for bills."""
        try:
            history = payload.get("history", [])
            categories = payload.get("categories", ["Rent", "Water", "Electricity", "Internet"])
            window_months = int(payload.get("window_months", 3))

            averages = {}
            for cat in categories:
                avg = calculate_rolling_utility_average(
                    utility_name=cat,
                    history=history,
                    window_months=window_months,
                )
                averages[cat] = str(avg)

            return self.success(averages)
        except Exception as e:
            return self.error(f"Failed to calculate rolling averages: {str(e)}")

