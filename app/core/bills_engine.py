"""
Monthly Bills & Roommate Utility Cost Splitting Engine.
Matches Dan BudgetingV3.xlsx 'Monthly Bills' sheet logic:
- Dynamic multi-occupant division: Total / active_tenants
- 3-Month rolling utility averages
- Payment status tracking (Paid, Pending, Complete)
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from .decimal_utils import to_decimal, quantize_currency, ZERO


class MonthlyBillRecord:
    """Represents a single monthly utility and rent billing record."""

    def __init__(
        self,
        billing_month: str,
        rent: Decimal,
        water: Decimal,
        electricity: Decimal,
        internet: Decimal,
        other_utils: Decimal = ZERO,
        occupants: Optional[List[Dict[str, Any]]] = None,
        status: str = "Paid",
        notes: str = "",
        per_person: Decimal = ZERO
    ):
        self.billing_month = str(billing_month).strip()
        self.rent = quantize_currency(rent)
        self.water = quantize_currency(water)
        self.electricity = quantize_currency(electricity)
        self.internet = quantize_currency(internet)
        self.other_utils = quantize_currency(other_utils)
        self.status = status
        self.notes = notes
        self.per_person = to_decimal(per_person)

        # Default occupants: Dan, Jaco, Troy
        self.occupants = occupants if occupants is not None else [
            {"name": "Dan", "is_active": True},
            {"name": "Jaco", "is_active": True},
            {"name": "Troy", "is_active": True}
        ]

    @property
    def total_utils(self) -> Decimal:
        """Total utility bill (water + electricity + internet + other)."""
        return self.water + self.electricity + self.internet + self.other_utils

    @property
    def total_bill(self) -> Decimal:
        """Grand total bill including rent."""
        return self.rent + self.total_utils

    @property
    def active_occupants_count(self) -> int:
        return sum(1 for o in self.occupants if o.get("is_active", True))

    def split_breakdown(self) -> Dict[str, Any]:
        """
        Divide rent and utilities among active tenants matching Excel formula:
        IF(Total="", "", IFERROR(Total / COUNTIF(tenants, TRUE), 0))
        """
        count = self.active_occupants_count
        if count == 0:
            per_person_rent = ZERO
            per_person_utils = ZERO
            per_person_total = ZERO
        else:
            d_count = Decimal(str(count))
            per_person_rent = quantize_currency(self.rent / d_count)
            per_person_utils = quantize_currency(self.total_utils / d_count)
            per_person_total = quantize_currency(self.total_bill / d_count)

        occupant_shares = []
        for occ in self.occupants:
            name = occ.get("name", "Occupant")
            is_active = occ.get("is_active", True)
            if is_active:
                occupant_shares.append({
                    "name": name,
                    "is_active": True,
                    "rent_share": per_person_rent,
                    "utils_share": per_person_utils,
                    "total_share": per_person_total
                })
            else:
                occupant_shares.append({
                    "name": name,
                    "is_active": False,
                    "rent_share": ZERO,
                    "utils_share": ZERO,
                    "total_share": ZERO
                })

        return {
            "billing_month": self.billing_month,
            "rent": self.rent,
            "water": self.water,
            "electricity": self.electricity,
            "internet": self.internet,
            "other_utils": self.other_utils,
            "total_utils": self.total_utils,
            "total_bill": self.total_bill,
            "active_count": count,
            "per_person_rent": per_person_rent,
            "per_person_utils": per_person_utils,
            "per_person_total": per_person_total,
            "status": self.status,
            "notes": self.notes,
            "occupant_shares": occupant_shares
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "billing_month": self.billing_month,
            "rent": str(self.rent),
            "water": str(self.water),
            "electricity": str(self.electricity),
            "internet": str(self.internet),
            "other_utils": str(self.other_utils),
            "total_utils": str(self.total_utils),
            "total_bill": str(self.total_bill),
            "occupants": self.occupants,
            "status": self.status,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonthlyBillRecord":
        return cls(
            billing_month=data.get("billing_month", ""),
            rent=to_decimal(data.get("rent", 0)),
            water=to_decimal(data.get("water", 0)),
            electricity=to_decimal(data.get("electricity", 0)),
            internet=to_decimal(data.get("internet", 0)),
            other_utils=to_decimal(data.get("other_utils", 0)),
            occupants=data.get("occupants", None),
            status=data.get("status", "Paid"),
            notes=data.get("notes", "")
        )


class BillsEngine:
    """Manages bill history and computes rolling trends & roommate distributions."""

    def __init__(self, records: Optional[List[MonthlyBillRecord]] = None):
        self.records: List[MonthlyBillRecord] = records or []

    def add_or_update_record(self, record: MonthlyBillRecord):
        for i, r in enumerate(self.records):
            if r.billing_month == record.billing_month:
                self.records[i] = record
                return
        self.records.append(record)

    def calculate_rolling_averages(self, window: int = 3) -> Dict[str, Decimal]:
        """
        Calculate rolling N-month averages matching Excel formula:
        AVERAGE(OFFSET(start, count-3, 0, 3, 1))
        """
        if not self.records:
            return {
                "rent_avg": ZERO,
                "water_avg": ZERO,
                "electricity_avg": ZERO,
                "internet_avg": ZERO,
                "utils_avg": ZERO,
                "total_avg": ZERO,
                "sample_count": 0
            }

        # Take last window records
        recent = self.records[-window:]
        n = Decimal(str(len(recent)))

        sum_rent = sum((r.rent for r in recent), ZERO)
        sum_water = sum((r.water for r in recent), ZERO)
        sum_elec = sum((r.electricity for r in recent), ZERO)
        sum_net = sum((r.internet for r in recent), ZERO)
        sum_utils = sum((r.total_utils for r in recent), ZERO)
        sum_total = sum((r.total_bill for r in recent), ZERO)

        return {
            "rent_avg": quantize_currency(sum_rent / n),
            "water_avg": quantize_currency(sum_water / n),
            "electricity_avg": quantize_currency(sum_elec / n),
            "internet_avg": quantize_currency(sum_net / n),
            "utils_avg": quantize_currency(sum_utils / n),
            "total_avg": quantize_currency(sum_total / n),
            "sample_count": len(recent)
        }

    def get_latest_bill(self) -> Optional[MonthlyBillRecord]:
        return self.records[-1] if self.records else None

    def calculate_ytd_summary(self) -> Dict[str, Any]:
        """Calculate YTD summary matching Monthly Bills A408:B413.

        - Months Paid: COUNTIF(L3:L405, 'Paid') -> 14
        - YTD Total Bills: SUMIF(L3:L405, 'Paid', G3:G405) -> ₱136,210.91
        - YTD Avg Per Person: SUMIF(L3:L405, 'Paid', K3:K405) / COUNTIF(L3:L405, 'Paid') -> ₱3,716.07
        - Highest Month (Total): MAX across paid months -> ₱12,794.63
        - Lowest Month (Paid): MIN across paid months -> ₱0.00
        """
        paid = [r for r in self.records if str(r.status).strip().lower() == "paid"]
        count = len(paid)
        if count == 0:
            return {
                "months_paid": 0,
                "ytd_total_bills": "0.00",
                "ytd_avg_per_person": "0.00",
                "highest_month_total": "0.00",
                "lowest_month_paid": "0.00",
            }

        total_bills = sum((r.total_bill for r in paid), ZERO)
        per_person_shares = []
        for r in paid:
            if hasattr(r, "per_person") and r.per_person > ZERO:
                per_person_shares.append(r.per_person)
            else:
                occs = len(r.occupants) if r.occupants else 3
                per_person_shares.append(r.total_bill / Decimal(str(max(1, occs))))
        avg_per_person = sum(per_person_shares, ZERO) / Decimal(str(count))
        highest = max(r.total_bill for r in paid)
        lowest = min(r.total_bill for r in paid)

        return {
            "months_paid": count,
            "ytd_total_bills": str(quantize_currency(total_bills)),
            "ytd_avg_per_person": str(quantize_currency(avg_per_person)),
            "highest_month_total": str(quantize_currency(highest)),
            "lowest_month_paid": str(quantize_currency(lowest)),
        }


def calculate_ytd_summary(records: List[Any]) -> Dict[str, Any]:
    """Calculate YTD Summary stats from list of bill records or history dictionaries."""
    bill_records: List[MonthlyBillRecord] = []
    for r in records:
        if isinstance(r, MonthlyBillRecord):
            bill_records.append(r)
        elif isinstance(r, dict):
            status = r.get("status", "Paid" if to_decimal(r.get("total", 0)) > ZERO else "Pending")
            r_rent = to_decimal(r.get("rent", 0))
            r_water = to_decimal(r.get("water", 0))
            r_elec = to_decimal(r.get("electricity", 0))
            r_net = to_decimal(r.get("internet", 0))
            r_other = to_decimal(r.get("other_utils", 0))
            if r_rent == ZERO and r_water == ZERO and r_elec == ZERO and r_net == ZERO and r_other == ZERO and "total" in r:
                r_other = to_decimal(r["total"])

            bill_records.append(
                MonthlyBillRecord(
                    billing_month=r.get("date", r.get("billing_month", "")),
                    rent=r_rent,
                    water=r_water,
                    electricity=r_elec,
                    internet=r_net,
                    other_utils=r_other,
                    occupants=r.get("active_tenants", r.get("occupants", ["Dan", "Jaco", "Troy"])),
                    status=status,
                    notes=r.get("notes", ""),
                    per_person=to_decimal(r.get("per_person", 0)),
                )
            )
    engine = BillsEngine(records=bill_records)
    return engine.calculate_ytd_summary()


# ---------------------------------------------------------------------------
# High-Level Dataclasses & API Functions
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field
from .decimal_utils import round_up_excel


@dataclass
class UtilityBill:
    name: str
    category: str
    total_amount: Decimal
    is_active: bool = True
    active_tenants: List[str] = field(default_factory=list)


@dataclass
class BillsSummary:
    grand_total: Decimal
    my_total_share: Decimal
    active_bills_count: int
    raw_payload: Dict[str, Any]


def calculate_bill_split(bill: UtilityBill, round_up: bool = False) -> Dict[str, Decimal]:
    """Calculate per-tenant share for a single utility bill."""
    if not bill.is_active or not bill.active_tenants or bill.total_amount <= ZERO:
        return {}

    count = len(bill.active_tenants)
    if count == 0:
        return {}

    d_count = Decimal(str(count))
    if round_up:
        per_share = round_up_excel(bill.total_amount / d_count, 0)
    else:
        per_share = quantize_currency(bill.total_amount / d_count)

    return {tenant: per_share for tenant in bill.active_tenants}


def calculate_rolling_utility_average(
    utility_name: str,
    history: List[Dict[str, Any]],
    window_months: int = 3
) -> Decimal:
    """Calculate rolling N-month average for a specific utility."""
    matching = [
        to_decimal(h.get("amount", 0))
        for h in history
        if str(h.get("name", "")).strip().lower() == utility_name.strip().lower()
    ]
    if not matching:
        return ZERO

    recent = matching[-window_months:]
    n = Decimal(str(len(recent)))
    return quantize_currency(sum(recent, ZERO) / n)


def calculate_total_bills_summary(
    bills: List[UtilityBill],
    my_tenant_name: str = "Dan",
    round_up: bool = False
) -> BillsSummary:
    """Calculate grand total bills and the user's personal share across all bills."""
    grand_total = ZERO
    my_total_share = ZERO
    active_count = 0
    bill_details = []

    for bill in bills:
        if not bill.is_active:
            continue
        active_count += 1
        grand_total += bill.total_amount
        splits = calculate_bill_split(bill, round_up=round_up)
        my_share = splits.get(my_tenant_name, ZERO)
        my_total_share += my_share
        bill_details.append({
            "name": bill.name,
            "category": bill.category,
            "total_amount": bill.total_amount,
            "active_tenants": bill.active_tenants,
            "splits": splits,
            "my_share": my_share
        })

    return BillsSummary(
        grand_total=quantize_currency(grand_total),
        my_total_share=quantize_currency(my_total_share),
        active_bills_count=active_count,
        raw_payload={"bills": bill_details}
    )


# ---------------------------------------------------------------------------
# Color Tokens (from Lists!D1:E8) & Recipient Breakdown (N3:Q6)
# ---------------------------------------------------------------------------
COLOR_TOKENS = {
    "Paid": "#1A7A4A",
    "Pending": "#E8A020",
    "Complete": "#2563A8",
    "Placeholder": "#EBEBEB",
    "Dan": "#D6EAF8",
    "Jaco": "#D5F5E3",
    "Troy": "#FDEBD0",
}


@dataclass
class RecipientBillRow:
    name: str
    rent_to_tita_beth: Decimal
    utilities_to_dan: Decimal
    total_bills: Decimal
    color_hex: str


def calculate_recipient_breakdown(
    rent_amount: Decimal,
    utilities_amount: Decimal,
    tenants: Optional[List[str]] = None,
    rent_payers: Optional[List[str]] = None,
    utils_payers: Optional[List[str]] = None,
    custom_overrides: Optional[Dict[str, Dict[str, Decimal]]] = None
) -> List[RecipientBillRow]:
    """Calculate Latest Month Breakdown separating Rent (to Tita Beth) from Utilities (to Dan).

    Matches Monthly Bills N3:Q6 logic.
    """
    all_tenants = tenants or ["Dan", "Jaco", "Troy"]
    active_rent = rent_payers if rent_payers is not None else ["Dan", "Troy"]
    active_utils = utils_payers if utils_payers is not None else ["Troy"]

    rent_per_person = quantize_currency(to_decimal(rent_amount) / Decimal(str(len(active_rent)))) if active_rent else ZERO
    utils_per_person = quantize_currency(to_decimal(utilities_amount) / Decimal(str(len(active_utils)))) if active_utils else ZERO

    results = []
    for t in all_tenants:
        # Check overrides first
        if custom_overrides and t in custom_overrides:
            t_rent = custom_overrides[t].get("rent", ZERO)
            t_utils = custom_overrides[t].get("utils", ZERO)
        else:
            t_rent = rent_per_person if t in active_rent else ZERO
            # Dan does not pay utilities to himself
            t_utils = utils_per_person if (t in active_utils and t != "Dan") else ZERO

        tot = t_rent + t_utils
        color = COLOR_TOKENS.get(t, "#E2E8F0")

        results.append(RecipientBillRow(
            name=t,
            rent_to_tita_beth=quantize_currency(t_rent),
            utilities_to_dan=quantize_currency(t_utils),
            total_bills=quantize_currency(tot),
            color_hex=color
        ))

    return results
