"""Tests for Calumpang peer settlements, Mama Groceries remittances, and Executive Cash Flow."""

from decimal import Decimal
import pytest
from app.core.settlement_engine import (
    calculate_calumpang_settlement,
    calculate_mama_groceries_remittance,
    generate_executive_cash_flow,
    CalumpangExpense,
    RemittanceLineItem,
)


def test_calumpang_roundup_settlement():
    """Verify `=ROUNDUP(Price/2, 0)` matching exact workbook examples:

    - water aug: 90 -> 45
    - sinigang: 222 -> 111
    - onion 20/09: 227 -> 114
    - angels pizza: 1034 -> 517
    - gas noella car: 500 -> 250
    """
    expenses = [
        CalumpangExpense("water aug", Decimal("90.00"), paid_by="Dan"),
        CalumpangExpense("vegetables sinigang", Decimal("222.00"), paid_by="Dan"),
        CalumpangExpense("onion et al 20/09", Decimal("227.00"), paid_by="Dan"),
        CalumpangExpense("angels pizza", Decimal("1034.00"), paid_by="Dan"),
        CalumpangExpense("gas noella car", Decimal("500.00"), paid_by="Dan"),
    ]
    summary = calculate_calumpang_settlement(expenses, peer_name="Troy")

    assert summary.total_expenses == Decimal("2073.00")
    # Dan shares: 45 + 111 + 114 + 517 + 250 = 1037
    assert summary.dan_total_share == Decimal("1037.00")
    # Peer shares: 45 + 111 + 113 + 517 + 250 = 1036
    assert summary.peer_total_share == Decimal("1036.00")
    assert summary.net_peer_owes_dan == Decimal("1036.00")


def test_mama_groceries_remittance():
    """Verify Mama Groceries net transfer: `=SUM(Items) - SUM(Deductions)`."""
    items = [
        RemittanceLineItem("Dada allowance", Decimal("4000.00")),
        RemittanceLineItem("LG Utang", Decimal("1380.00")),
        RemittanceLineItem("Gas Oct 18", Decimal("946.00")),
    ]
    deductions = [
        RemittanceLineItem("Advance payment", Decimal("1000.00")),
    ]
    summary = calculate_mama_groceries_remittance(items, deductions, recipient_name="Mama")
    assert summary.gross_amount == Decimal("6326.00")
    assert summary.total_deductions == Decimal("1000.00")
    assert summary.net_transfer_amount == Decimal("5326.00")


def test_executive_cash_flow_waterfall():
    """Verify Executive Dashboard cash flow reconciliation."""
    cash_flow = generate_executive_cash_flow(
        net_salary=Decimal("30000.00"),
        other_income=Decimal("5000.00"),
        monthly_bills_share=Decimal("3900.00"),
        living_budget=Decimal("7000.00"),
        peer_settlement_payable=Decimal("1000.00"),
        groceries_remittance=Decimal("5000.00"),
    )
    assert cash_flow.total_inflow == Decimal("35000.00")
    # Total outflow: 3900 + 7000 + 1000 + 5000 = 16900.00
    assert cash_flow.total_outflow == Decimal("16900.00")
    # Net savings: 35000 - 16900 = 18100.00
    assert cash_flow.net_surplus == Decimal("18100.00")
    # Savings rate: 18100 / 35000 = 51.71%
    assert cash_flow.savings_rate_pct == Decimal("51.71")


def test_master_settlement_matrix():
    """Verify Calumpang M1:U39 Master Settlement Matrix with Spotify, Utilities, and ROUNDUP."""
    from app.core.settlement_engine import calculate_master_settlement_matrix

    troy_entries = [
        {"amount": "500.00", "is_paid": True, "note": "Gas"},
        {"amount": "1139.00", "is_paid": True, "note": "SnR Food"},
        {"amount": "300.00", "is_paid": False, "note": "Pending laundry"},
    ]
    # Paid items: 500 + 1139 = 1639.
    # Add-ons: Spotify 57.40 + Utilities 3175 = 3232.40.
    # Subtotal selected: 1639 + 3232.40 = 4871.40.
    # Bank transfer = ROUNDUP(4871.40, 0) = 4872.00.
    res = calculate_master_settlement_matrix(
        troy_entries=troy_entries,
        spotify_amount=Decimal("57.40"),
        troy_utilities=Decimal("3175.00"),
    )
    assert res["troy"]["subtotal"] == "4871.40"
    assert res["troy"]["bank_transfer"] == "4872.00"
    assert res["troy"]["spotify"] == "57.40"
    assert res["troy"]["utilities"] == "3175.00"

