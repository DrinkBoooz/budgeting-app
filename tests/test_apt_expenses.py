"""Unit tests for Apartment Expenditures, Dentist Tracker, and Expedition Splits."""

from decimal import Decimal
import pytest

from app.core.apt_expenses_engine import (
    ExpenditureItem,
    SubtotalItem,
    ExpeditionItem,
    calculate_house_expenditures,
    calculate_application_expenses,
    calculate_dentist_tracker,
    calculate_expedition_expenses,
)


def test_house_expenditures_formula():
    """House / IKEA Expenditures (=(Count*Price)-Discount), Grand Total ₱4,675."""
    items = [
        ExpenditureItem(item="BDO 50% promo item", count=Decimal("1"), price=Decimal("1000.00"), discount=Decimal("500.00")),
        ExpenditureItem(item="IKEA Storage Box", count=Decimal("3"), price=Decimal("500.00"), discount=Decimal("0")),
        ExpenditureItem(item="Desk Lamp", count=Decimal("1"), price=Decimal("2675.00"), discount=Decimal("0")),
    ]
    # (1*1000 - 500 = 500) + (3*500 = 1500) + 2675 = 4675.00
    res = calculate_house_expenditures(items)
    assert res["grand_total"] == "4675.00"
    assert len(res["items"]) == 3
    assert res["items"][0]["total_price"] == "500.00"


def test_application_expenses_exact():
    """Application Expenses: Drug Test, Neuro Psych, NBI, TOR, Medical = ₱2,420."""
    items = [
        SubtotalItem(label="Drug Test", count=Decimal("1"), price=Decimal("300.00")),
        SubtotalItem(label="Neuro Psych", count=Decimal("1"), price=Decimal("1000.00")),
        SubtotalItem(label="NBI Clearance", count=Decimal("1"), price=Decimal("160.00")),
        SubtotalItem(label="TOR Transcript", count=Decimal("1"), price=Decimal("460.00")),
        SubtotalItem(label="Medical Exam", count=Decimal("1"), price=Decimal("500.00")),
    ]
    res = calculate_application_expenses(items)
    assert res["subtotal"] == "2420.00"
    assert len(res["items"]) == 5


def test_dentist_tracker_pure_and_combined_and_progress():
    """Dentist Billed ₱37,500, Deductibles -₱8,000, Pure Remaining ₱29,500, Combined ₱31,920."""
    billed = [
        SubtotalItem(label="Initial Downpayment", count=Decimal("1"), price=Decimal("10000.00")),
        SubtotalItem(label="Adjustments (Batch 1)", count=Decimal("1"), price=Decimal("4500.00")),
        SubtotalItem(label="Adjustments (Batch 2)", count=Decimal("1"), price=Decimal("20000.00")),
        SubtotalItem(label="Dental Cleaning", count=Decimal("1"), price=Decimal("3000.00")),
    ]
    deductibles = [
        SubtotalItem(label="Nov 11 Payment", count=Decimal("1"), price=Decimal("2000.00")),
        SubtotalItem(label="Dec 5 Payment", count=Decimal("1"), price=Decimal("4000.00")),
        SubtotalItem(label="Jan 29 Payment", count=Decimal("1"), price=Decimal("2000.00")),
    ]
    summary = calculate_dentist_tracker(
        billed=billed,
        deductibles=deductibles,
        app_expenses_subtotal=Decimal("2420.00"),
    )
    assert summary.total_billed == Decimal("37500.00")
    assert summary.total_paid == Decimal("8000.00")
    assert summary.pure_dentist_remaining == Decimal("29500.00")
    # Combined balance = App (2,420) + Pure Remaining (29,500) = 31,920.00
    assert summary.combined_grand_total == Decimal("31920.00")
    assert summary.payments_made_count == 3
    # 8,000 / 37,500 = 21.33% -> 2 blocks out of 10
    assert summary.progress_pct == Decimal("21.33")
    assert summary.progress_bar == "██░░░░░░░░"


def test_expedition_dynamic_divisor():
    """Noella & James Expedition (=ROUNDUP(Price*Count/Divisor, 0))."""
    items = [
        ExpeditionItem(label="Gas Split (5 people)", count=Decimal("1"), price=Decimal("1500.00"), divisor=Decimal("5")),  # 300
        ExpeditionItem(label="Toll Fee (3 people)", count=Decimal("1"), price=Decimal("455.00"), divisor=Decimal("3")),   # 455/3 = 151.66 -> 152
        ExpeditionItem(label="Solo Snack (1 person)", count=Decimal("1"), price=Decimal("516.00"), divisor=Decimal("1")), # 516
    ]
    # 300 + 152 + 516 = 968.00
    res = calculate_expedition_expenses(items)
    assert res["subtotal"] == "968.00"
    assert res["items"][1]["subtotal"] == "152.00"
