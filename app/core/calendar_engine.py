"""
Bi-Weekly Calendar & Workday Engine.
Python implementation of Excel's NETWORKDAYS.INTL with 7-day binary masks and
Philippine statutory holiday calendar integration.
"""
from datetime import date, timedelta
import calendar
from typing import Set, Dict, List, Any, Optional
from decimal import Decimal
from .decimal_utils import to_decimal, quantize_currency, ZERO

# ---------------------------------------------------------------------------
# Default Statutory Philippine Holidays (Nationwide Observances)
# ---------------------------------------------------------------------------
DEFAULT_PHILIPPINE_HOLIDAYS_2026 = [
    # 2026 Regular & Special Non-Working Holidays
    date(2026, 1, 1),   # New Year's Day
    date(2026, 2, 17),  # Chinese New Year
    date(2026, 2, 25),  # EDSA People Power Anniversary
    date(2026, 3, 20),  # Eid'l Fitr (Estimated)
    date(2026, 4, 2),   # Maundy Thursday
    date(2026, 4, 3),   # Good Friday
    date(2026, 4, 4),   # Black Saturday
    date(2026, 4, 9),   # Araw ng Kagitingan (Day of Valor)
    date(2026, 5, 1),   # Labor Day
    date(2026, 5, 27),  # Eid'l Adha (Estimated)
    date(2026, 6, 12),  # Independence Day
    date(2026, 8, 21),  # Ninoy Aquino Day
    date(2026, 8, 31),  # National Heroes Day
    date(2026, 11, 1),  # All Saints' Day
    date(2026, 11, 2),  # All Souls' Day (Special Non-Working)
    date(2026, 11, 30), # Bonifacio Day
    date(2026, 12, 8),  # Feast of the Immaculate Conception
    date(2026, 12, 24), # Christmas Eve
    date(2026, 12, 25), # Christmas Day
    date(2026, 12, 30), # Rizal Day
    date(2026, 12, 31), # Last Day of the Year
]

DAY_MASKS = {
    0: "0111111",  # Monday only
    1: "1011111",  # Tuesday only
    2: "1101111",  # Wednesday only
    3: "1110111",  # Thursday only
    4: "1111011",  # Friday only
    5: "1111101",  # Saturday only
    6: "1111110",  # Sunday only
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def networkdays_intl(
    start_date: date,
    end_date: date,
    weekend_mask: str = "0000011",
    holidays: Optional[Any] = None
) -> int:
    """
    Exact Python implementation of Excel's NETWORKDAYS.INTL(start_date, end_date, weekend_mask, holidays).
    - weekend_mask: 7-character string of '0' (working) and '1' (non-working) starting on Monday.
    - holidays: set or list of date or Holiday objects excluded from count.
    """
    if start_date > end_date:
        return 0

    if len(weekend_mask) != 7 or not all(c in "01" for c in weekend_mask):
        raise ValueError(f"Invalid weekend mask: {weekend_mask}. Must be 7 characters of '0' and '1'.")

    holiday_set: Set[date] = set()
    if holidays:
        for h in holidays:
            if hasattr(h, "date"):
                holiday_set.add(h.date)
            elif isinstance(h, date):
                holiday_set.add(h)

    current = start_date
    working_days = 0

    while current <= end_date:
        weekday_idx = current.weekday()  # 0 = Monday, 6 = Sunday
        is_weekend = weekend_mask[weekday_idx] == "1"
        is_holiday = current in holiday_set

        if not is_weekend and not is_holiday:
            working_days += 1

        current += timedelta(days=1)

    return working_days


class CalendarEngine:
    """Engine for computing bi-weekly cutoffs, schedule units, and holiday deductions."""

    def __init__(self, holidays: Optional[List[date]] = None):
        self.holidays: Set[date] = set(holidays or DEFAULT_PHILIPPINE_HOLIDAYS_2026)

    def add_holiday(self, holiday_date: date):
        self.holidays.add(holiday_date)

    def remove_holiday(self, holiday_date: date):
        self.holidays.discard(holiday_date)

    def get_cutoff_ranges(self, year: int, month: int) -> Dict[str, tuple]:
        """Return (start_date, end_date) tuples for Cutoff 1 and Cutoff 2."""
        last_day = calendar.monthrange(year, month)[1]
        c1 = (date(year, month, 1), date(year, month, 15))
        c2 = (date(year, month, 16), date(year, month, last_day))
        return {
            "cutoff_1": c1,
            "cutoff_2": c2,
            "month_full": (date(year, month, 1), date(year, month, last_day))
        }

    def calculate_cutoff_workdays_by_day(
        self,
        start_date: date,
        end_date: date,
        include_holidays: bool = False
    ) -> Dict[int, int]:
        """
        Count occurrences of each weekday in the date range.
        If include_holidays is True, holiday days are NOT deducted (Calendar Days).
        If False, holidays are deducted (Working Days).
        """
        counts = {}
        holiday_filter = None if include_holidays else self.holidays
        for day_idx in range(7):
            mask = DAY_MASKS[day_idx]
            counts[day_idx] = networkdays_intl(start_date, end_date, mask, holiday_filter)
        return counts

    def calculate_biweekly_teaching_units(
        self,
        year: int,
        month: int,
        schedule_units_per_day: Dict[int, Decimal],
        hourly_rate: Decimal
    ) -> Dict[str, Any]:
        """
        Calculate units and gross pay across Cutoff 1 (1-15) and Cutoff 2 (16-EOM)
        matching Dan BudgetingV3.xlsx Dashboard logic.
        - schedule_units_per_day: dict of weekday (0=Mon .. 6=Sun) to units/hours.
        """
        ranges = self.get_cutoff_ranges(year, month)
        rate = to_decimal(hourly_rate)

        # Cutoff 1 Working Days
        c1_start, c1_end = ranges["cutoff_1"]
        c1_workdays = self.calculate_cutoff_workdays_by_day(c1_start, c1_end, include_holidays=False)
        c1_caldays = self.calculate_cutoff_workdays_by_day(c1_start, c1_end, include_holidays=True)

        # Cutoff 2 Working Days
        c2_start, c2_end = ranges["cutoff_2"]
        c2_workdays = self.calculate_cutoff_workdays_by_day(c2_start, c2_end, include_holidays=False)
        c2_caldays = self.calculate_cutoff_workdays_by_day(c2_start, c2_end, include_holidays=True)

        c1_units = ZERO
        c2_units = ZERO
        c1_total_workdays = 0
        c2_total_workdays = 0
        c1_holiday_days = 0
        c2_holiday_days = 0

        breakdown_by_day = []

        for d_idx in range(7):
            units = to_decimal(schedule_units_per_day.get(d_idx, ZERO))
            c1_days = c1_workdays[d_idx]
            c2_days = c2_workdays[d_idx]
            c1_cal = c1_caldays[d_idx]
            c2_cal = c2_caldays[d_idx]

            c1_units += Decimal(str(c1_days)) * units
            c2_units += Decimal(str(c2_days)) * units

            c1_total_workdays += c1_days
            c2_total_workdays += c2_days
            c1_holiday_days += (c1_cal - c1_days)
            c2_holiday_days += (c2_cal - c2_days)

            breakdown_by_day.append({
                "day_index": d_idx,
                "day_name": DAY_NAMES[d_idx],
                "units_per_day": units,
                "c1_workdays": c1_days,
                "c2_workdays": c2_days,
                "c1_units": Decimal(str(c1_days)) * units,
                "c2_units": Decimal(str(c2_days)) * units,
                "total_month_units": (Decimal(str(c1_days + c2_days)) * units)
            })

        total_units = c1_units + c2_units
        c1_gross = quantize_currency(c1_units * rate)
        c2_gross = quantize_currency(c2_units * rate)
        total_gross = c1_gross + c2_gross

        return {
            "year": year,
            "month": month,
            "hourly_rate": rate,
            "cutoff_1": {
                "start_date": c1_start.isoformat(),
                "end_date": c1_end.isoformat(),
                "working_days": c1_total_workdays,
                "holidays": c1_holiday_days,
                "units": c1_units,
                "gross_pay": c1_gross
            },
            "cutoff_2": {
                "start_date": c2_start.isoformat(),
                "end_date": c2_end.isoformat(),
                "working_days": c2_total_workdays,
                "holidays": c2_holiday_days,
                "units": c2_units,
                "gross_pay": c2_gross
            },
            "month_totals": {
                "working_days": c1_total_workdays + c2_total_workdays,
                "holidays": c1_holiday_days + c2_holiday_days,
                "units": total_units,
                "gross_pay": total_gross
            },
            "day_breakdowns": breakdown_by_day
        }


# ---------------------------------------------------------------------------
# High-Level Dataclasses & API Functions
# ---------------------------------------------------------------------------
from dataclasses import dataclass


@dataclass
class Holiday:
    date: date
    name: str
    law_type: str = "Regular Holiday"
    scope: str = "Nationwide"


@dataclass
class CutoffBreakdown:
    year: int
    month: int
    cutoff1_working_days: int
    cutoff1_total_units: Decimal
    cutoff1_gross_pay: Decimal
    cutoff1_living_budget: Decimal
    cutoff2_working_days: int
    cutoff2_total_units: Decimal
    cutoff2_gross_pay: Decimal
    cutoff2_living_budget: Decimal
    monthly_working_days: int
    monthly_total_units: Decimal
    monthly_gross_pay: Decimal
    monthly_living_budget: Decimal
    raw_payload: Dict[str, Any]


def generate_philippine_holidays(year: int = 2026) -> List[Holiday]:
    """Return default statutory Philippine holidays for the given year."""
    return [
        Holiday(d, f"PH Holiday {d.strftime('%b %d')}")
        for d in DEFAULT_PHILIPPINE_HOLIDAYS_2026
    ]


DAY_NAME_TO_INDEX = {
    "mon": 0, "monday": 0,
    "tue": 1, "tues": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thurs": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}


def calculate_cutoff_units(
    year: int,
    month: int,
    daily_units: Dict[str | int, Any],
    hourly_rate: Decimal,
    daily_food_rate: Decimal = Decimal("200.00"),
    daily_transport_rate: Decimal = Decimal("150.00"),
    holidays: Optional[List[Holiday] | List[date]] = None,
) -> CutoffBreakdown:
    """Calculate bi-weekly teaching units, gross pay, and living budget."""
    holiday_dates = []
    if holidays:
        for h in holidays:
            if hasattr(h, "date"):
                holiday_dates.append(h.date)
            elif isinstance(h, date):
                holiday_dates.append(h)
    else:
        holiday_dates = DEFAULT_PHILIPPINE_HOLIDAYS_2026

    engine = CalendarEngine(holidays=holiday_dates)

    # Normalize daily_units keys to 0..6 integers
    sched_map: Dict[int, Decimal] = {}
    for k, v in daily_units.items():
        if isinstance(k, int):
            sched_map[k] = to_decimal(v)
        elif isinstance(k, str):
            idx = DAY_NAME_TO_INDEX.get(k.strip().lower(), -1)
            if idx >= 0:
                sched_map[idx] = to_decimal(v)

    payload = engine.calculate_biweekly_teaching_units(
        year=year,
        month=month,
        schedule_units_per_day=sched_map,
        hourly_rate=hourly_rate,
    )

    daily_allowance = to_decimal(daily_food_rate) + to_decimal(daily_transport_rate)
    c1_days = payload["cutoff_1"]["working_days"]
    c2_days = payload["cutoff_2"]["working_days"]
    c1_budget = quantize_currency(Decimal(str(c1_days)) * daily_allowance)
    c2_budget = quantize_currency(Decimal(str(c2_days)) * daily_allowance)

    return CutoffBreakdown(
        year=year,
        month=month,
        cutoff1_working_days=c1_days,
        cutoff1_total_units=payload["cutoff_1"]["units"],
        cutoff1_gross_pay=payload["cutoff_1"]["gross_pay"],
        cutoff1_living_budget=c1_budget,
        cutoff2_working_days=c2_days,
        cutoff2_total_units=payload["cutoff_2"]["units"],
        cutoff2_gross_pay=payload["cutoff_2"]["gross_pay"],
        cutoff2_living_budget=c2_budget,
        monthly_working_days=payload["month_totals"]["working_days"],
        monthly_total_units=payload["month_totals"]["units"],
        monthly_gross_pay=payload["month_totals"]["gross_pay"],
        monthly_living_budget=c1_budget + c2_budget,
        raw_payload=payload,
    )
