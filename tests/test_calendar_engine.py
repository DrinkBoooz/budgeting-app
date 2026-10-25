"""Tests for Excel NETWORKDAYS.INTL parity, teaching schedules, and cutoff units."""

from datetime import date
from decimal import Decimal
import pytest
from app.core.calendar_engine import (
    networkdays_intl,
    calculate_cutoff_units,
    generate_philippine_holidays,
    Holiday,
)


def test_networkdays_standard_weekend():
    """Verify standard Sat/Sun weekend mask '0000011'."""
    # October 2026: Oct 1 is Thursday, Oct 31 is Saturday.
    # Total days = 31. Saturdays = 5, Sundays = 4. Workdays = 22.
    workdays = networkdays_intl(date(2026, 10, 1), date(2026, 10, 31), weekend_mask="0000011")
    assert workdays == 22


def test_networkdays_teaching_mask_monday_only():
    """Verify mask '0111111' where only Monday is a working day."""
    # October 2026 Mondays: Oct 5, 12, 19, 26 -> 4 Mondays
    mondays = networkdays_intl(date(2026, 10, 1), date(2026, 10, 31), weekend_mask="0111111")
    assert mondays == 4


def test_networkdays_with_holiday_exclusion():
    """Verify that statutory holidays fall on a workday and are excluded."""
    # National Heroes Day is Monday, Aug 31, 2026
    # August 2026 Mondays: Aug 3, 10, 17, 24, 31 -> 5 Mondays
    # With Aug 31 as holiday -> 4 working Mondays
    holidays = [Holiday(date(2026, 8, 31), "National Heroes Day")]
    mondays = networkdays_intl(
        date(2026, 8, 1),
        date(2026, 8, 31),
        weekend_mask="0111111",
        holidays=holidays,
    )
    assert mondays == 4


def test_cutoff_units_breakdown():
    """Verify teaching unit accumulation for Cutoff 1 (1-15) and Cutoff 2 (16-EOM)."""
    # Daily units: Mon = 9, Wed = 10, others = 0
    daily_units = {"Mon": Decimal("9"), "Wed": Decimal("10")}
    # September 2026
    breakdown = calculate_cutoff_units(
        year=2026,
        month=9,
        daily_units=daily_units,
        hourly_rate=Decimal("198.85"),
        daily_food_rate=Decimal("200.00"),
        daily_transport_rate=Decimal("55.00"),
    )

    # Cutoff 1: Sept 1 to 15.
    # Mondays: Sept 7, 14 (2 * 9 = 18 units)
    # Wednesdays: Sept 2, 9 (2 * 10 = 20 units)
    # Total units = 38
    assert breakdown.cutoff1_working_days >= 4
    assert breakdown.cutoff1_total_units > Decimal("0")
    assert breakdown.monthly_total_units == breakdown.cutoff1_total_units + breakdown.cutoff2_total_units
    assert breakdown.monthly_living_budget == breakdown.cutoff1_living_budget + breakdown.cutoff2_living_budget


def test_philippine_holidays_21_entries():
    """Verify full 21 holidays from Holidays!A2:E22 including Emilio Aguinaldo Day."""
    from app.core.calendar_engine import generate_philippine_holidays, DEFAULT_PHILIPPINE_HOLIDAYS_2026

    # Verify at least 21 holidays are registered
    assert len(DEFAULT_PHILIPPINE_HOLIDAYS_2026) >= 21
    holidays = generate_philippine_holidays(2027)
    aguinaldo = [h for h in holidays if "Aguinaldo" in h.name]
    assert len(aguinaldo) == 1
    assert aguinaldo[0].date == date(2027, 3, 22)
    assert aguinaldo[0].scope == "Cavite"


def test_holiday_loss_and_allowances():
    """Verify lost units due to holidays and 1-week base allowance (₱465)."""
    daily_units = {"Mon": Decimal("9"), "Wed": Decimal("10")}
    # August 2026: Aug 31 is National Heroes Day (Monday)
    breakdown = calculate_cutoff_units(
        year=2026,
        month=8,
        daily_units=daily_units,
        hourly_rate=Decimal("198.85"),
        daily_food_rate=Decimal("300.00"),
        daily_transport_rate=Decimal("165.00"),
    )
    # Aug 31 lost Monday = 9 units lost * 198.85
    assert breakdown.lost_units_due_to_holidays == Decimal("9.00")
    assert breakdown.lost_cash_due_to_holidays == Decimal("1789.65")
    # 1-week base allowance: 165 + 300 = 465.00
    assert breakdown.one_week_base_allowance == Decimal("465.00")


def test_unified_budget_pipeline_private():
    """Verify Schedule -> Pinasweldo -> Budget pipeline on 154 units @ ₱198.85."""
    from app.core.calendar_engine import calculate_unified_budget_pipeline

    daily_units = {"0": 9, "1": 0, "2": 10, "3": 0, "4": 10, "5": 7}
    breakdown = calculate_cutoff_units(
        year=2026,
        month=9,
        daily_units=daily_units,
        hourly_rate=Decimal("198.85"),
        daily_food_rate=Decimal("300.00"),
        daily_transport_rate=Decimal("165.00"),
    )
    assert breakdown.cutoff1_gross_pay == Decimal("14317.20")
    assert breakdown.cutoff2_gross_pay == Decimal("16305.70")
    assert breakdown.monthly_gross_pay == Decimal("30622.90")

    res = calculate_unified_budget_pipeline(
        cutoff_breakdown=breakdown,
        tax_mode="pinasweldo_private",
        tax_split_method="equal_split",
        living_expense_option="one_week",
        rent_perceived=Decimal("2500.00"),
        utilities_perceived=Decimal("3175.00"),
        additionals=[
            {"label": "September", "amount": "4000.00"},
            {"label": "additional transfer", "amount": "4700.00"},
        ],
    )
    assert res["b8_gross_total"] == "30622.90"
    assert res["statutory_breakdown"]["sss"] == "1525.00"
    assert res["statutory_breakdown"]["philhealth"] in ["765.57", "765.58"]
    assert res["statutory_breakdown"]["pagibig"] == "200.00"
    assert res["b10_total_after_tax"] in ["27037.47", "27037.48"]
    assert res["perceived_expenses"]["b22_total_spent"] == "6140.00"
    assert res["perceived_expenses"]["b23_available_after_utility"] in ["20897.47", "20897.48"]
    assert res["additionals_section"]["total_additionals"] == "8700.00"
    assert res["additionals_section"]["b32_money_after_additionals"] in ["29597.47", "29597.48"]


def test_unified_budget_pipeline_8pct_and_legacy():
    """Verify 8% Freelancer mode and Legacy Excel 0% tax mode."""
    from app.core.calendar_engine import calculate_unified_budget_pipeline

    daily_units = {"0": 9, "1": 0, "2": 10, "3": 0, "4": 10, "5": 7}
    breakdown = calculate_cutoff_units(
        year=2026,
        month=9,
        daily_units=daily_units,
        hourly_rate=Decimal("198.85"),
        daily_food_rate=Decimal("300.00"),
        daily_transport_rate=Decimal("165.00"),
    )

    # 8% Freelance Mode
    res_8pct = calculate_unified_budget_pipeline(
        cutoff_breakdown=breakdown,
        tax_mode="pinasweldo_freelance_8pct",
        living_expense_option="one_week",
    )
    assert res_8pct["b8_gross_total"] == "30622.90"
    assert res_8pct["b9_tax_and_statutory"] == "783.17"
    assert res_8pct["b10_total_after_tax"] == "29839.73"
    assert res_8pct["perceived_expenses"]["b23_available_after_utility"] == "23699.73"

    # Excel Legacy 0% Tax Mode (Exact Dan BudgetingV3.xlsx Current Budget parity)
    res_legacy = calculate_unified_budget_pipeline(
        cutoff_breakdown=breakdown,
        tax_mode="legacy_custom",
        custom_tax_rate=Decimal("0.00"),
        living_expense_option="one_week",
        additionals=[
            {"label": "September", "amount": "4000.00"},
            {"label": "additional transfer", "amount": "4700.00"},
        ],
    )
    assert res_legacy["b8_gross_total"] == "30622.90"
    assert res_legacy["b9_tax_and_statutory"] == "0.00"
    assert res_legacy["b10_total_after_tax"] == "30622.90"
    assert res_legacy["perceived_expenses"]["b23_available_after_utility"] == "24482.90"
    assert res_legacy["additionals_section"]["b32_money_after_additionals"] == "33182.90"


def test_holiday_pay_multipliers():
    """Verify Regular (200%) and Special Non-Working (130%) holiday multipliers."""
    from app.core.tax_calculator import calculate_holiday_pay

    # 8 hours regular holiday
    h_reg = calculate_holiday_pay(
        hourly_rate=Decimal("198.85"),
        hours_worked=Decimal("8"),
        holiday_type="Regular Holiday",
    )
    assert h_reg["multiplier"] == "2.00"
    assert h_reg["base_pay"] == "1590.80"
    assert h_reg["total_holiday_pay"] == "3181.60"

    # 8 hours special holiday
    h_spec = calculate_holiday_pay(
        hourly_rate=Decimal("198.85"),
        hours_worked=Decimal("8"),
        holiday_type="Special Non-Working Holiday",
    )
    assert h_spec["multiplier"] == "1.30"
    assert h_spec["total_holiday_pay"] == "2068.04"

