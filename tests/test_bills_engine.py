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


def test_recipient_breakdown_and_color_tokens():
    """Verify Latest Month Breakdown separating Rent (Tita Beth) from Utilities (Dan) and hex colors."""
    from app.core.bills_engine import calculate_recipient_breakdown, COLOR_TOKENS

    assert COLOR_TOKENS["Paid"] == "#1A7A4A"
    assert COLOR_TOKENS["Dan"] == "#D6EAF8"
    assert COLOR_TOKENS["Troy"] == "#FDEBD0"

    rows = calculate_recipient_breakdown(
        rent_amount=Decimal("7000.00"),
        utilities_amount=Decimal("3175.00"),
        tenants=["Dan", "Jaco", "Troy"],
        rent_payers=["Dan", "Troy"],
        utils_payers=["Troy"],
    )
    assert len(rows) == 3
    dan = next(r for r in rows if r.name == "Dan")
    troy = next(r for r in rows if r.name == "Troy")
    jaco = next(r for r in rows if r.name == "Jaco")

    # Rent is 7000 / 2 = 3500 each for Dan and Troy. Jaco is 0.
    assert dan.rent_to_tita_beth == Decimal("3500.00")
    assert troy.rent_to_tita_beth == Decimal("3500.00")
    assert jaco.rent_to_tita_beth == Decimal("0.00")

    # Utilities: Troy pays 3175.00 to Dan. Dan pays 0 to Dan.
    assert troy.utilities_to_dan == Decimal("3175.00")
    assert dan.utilities_to_dan == Decimal("0.00")
    assert troy.total_bills == Decimal("6675.00")


def test_bills_ytd_summary():
    """Verify YTD summary calculation matching Monthly Bills A408:B413."""
    from app.core.bills_engine import calculate_ytd_summary

    records = [
        {"billing_month": "2025-08-28", "total": "6625.00", "per_person": "2208.33", "status": "Paid", "occupants": ["Dan", "Jaco", "Troy"]},
        {"billing_month": "2025-09-20", "total": "7688.00", "per_person": "2562.67", "status": "Paid", "occupants": ["Dan", "Jaco", "Troy"]},
        {"billing_month": "2026-10-20", "total": "11231.31", "per_person": "5615.66", "status": "Pending", "occupants": ["Dan", "Troy"]},
    ]
    summary = calculate_ytd_summary(records)
    assert summary["months_paid"] == 2
    assert summary["ytd_total_bills"] == "14313.00"
    assert summary["highest_month_total"] == "7688.00"
    assert summary["lowest_month_paid"] == "6625.00"

