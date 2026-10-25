"""Peer Settlements, Family Remittances, and Executive Dashboard API Bridge."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List

from app.api.base import BaseAPI
from app.core.decimal_utils import to_decimal
from app.core.settlement_engine import (
    calculate_calumpang_settlement,
    calculate_mama_groceries_remittance,
    generate_executive_cash_flow,
    calculate_master_settlement_matrix,
    CalumpangExpense,
    RemittanceLineItem,
)


class SettlementsAPI(BaseAPI):
    """API endpoints for Calumpang peer expenses, Mama Groceries, and Executive Dashboard."""

    def compute_peer_settlement(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Calumpang 50/50 roundup settlement."""
        try:
            items_data = payload.get("items", [])
            peer_name = payload.get("peer_name", "Troy")

            expenses = [
                CalumpangExpense(
                    description=it.get("description", "Item"),
                    total_amount=to_decimal(it.get("total_amount", 0)),
                    paid_by=it.get("paid_by", "Dan"),
                    status=it.get("status", "pending"),
                )
                for it in items_data
            ]

            summary = calculate_calumpang_settlement(expenses, peer_name=peer_name)

            return self.success({
                "total_expenses": str(summary.total_expenses),
                "dan_total_share": str(summary.dan_total_share),
                "peer_total_share": str(summary.peer_total_share),
                "net_peer_owes_dan": str(summary.net_peer_owes_dan),
                "peer_name": peer_name,
                "expenses_count": summary.expenses_count,
                "items": [
                    {
                        "description": it["description"],
                        "total_amount": str(it["total_amount"]),
                        "dan_share": str(it["dan_share"]),
                        "peer_share": str(it["peer_share"]),
                        "paid_by": it["paid_by"],
                        "status": it["status"],
                    }
                    for it in summary.items_breakdown
                ],
            })
        except Exception as e:
            return self.error(f"Failed to calculate peer settlement: {str(e)}")

    def compute_master_matrix(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Master Settlement Matrix matching Calumpang M1:U39."""
        try:
            troy_entries = payload.get("troy_entries", [])
            jaco_entries = payload.get("jaco_entries", [])
            dan_entries = payload.get("dan_entries", [])
            spotify = to_decimal(payload.get("spotify_amount", "57.40"))
            troy_utils = to_decimal(payload.get("troy_utilities", "3175.00"))

            res = calculate_master_settlement_matrix(
                troy_entries=troy_entries,
                jaco_entries=jaco_entries,
                dan_entries=dan_entries,
                spotify_amount=spotify,
                troy_utilities=troy_utils,
            )
            return self.success(res)
        except Exception as e:
            return self.error(f"Failed to calculate master settlement matrix: {str(e)}")

    def compute_groceries_remittance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute net grocery remittance: SUM(items) - SUM(deductions)."""
        try:
            items_raw = payload.get("items", [])
            deductions_raw = payload.get("deductions", [])
            recipient_name = payload.get("recipient_name", "Mama")

            items = [
                RemittanceLineItem(
                    description=it.get("description", "Item"),
                    amount=to_decimal(it.get("amount", 0)),
                    note=it.get("note", ""),
                )
                for it in items_raw
            ]

            deductions = [
                RemittanceLineItem(
                    description=d.get("description", "Deduction"),
                    amount=to_decimal(d.get("amount", 0)),
                    note=d.get("note", ""),
                )
                for d in deductions_raw
            ]

            summary = calculate_mama_groceries_remittance(
                items=items,
                deductions=deductions,
                recipient_name=recipient_name,
            )

            return self.success({
                "gross_amount": str(summary.gross_amount),
                "total_deductions": str(summary.total_deductions),
                "net_transfer_amount": str(summary.net_transfer_amount),
                "recipient_name": summary.recipient_name,
                "items_count": summary.items_count,
                "deductions_count": summary.deductions_count,
            })
        except Exception as e:
            return self.error(f"Failed to calculate remittance: {str(e)}")

    def compute_cash_flow_waterfall(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute Executive Dashboard cash flow waterfall and savings rate."""
        try:
            net_salary = to_decimal(payload.get("net_salary", 0))
            other_income = to_decimal(payload.get("other_income", 0))
            monthly_bills = to_decimal(payload.get("monthly_bills_share", 0))
            living_budget = to_decimal(payload.get("living_budget", 0))
            peer_settlement = to_decimal(payload.get("peer_settlement_payable", 0))
            groceries_remittance = to_decimal(payload.get("groceries_remittance", 0))

            cf = generate_executive_cash_flow(
                net_salary=net_salary,
                other_income=other_income,
                monthly_bills_share=monthly_bills,
                living_budget=living_budget,
                peer_settlement_payable=peer_settlement,
                groceries_remittance=groceries_remittance,
            )

            return self.success({
                "total_inflow": str(cf.total_inflow),
                "total_outflow": str(cf.total_outflow),
                "net_surplus": str(cf.net_surplus),
                "savings_rate_pct": str(cf.savings_rate_pct),
                "net_salary": str(cf.net_salary),
                "living_budget": str(cf.living_budget),
                "monthly_bills_share": str(cf.monthly_bills_share),
                "peer_settlement_payable": str(cf.peer_settlement_payable),
                "groceries_remittance": str(cf.groceries_remittance),
            })
        except Exception as e:
            return self.error(f"Failed to calculate cash flow waterfall: {str(e)}")

