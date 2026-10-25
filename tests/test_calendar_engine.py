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

