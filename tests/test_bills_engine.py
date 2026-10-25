"""Tests for multi-tenant dynamic cost splitting and rolling utility averages."""

from decimal import Decimal
import pytest
from app.core.bills_engine import (
    calculate_bill_split,
    calculate_rolling_utility_average,
    calculate_total_bills_summary,
    UtilityBill,
)


def test_bill_split_equal_division():
    """Verify `=IF(Total="", "", IFERROR(Total / COUNTIF(tenants, TRUE), 0))`."""
    bill = UtilityBill(
        name="Internet",
        category="Internet",
        total_amount=Decimal("1600.00"),
        is_active=True,
        active_tenants=["Dan", "Jaco"],
    )
    splits = calculate_bill_split(bill)
    assert splits["Dan"] == Decimal("800.00")
    assert splits["Jaco"] == Decimal("800.00")


def test_bill_split_with_three_tenants():
    """Verify 3-tenant division with rounding."""
    bill = UtilityBill(
        name="Electricity",
        category="Electricity",
        total_amount=Decimal("1000.00"),
        is_active=True,
        active_tenants=["Dan", "Jaco", "Troy"],
    )
    splits = calculate_bill_split(bill, round_up=False)
    # 1000 / 3 = 333.33 each
    assert splits["Dan"] == Decimal("333.33")
    assert splits["Jaco"] == Decimal("333.33")
    assert splits["Troy"] == Decimal("333.33")


def test_bill_split_no_active_tenants():
    """Division with 0 active tenants should return empty dict without divide-by-zero error."""
    bill = UtilityBill(
        name="Empty Bill",
        category="Other",
        total_amount=Decimal("500.00"),
        is_active=True,
        active_tenants=[],
    )
    splits = calculate_bill_split(bill)
    assert splits == {}


def test_rolling_utility_average():
    """Verify 3-month rolling utility average."""
    history = [
        {"name": "Electricity", "amount": Decimal("1500.00")},
        {"name": "Electricity", "amount": Decimal("1800.00")},
        {"name": "Electricity", "amount": Decimal("2100.00")},
    ]
    avg = calculate_rolling_utility_average("Electricity", history, window_months=3)
    # (1500 + 1800 + 2100) / 3 = 1800.00
    assert avg == Decimal("1800.00")


def test_total_bills_summary():
    """Verify multi-bill aggregation and Dan's individual share."""
    bills = [
        UtilityBill(name="Rent", category="Rent", total_amount=Decimal("6000.00"), is_active=True, active_tenants=["Dan", "Jaco"]),
        UtilityBill(name="Water", category="Water", total_amount=Decimal("300.00"), is_active=True, active_tenants=["Dan", "Jaco", "Troy"]),
        UtilityBill(name="Internet", category="Internet", total_amount=Decimal("1600.00"), is_active=True, active_tenants=["Dan", "Jaco"]),
    ]
    summary = calculate_total_bills_summary(bills, my_tenant_name="Dan")
    assert summary.grand_total == Decimal("7900.00")
    # Dan share: Rent 3000 + Water 100 + Internet 800 = 3900.00
    assert summary.my_total_share == Decimal("3900.00")
    assert summary.active_bills_count == 3
