"""
Bi-Weekly Calendar & Workday Engine.
Python implementation of Excel's NETWORKDAYS.INTL with 7-day binary masks and
Philippine statutory holiday calendar integration.
"""
import json
import urllib.request
import urllib.error
from datetime import date, timedelta
import calendar
from typing import Set, Dict, List, Any, Optional, Tuple
from decimal import Decimal
from .decimal_utils import to_decimal, quantize_currency, ZERO

# ---------------------------------------------------------------------------
# Default Statutory Philippine Holidays (21 Workbook Observances)
# ---------------------------------------------------------------------------
DEFAULT_PHILIPPINE_HOLIDAYS_2026 = [
    date(2026, 8, 21),   # Ninoy Aquino Day
    date(2026, 8, 31),   # National Heroes Day
    date(2026, 11, 1),   # All Saints' Day
    date(2026, 11, 2),   # All Souls' Day
    date(2026, 11, 30),  # Bonifacio Day
    date(2026, 12, 8),   # Feast of the Immaculate Conception
    date(2026, 12, 24),  # Christmas Eve
    date(2026, 12, 25),  # Christmas Day
    date(2026, 12, 30),  # Rizal Day
    date(2026, 12, 31),  # Last Day of the Year
    date(2027, 1, 1),    # New Year's Day
    date(2027, 2, 6),    # Chinese New Year
    date(2027, 2, 25),   # EDSA People Power Revolution Anniversary
    date(2027, 3, 9),    # Eid'l Fitr
    date(2027, 3, 10),   # Eid'l Fitr
    date(2027, 3, 22),   # Emilio Aguinaldo Day (Local Cavite Province)
    date(2027, 3, 25),   # Maundy Thursday
    date(2027, 3, 26),   # Good Friday
    date(2027, 3, 27),   # Black Saturday
    date(2027, 4, 9),    # Araw ng Kagitingan (Day of Valor)
    date(2027, 5, 1),    # Labor Day
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
                if getattr(h, "is_active", True):
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
from dataclasses import dataclass, field



@dataclass
class Holiday:
    date: date
    name: str
    law_type: str = "Regular Holiday"
    scope: str = "Nationwide"
    is_active: bool = True


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
    lost_units_due_to_holidays: Decimal = ZERO
    lost_cash_due_to_holidays: Decimal = ZERO
    one_week_base_allowance: Decimal = ZERO
    full_month_allowance: Decimal = ZERO
    raw_payload: Dict[str, Any] = field(default_factory=dict)


def compute_easter_sunday(year: int) -> date:
    """Meeus/Jones/Butcher algorithm to compute Easter Sunday for any Gregorian calendar year."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def compute_last_monday_of_august(year: int) -> date:
    """Compute National Heroes Day (Last Monday of August under Philippine RA 9492)."""
    d = date(year, 8, 31)
    return d - timedelta(days=d.weekday())


# Multi-year Islamic & Lunar holiday lookup (2020-2035)
ISLAMIC_AND_LUNAR_CALENDAR: Dict[int, Dict[str, Any]] = {
    2020: {"cny": (1, 25), "fitr": [(5, 25)], "adha": (7, 31)},
    2021: {"cny": (2, 12), "fitr": [(5, 13)], "adha": (7, 20)},
    2022: {"cny": (2, 1), "fitr": [(5, 3)], "adha": (7, 9)},
    2023: {"cny": (1, 22), "fitr": [(4, 21)], "adha": (6, 28)},
    2024: {"cny": (2, 10), "fitr": [(4, 10)], "adha": (6, 17)},
    2025: {"cny": (1, 29), "fitr": [(3, 31)], "adha": (6, 6)},
    2026: {"cny": (2, 17), "fitr": [(3, 20), (3, 21)], "adha": (5, 27)},
    2027: {"cny": (2, 6), "fitr": [(3, 9), (3, 10)], "adha": (5, 17)},
    2028: {"cny": (1, 26), "fitr": [(2, 27), (2, 28)], "adha": (5, 5)},
    2029: {"cny": (2, 13), "fitr": [(2, 15), (2, 16)], "adha": (4, 24)},
    2030: {"cny": (2, 3), "fitr": [(2, 5)], "adha": (4, 14)},
    2031: {"cny": (1, 23), "fitr": [(1, 25)], "adha": (4, 3)},
    2032: {"cny": (2, 11), "fitr": [(1, 14)], "adha": (3, 23)},
    2033: {"cny": (1, 31), "fitr": [(1, 3)], "adha": (3, 12)},
    2034: {"cny": (2, 19), "fitr": [(12, 23)], "adha": (3, 1)},
    2035: {"cny": (2, 8), "fitr": [(12, 12)], "adha": (2, 19)},
}


PHILIPPINE_HOLIDAYS_FULL: List[Holiday] = [
    Holiday(date(2026, 8, 21), "Ninoy Aquino Day", "Special Non-Working Day", "Nationwide"),
    Holiday(date(2026, 8, 31), "National Heroes Day", "Regular Holiday", "Nationwide"),
    Holiday(date(2026, 11, 1), "All Saints' Day", "Special Non-Working Day", "Nationwide"),
    Holiday(date(2026, 11, 2), "All Souls' Day", "Special Working Day", "Nationwide"),
    Holiday(date(2026, 11, 30), "Bonifacio Day", "Regular Holiday", "Nationwide"),
    Holiday(date(2026, 12, 8), "Feast of the Immaculate Conception", "Special Non-Working Day", "Nationwide"),
    Holiday(date(2026, 12, 24), "Christmas Eve", "Special Non-Working Day", "Nationwide"),
    Holiday(date(2026, 12, 25), "Christmas Day", "Regular Holiday", "Nationwide"),
    Holiday(date(2026, 12, 30), "Rizal Day", "Regular Holiday", "Nationwide"),
    Holiday(date(2026, 12, 31), "Last Day of the Year", "Special Non-Working Day", "Nationwide"),
    Holiday(date(2027, 1, 1), "New Year's Day", "Regular Holiday", "Nationwide"),
    Holiday(date(2027, 2, 6), "Chinese New Year", "Special Non-Working Day", "Nationwide"),
    Holiday(date(2027, 2, 25), "EDSA People Power Revolution Anniversary", "Special Non-Working Day", "Nationwide"),
    Holiday(date(2027, 3, 9), "Eid'l Fitr (Day 1)", "Regular Holiday", "Nationwide"),
    Holiday(date(2027, 3, 10), "Eid'l Fitr (Day 2)", "Regular Holiday", "Nationwide"),
    Holiday(date(2027, 3, 22), "Emilio Aguinaldo Day", "Special Non-Working Day", "Cavite"),
    Holiday(date(2027, 3, 25), "Maundy Thursday", "Regular Holiday", "Nationwide"),
    Holiday(date(2027, 3, 26), "Good Friday", "Regular Holiday", "Nationwide"),
    Holiday(date(2027, 3, 27), "Black Saturday", "Special Non-Working Day", "Nationwide"),
    Holiday(date(2027, 4, 9), "Araw ng Kagitingan (Day of Valor)", "Regular Holiday", "Nationwide"),
    Holiday(date(2027, 5, 1), "Labor Day", "Regular Holiday", "Nationwide"),
]


def generate_philippine_holidays(year: Optional[int] = None) -> List[Holiday]:
    """Dynamically generate the complete statutory Philippine holiday calendar for any year."""
    if year is None:
        return list(PHILIPPINE_HOLIDAYS_FULL)

    easter = compute_easter_sunday(year)
    heroes = compute_last_monday_of_august(year)
    lunar = ISLAMIC_AND_LUNAR_CALENDAR.get(
        year,
        {"cny": (2, 1), "fitr": [(3, 15)], "adha": (5, 20)}
    )

    holidays: List[Holiday] = []

    # 1. Regular Fixed Holidays (200% Pay)
    holidays.append(Holiday(date(year, 1, 1), "New Year's Day", "Regular Holiday", "Nationwide"))
    holidays.append(Holiday(date(year, 4, 9), "Araw ng Kagitingan (Day of Valor)", "Regular Holiday", "Nationwide"))
    holidays.append(Holiday(date(year, 5, 1), "Labor Day", "Regular Holiday", "Nationwide"))
    holidays.append(Holiday(date(year, 6, 12), "Independence Day", "Regular Holiday", "Nationwide"))
    holidays.append(Holiday(heroes, "National Heroes Day", "Regular Holiday", "Nationwide"))
    holidays.append(Holiday(date(year, 11, 30), "Bonifacio Day", "Regular Holiday", "Nationwide"))
    holidays.append(Holiday(date(year, 12, 25), "Christmas Day", "Regular Holiday", "Nationwide"))
    holidays.append(Holiday(date(year, 12, 30), "Rizal Day", "Regular Holiday", "Nationwide"))

    # 2. Regular Movable Holidays (Holy Week & Islamic)
    holidays.append(Holiday(easter - timedelta(days=3), "Maundy Thursday", "Regular Holiday", "Nationwide"))
    holidays.append(Holiday(easter - timedelta(days=2), "Good Friday", "Regular Holiday", "Nationwide"))

    for idx, (fm, fd) in enumerate(lunar["fitr"]):
        label = f"Eid'l Fitr (Day {idx + 1})" if len(lunar["fitr"]) > 1 else "Eid'l Fitr"
        holidays.append(Holiday(date(year, fm, fd), label, "Regular Holiday", "Nationwide"))

    am, ad = lunar["adha"]
    holidays.append(Holiday(date(year, am, ad), "Eid'l Adha", "Regular Holiday", "Nationwide"))

    # 3. Special Non-Working Fixed Holidays (130% Pay)
    holidays.append(Holiday(date(year, 2, 25), "EDSA People Power Revolution Anniversary", "Special Non-Working Day", "Nationwide"))
    holidays.append(Holiday(date(year, 3, 22), "Emilio Aguinaldo Day", "Special Non-Working Day", "Cavite"))
    holidays.append(Holiday(date(year, 8, 21), "Ninoy Aquino Day", "Special Non-Working Day", "Nationwide"))
    holidays.append(Holiday(date(year, 11, 1), "All Saints' Day", "Special Non-Working Day", "Nationwide"))
    holidays.append(Holiday(date(year, 11, 2), "All Souls' Day", "Special Working Day", "Nationwide"))
    holidays.append(Holiday(date(year, 12, 8), "Feast of the Immaculate Conception", "Special Non-Working Day", "Nationwide"))
    holidays.append(Holiday(date(year, 12, 24), "Christmas Eve", "Special Non-Working Day", "Nationwide"))
    holidays.append(Holiday(date(year, 12, 31), "Last Day of the Year", "Special Non-Working Day", "Nationwide"))

    # 4. Special Non-Working Movable Holidays
    c_m, c_d = lunar["cny"]
    holidays.append(Holiday(date(year, c_m, c_d), "Chinese New Year", "Special Non-Working Day", "Nationwide"))
    holidays.append(Holiday(easter - timedelta(days=1), "Black Saturday", "Special Non-Working Day", "Nationwide"))

    holidays.sort(key=lambda h: h.date)
    return holidays


def fetch_external_philippine_holidays(year: int, timeout: float = 4.0) -> Tuple[List[Holiday], str]:
    """
    Fetch Philippine holidays from external public calendar API (Nager.Date v3).
    Classifies legal pay categories (Regular 200%, Special Non-Working 130%, Special Working 100%)
    and supplements missing Islamic/Cavite observances.
    Falls back gracefully to offline dynamic engine if offline or unreachable.
    Returns: (List[Holiday], source_label)
    """
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/PH"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "BudgetingApp/0.2.0 (Philippine Statutory Suite)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                raw_data = json.loads(response.read().decode("utf-8"))
                external_holidays: List[Holiday] = []
                seen_dates: Set[date] = set()

                regular_names = {
                    "new year", "maundy thursday", "good friday", "day of valor",
                    "araw ng kagitingan", "labour", "labor", "independence",
                    "national heroes", "bonifacio", "christmas day", "rizal",
                    "eid'l fitr", "eidul fitr", "eid'l adha", "eidul adha"
                }
                special_working = {"all souls' day"}

                for item in raw_data:
                    dt = date.fromisoformat(item["date"])
                    name = item.get("name", "").strip() or item.get("localName", "").strip()
                    lower_name = name.lower()

                    if any(r in lower_name for r in regular_names):
                        law_type = "Regular Holiday"
                    elif any(w in lower_name for w in special_working):
                        law_type = "Special Working Day"
                    else:
                        law_type = "Special Non-Working Day"

                    scope = "Cavite" if "aguinaldo" in lower_name else "Nationwide"
                    external_holidays.append(Holiday(
                        date=dt,
                        name=name,
                        law_type=law_type,
                        scope=scope,
                        is_active=True
                    ))
                    seen_dates.add(dt)

                # Supplement any missing statutory holidays (e.g. Islamic lunar dates or Cavite day)
                defaults = generate_philippine_holidays(year)
                for dh in defaults:
                    if dh.date not in seen_dates:
                        external_holidays.append(dh)
                        seen_dates.add(dh.date)

                external_holidays.sort(key=lambda h: h.date)
                return external_holidays, "nager_external_api"
    except Exception:
        pass

    # Graceful fallback to offline statutory calculation engine
    return generate_philippine_holidays(year), "offline_dynamic_engine"


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
    """Calculate bi-weekly teaching units, gross pay, lost holiday units, and living budget."""
    holiday_dates = []
    if holidays:
        for h in holidays:
            if hasattr(h, "date"):
                if getattr(h, "is_active", True):
                    holiday_dates.append(h.date)
            elif isinstance(h, date):
                holiday_dates.append(h)
    else:
        holiday_dates = [h.date for h in generate_philippine_holidays(year) if getattr(h, "is_active", True)]

    engine = CalendarEngine(holidays=holiday_dates)

    # Normalize daily_units keys to 0..6 integers
    sched_map: Dict[int, Decimal] = {}
    for k, v in daily_units.items():
        if isinstance(k, int):
            sched_map[k] = to_decimal(v)
        elif isinstance(k, str):
            if k.strip().isdigit():
                sched_map[int(k.strip())] = to_decimal(v)
            else:
                idx = DAY_NAME_TO_INDEX.get(k.strip().lower(), -1)
                if idx >= 0:
                    sched_map[idx] = to_decimal(v)

    payload = engine.calculate_biweekly_teaching_units(
        year=year,
        month=month,
        schedule_units_per_day=sched_map,
        hourly_rate=hourly_rate,
    )

    # Calculate lost units due to holidays: SUMPRODUCT(Holidays_Per_Weekday, Units_Per_Weekday)
    lost_units = ZERO
    for d_idx in range(7):
        units = sched_map.get(d_idx, ZERO)
        mask = DAY_MASKS[d_idx]
        last_day = calendar.monthrange(year, month)[1]
        cal_days = networkdays_intl(date(year, month, 1), date(year, month, last_day), mask, holidays=None)
        work_days = networkdays_intl(date(year, month, 1), date(year, month, last_day), mask, holidays=holiday_dates)
        holidays_on_day = Decimal(str(cal_days - work_days))
        lost_units += (holidays_on_day * units)

    rate = to_decimal(hourly_rate)
    lost_cash = quantize_currency(lost_units * rate)

    daily_allowance = to_decimal(daily_food_rate) + to_decimal(daily_transport_rate)
    c1_days = payload["cutoff_1"]["working_days"]
    c2_days = payload["cutoff_2"]["working_days"]
    c1_budget = quantize_currency(Decimal(str(c1_days)) * daily_allowance)
    c2_budget = quantize_currency(Decimal(str(c2_days)) * daily_allowance)

    one_week_base = quantize_currency(to_decimal(daily_food_rate) + to_decimal(daily_transport_rate))
    full_month_budget = c1_budget + c2_budget


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
        monthly_living_budget=full_month_budget,
        lost_units_due_to_holidays=lost_units,
        lost_cash_due_to_holidays=lost_cash,
        one_week_base_allowance=one_week_base,
        full_month_allowance=full_month_budget,
        raw_payload=payload,
    )


def calculate_unified_budget_pipeline(
    cutoff_breakdown: CutoffBreakdown,
    tax_mode: str = "pinasweldo_private",
    tax_split_method: str = "equal_split",
    living_expense_option: str = "one_week",
    rent_perceived: Decimal = Decimal("2500.00"),
    utilities_perceived: Decimal = Decimal("3175.00"),
    additionals: Optional[List[Dict[str, Any]]] = None,
    payables: Optional[List[Dict[str, Any]]] = None,
    include_13th_month: bool = False,
    months_worked_13th: Decimal = Decimal("12"),
    custom_tax_rate: Decimal = Decimal("0.00"),
) -> Dict[str, Any]:
    """
    Unified Schedule -> Pinasweldo -> Current Budget Pipeline.

    Fuses teaching schedule cutoffs directly into Philippine statutory calculations
    and updates Current Budget rows B8..B32, R31, and Dashboard metrics.
    """
    from .tax_calculator import (
        calculate_salary_payload,
        calculate_cutoff_deductions_split,
        calculate_13th_month_pay,
    )

    c1_gross = cutoff_breakdown.cutoff1_gross_pay
    c2_gross = cutoff_breakdown.cutoff2_gross_pay
    monthly_gross = cutoff_breakdown.monthly_gross_pay
    monthly_units = cutoff_breakdown.monthly_total_units

    # 1. Pinasweldo / Tax calculation based on mode
    salary_payload = None
    tax_desc = ""

    if tax_mode == "pinasweldo_private":
        salary_payload = calculate_salary_payload(monthly_gross, status="private")
        total_deductions = salary_payload["total_deductions"]
        statutory_ee = salary_payload["statutory_ee"]
        withholding_tax = salary_payload["withholding_tax_monthly"]
        net_pay = salary_payload["net_monthly"]
        tax_desc = "Private Employee (SSS + PhilHealth + Pag-IBIG + BIR TRAIN)"
    elif tax_mode == "pinasweldo_freelance_8pct":
        salary_payload = calculate_salary_payload(monthly_gross, status="freelancer", freelance_mode="eight")
        statutory_ee = ZERO
        withholding_tax = salary_payload["withholding_tax_monthly"]
        total_deductions = withholding_tax
        net_pay = quantize_currency(monthly_gross - total_deductions)
        tax_desc = "COS / Part-Time / Freelance (8% Flat Tax over ₱250k)"
    elif tax_mode == "pinasweldo_government":
        salary_payload = calculate_salary_payload(monthly_gross, status="government")
        total_deductions = salary_payload["total_deductions"]
        statutory_ee = salary_payload["statutory_ee"]
        withholding_tax = salary_payload["withholding_tax_monthly"]
        net_pay = salary_payload["net_monthly"]
        tax_desc = "Government Sector (GSIS 9% + PhilHealth + Pag-IBIG + BIR TRAIN)"
    else:  # legacy_custom (Excel legacy formula B10 = B8 - (B8 * B9))
        rate = to_decimal(custom_tax_rate)
        total_deductions = quantize_currency(monthly_gross * rate)
        statutory_ee = ZERO
        withholding_tax = total_deductions
        net_pay = quantize_currency(monthly_gross - total_deductions)
        pct_display = (rate * Decimal("100")).quantize(Decimal("0.1"))
        tax_desc = f"Excel Legacy Formula (Tax Rate: {pct_display}%)"

    effective_rate = (
        quantize_currency((total_deductions / monthly_gross) * Decimal("100"))
        if monthly_gross > ZERO
        else ZERO
    )

    # 2. Semi-monthly Cutoff Deduction Splitting
    if salary_payload is not None:
        split_res = calculate_cutoff_deductions_split(
            cutoff1_gross=c1_gross,
            cutoff2_gross=c2_gross,
            salary_payload=salary_payload,
            split_method=tax_split_method,
        )
    else:
        c1_d = quantize_currency(total_deductions / Decimal("2"))
        c2_d = total_deductions - c1_d
        split_res = {
            "split_method": tax_split_method,
            "monthly_gross": str(monthly_gross),
            "total_deductions": str(total_deductions),
            "total_net": str(net_pay),
            "cutoff_1": {
                "gross": str(c1_gross),
                "deductions": str(c1_d),
                "net_pay": str(quantize_currency(max(ZERO, c1_gross - c1_d))),
                "items": {"share": str(c1_d)},
            },
            "cutoff_2": {
                "gross": str(c2_gross),
                "deductions": str(c2_d),
                "net_pay": str(quantize_currency(max(ZERO, c2_gross - c2_d))),
                "items": {"share": str(c2_d)},
            },
        }

    # 3. Perceived Living Expenses & Utilities (B22)
    rent = to_decimal(rent_perceived)
    utils = to_decimal(utilities_perceived)
    if living_expense_option == "full_month":
        living_cost = cutoff_breakdown.full_month_allowance
        living_label = f"Full Monthly Working-Day Allowance ({cutoff_breakdown.monthly_working_days} days)"
    else:
        living_cost = cutoff_breakdown.one_week_base_allowance
        living_label = "1-Week Base Living Allowance"

    total_spent_b22 = quantize_currency(rent + utils + living_cost)
    money_available_b23 = quantize_currency(net_pay - total_spent_b22)

    # 4. Additionals (A25:B32) with 13th-Month Injection
    add_list = list(additionals or [])
    if include_13th_month:
        bonus_calc = calculate_13th_month_pay(monthly_gross, months_worked=months_worked_13th)
        bonus_val = bonus_calc["total_bonus"]
        add_list.append({
            "label": f"13th-Month Pay Bonus ({months_worked_13th} mos)",
            "amount": str(bonus_val),
            "is_13th_month": True,
        })

    total_additionals = sum((to_decimal(a.get("amount", 0)) for a in add_list), ZERO)
    money_after_additionals_b32 = quantize_currency(money_available_b23 + total_additionals)

    # 5. Payables (P2:R31)
    pay_list = list(payables or [])
    total_payables = sum((to_decimal(p.get("price", p.get("amount", 0))) for p in pay_list), ZERO)
    money_after_payables_r31 = quantize_currency(money_after_additionals_b32 - total_payables)

    # 6. Precompute Side-by-Side Comparison Modes
    def _quick_mode(mode_key: str, s_status: str, freelance_m: Optional[str] = None) -> Dict[str, Any]:
        if mode_key == "legacy":
            t_ded = ZERO
            n_pay = monthly_gross
            avail = quantize_currency(n_pay - total_spent_b22)
            after_add = quantize_currency(avail + total_additionals)
            return {
                "gross": str(monthly_gross),
                "statutory": "0.00",
                "tax": "0.00",
                "total_deductions": "0.00",
                "net_pay": str(n_pay),
                "money_after_utility": str(avail),
                "money_after_additionals": str(after_add),
                "money_after_payables": str(quantize_currency(after_add - total_payables)),
            }
        p = calculate_salary_payload(monthly_gross, status=s_status, freelance_mode=freelance_m)
        stat = p["statutory_ee"]
        tx = p["withholding_tax_monthly"]
        if mode_key == "freelance_8pct":
            stat = ZERO
            tot_d = tx
        else:
            tot_d = p["total_deductions"]
        np_val = quantize_currency(monthly_gross - tot_d)
        avail_val = quantize_currency(np_val - total_spent_b22)
        add_val = quantize_currency(avail_val + total_additionals)
        return {
            "gross": str(monthly_gross),
            "statutory": str(stat),
            "tax": str(tx),
            "total_deductions": str(tot_d),
            "net_pay": str(np_val),
            "money_after_utility": str(avail_val),
            "money_after_additionals": str(add_val),
            "money_after_payables": str(quantize_currency(add_val - total_payables)),
        }

    comparison = {
        "legacy_excel_0pct": _quick_mode("legacy", "private"),
        "pinasweldo_private": _quick_mode("private", "private"),
        "pinasweldo_freelance_8pct": _quick_mode("freelance_8pct", "freelancer", "eight"),
        "pinasweldo_government": _quick_mode("government", "government"),
    }

    return {
        "year": cutoff_breakdown.year,
        "month": cutoff_breakdown.month,
        "tax_mode": tax_mode,
        "tax_description": tax_desc,
        "tax_split_method": tax_split_method,
        "living_expense_option": living_expense_option,
        "living_label": living_label,
        "monthly_units": str(monthly_units),
        "b8_gross_total": str(monthly_gross),
        "b9_tax_and_statutory": str(total_deductions),
        "b9_effective_rate": str(effective_rate),
        "b10_total_after_tax": str(net_pay),
        "cutoff_1": {
            "units": str(cutoff_breakdown.cutoff1_total_units),
            "gross": str(c1_gross),
            "deductions": split_res["cutoff_1"]["deductions"],
            "net_pay": split_res["cutoff_1"]["net_pay"],
            "items": split_res["cutoff_1"].get("items", {}),
        },
        "cutoff_2": {
            "units": str(cutoff_breakdown.cutoff2_total_units),
            "gross": str(c2_gross),
            "deductions": split_res["cutoff_2"]["deductions"],
            "net_pay": split_res["cutoff_2"]["net_pay"],
            "items": split_res["cutoff_2"].get("items", {}),
        },
        "statutory_breakdown": {
            "sss": str(salary_payload["sss"]["ee_total"]) if salary_payload and "sss" in salary_payload else "0.00",
            "philhealth": str(salary_payload["philhealth"]["ee_share"]) if salary_payload and "philhealth" in salary_payload else "0.00",
            "pagibig": str(salary_payload["pagibig"]["ee_share"]) if salary_payload and "pagibig" in salary_payload else "0.00",
            "gsis": str(salary_payload["gsis"]["ee_share"]) if salary_payload and "gsis" in salary_payload else "0.00",
            "withholding_tax": str(withholding_tax),
            "total_deductions": str(total_deductions),
        },
        "perceived_expenses": {
            "rent_b12": str(rent),
            "utilities_b13": str(utils),
            "living_cost": str(living_cost),
            "b22_total_spent": str(total_spent_b22),
            "b23_available_after_utility": str(money_available_b23),
        },
        "additionals_section": {
            "items": add_list,
            "total_additionals": str(total_additionals),
            "b32_money_after_additionals": str(money_after_additionals_b32),
        },
        "payables_section": {
            "items": pay_list,
            "total_payables": str(total_payables),
            "r31_money_after_payables": str(money_after_payables_r31),
        },
        "side_by_side_comparison": comparison,
    }
