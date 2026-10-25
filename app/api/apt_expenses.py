"""Apartment Expenses & Dentist Tracker API Bridge."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.api.base import BaseAPI
from app.core.apt_expenses_engine import (
    ExpenditureItem,
    SubtotalItem,
    ExpeditionItem,
    calculate_house_expenditures,
    calculate_application_expenses,
    calculate_dentist_tracker,
    calculate_expedition_expenses,
)
from app.core.decimal_utils import to_decimal


class AptExpensesAPI(BaseAPI):
    """API endpoints for Apt Expenses, Dentist & Braces Tracker, and Expedition splits."""

    def compute_house_expenditures(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute house / IKEA expenditures matching Apt Expenses A1:G22."""
        try:
            items_raw = payload.get("items", [])
            items = [
                ExpenditureItem(
                    item=it.get("item", "Item"),
                    count=to_decimal(it.get("count", 1)),
                    price=to_decimal(it.get("price", 0)),
                    discount=to_decimal(it.get("discount", 0)),
                    note=str(it.get("note", "")),
                )
                for it in items_raw
            ]
            res = calculate_house_expenditures(items)
            return self.success(res)
        except Exception as e:
            return self.error(f"Failed to calculate house expenditures: {str(e)}")

    def compute_application_expenses(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute application expenses matching Apt Expenses A33:E42."""
        try:
            items_raw = payload.get("items", [])
            items = [
                SubtotalItem(
                    label=it.get("label", "Application Item"),
                    count=to_decimal(it.get("count", 1)),
                    price=to_decimal(it.get("price", 0)),
                    note=str(it.get("note", "")),
                )
                for it in items_raw
            ]
            res = calculate_application_expenses(items)
            return self.success(res)
        except Exception as e:
            return self.error(f"Failed to calculate application expenses: {str(e)}")

    def compute_dentist_tracker(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute dentist & braces tracker, deductibles, combined D67 balance, and progress bar."""
        try:
            billed_raw = payload.get("billed_items", [])
            deductibles_raw = payload.get("deductibles", [])
            app_subtotal = to_decimal(payload.get("app_expenses_subtotal", "2420.00"))

            billed = [
                SubtotalItem(
                    label=b.get("label", "Procedure"),
                    count=to_decimal(b.get("count", 1)),
                    price=to_decimal(b.get("price", 0)),
                    note=str(b.get("note", "")),
                )
                for b in billed_raw
            ]

            deductibles = [
                SubtotalItem(
                    label=d.get("label", "Payment"),
                    count=to_decimal(d.get("count", 1)),
                    price=to_decimal(d.get("price", 0)),
                    note=str(d.get("note", "")),
                )
                for d in deductibles_raw
            ]

            summary = calculate_dentist_tracker(
                billed=billed,
                deductibles=deductibles,
                app_expenses_subtotal=app_subtotal,
            )

            return self.success({
                "total_billed": str(summary.total_billed),
                "total_paid": str(summary.total_paid),
                "pure_dentist_remaining": str(summary.pure_dentist_remaining),
                "combined_grand_total": str(summary.combined_grand_total),
                "payments_made_count": summary.payments_made_count,
                "progress_pct": str(summary.progress_pct),
                "progress_bar": summary.progress_bar,
                "billed_items": summary.billed_items,
                "deductible_items": summary.deductible_items,
            })
        except Exception as e:
            return self.error(f"Failed to calculate dentist tracker: {str(e)}")

    def compute_expedition_expenses(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Noella & James Expedition split with N-person divisor."""
        try:
            items_raw = payload.get("items", [])
            items = [
                ExpeditionItem(
                    label=it.get("label", "Item"),
                    count=to_decimal(it.get("count", 1)),
                    price=to_decimal(it.get("price", 0)),
                    divisor=to_decimal(it.get("divisor", 1)),
                    note=str(it.get("note", "")),
                )
                for it in items_raw
            ]
            res = calculate_expedition_expenses(items)
            return self.success(res)
        except Exception as e:
            return self.error(f"Failed to calculate expedition expenses: {str(e)}")
