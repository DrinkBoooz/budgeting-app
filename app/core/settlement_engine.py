"""
Peer Settlement, Family Remittance, and Executive Cash Flow Reconciliation Engine.
Implements Dan BudgetingV3.xlsx logic:
- Calumpang peer-to-peer 50/50 division with Excel ROUNDUP(price/2, 0)
- Mama Groceries net remittance calculation (Items - Deductions)
- Executive Dashboard Cash Flow waterfall
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from .decimal_utils import to_decimal, quantize_currency, round_up_excel, ZERO


class PeerSettlementItem:
    """A shared expenditure item with 50/50 or custom split."""

    def __init__(
        self,
        item_name: str,
        price: Decimal,
        paid_by: str = "Dan",
        troy_share: Optional[Decimal] = None,
        jaco_share: Optional[Decimal] = None,
        dan_share: Optional[Decimal] = None,
        troy_paid: bool = False,
        jaco_paid: bool = False,
        dan_paid: bool = True,
        notes: str = ""
    ):
        self.item_name = str(item_name).strip()
        self.price = quantize_currency(price)
        self.paid_by = paid_by
        self.notes = notes

        # Default 50/50 roundup split matching Excel formula: =ROUNDUP(Price/2, 0)
        default_half = round_up_excel(self.price / Decimal("2"), 0)

        self.troy_share = quantize_currency(troy_share if troy_share is not None else default_half)
        self.jaco_share = quantize_currency(jaco_share if jaco_share is not None else default_half)
        self.dan_share = quantize_currency(dan_share if dan_share is not None else default_half)

        self.troy_paid = bool(troy_paid)
        self.jaco_paid = bool(jaco_paid)
        self.dan_paid = bool(dan_paid)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_name": self.item_name,
            "price": str(self.price),
            "paid_by": self.paid_by,
            "troy_share": str(self.troy_share),
            "jaco_share": str(self.jaco_share),
            "dan_share": str(self.dan_share),
            "troy_paid": self.troy_paid,
            "jaco_paid": self.jaco_paid,
            "dan_paid": self.dan_paid,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PeerSettlementItem":
        return cls(
            item_name=data.get("item_name", ""),
            price=to_decimal(data.get("price", 0)),
            paid_by=data.get("paid_by", "Dan"),
            troy_share=to_decimal(data.get("troy_share")) if "troy_share" in data else None,
            jaco_share=to_decimal(data.get("jaco_share")) if "jaco_share" in data else None,
            dan_share=to_decimal(data.get("dan_share")) if "dan_share" in data else None,
            troy_paid=data.get("troy_paid", False),
            jaco_paid=data.get("jaco_paid", False),
            dan_paid=data.get("dan_paid", True),
            notes=data.get("notes", "")
        )


class FamilyRemittanceItem:
    """An item in the grocery / remittance ledger."""

    def __init__(self, item_name: str, count: Decimal = Decimal("1"), price: Decimal = ZERO, note: str = ""):
        self.item_name = str(item_name).strip()
        self.count = to_decimal(count)
        self.price = quantize_currency(price)
        self.note = note

    @property
    def subtotal(self) -> Decimal:
        return quantize_currency(self.count * self.price)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_name": self.item_name,
            "count": str(self.count),
            "price": str(self.price),
            "subtotal": str(self.subtotal),
            "note": self.note
        }


class SettlementEngine:
    """Coordinates peer settlements and family remittances."""

    def __init__(
        self,
        peer_items: Optional[List[PeerSettlementItem]] = None,
        grocery_items: Optional[List[FamilyRemittanceItem]] = None,
        deduction_items: Optional[List[FamilyRemittanceItem]] = None
    ):
        self.peer_items = peer_items or []
        self.grocery_items = grocery_items or []
        self.deduction_items = deduction_items or []

    def calculate_peer_settlements(self) -> Dict[str, Any]:
        """Summarize peer accounts receivable and payable."""
        troy_total_owed = ZERO
        troy_unpaid = ZERO
        jaco_total_owed = ZERO
        jaco_unpaid = ZERO
        dan_total_share = ZERO

        for it in self.peer_items:
            troy_total_owed += it.troy_share
            jaco_total_owed += it.jaco_share
            dan_total_share += it.dan_share

            if not it.troy_paid:
                troy_unpaid += it.troy_share
            if not it.jaco_paid:
                jaco_unpaid += it.jaco_share

        return {
            "items_count": len(self.peer_items),
            "troy": {
                "total_share": troy_total_owed,
                "unpaid_amount": troy_unpaid,
                "paid_amount": troy_total_owed - troy_unpaid
            },
            "jaco": {
                "total_share": jaco_total_owed,
                "unpaid_amount": jaco_unpaid,
                "paid_amount": jaco_total_owed - jaco_unpaid
            },
            "dan_total_share": dan_total_share,
            "total_receivable_unpaid": troy_unpaid + jaco_unpaid
        }

    def calculate_family_remittance(self) -> Dict[str, Any]:
        """
        Calculate net family remittance:
        TOTAL TO SEND = SUM(grocery_items) - SUM(deduction_items)
        """
        gross_items = sum((it.subtotal for it in self.grocery_items), ZERO)
        gross_deductions = sum((it.subtotal for it in self.deduction_items), ZERO)
        net_to_send = max(ZERO, gross_items - gross_deductions)

        return {
            "gross_items": gross_items,
            "gross_deductions": gross_deductions,
            "net_to_send": net_to_send,
            "item_count": len(self.grocery_items),
            "deduction_count": len(self.deduction_items)
        }

    def reconcile_executive_cash_flow(
        self,
        gross_salary: Decimal,
        tax_and_statutory_deductions: Decimal,
        daily_transpo: Decimal,
        daily_food: Decimal,
        monthly_working_days: int,
        my_utility_and_rent_bill: Decimal,
        additional_inflows: Decimal = ZERO,
        additional_outflows: Decimal = ZERO
    ) -> Dict[str, Any]:
        """
        Complete cash flow waterfall matching Excel 📊 Dashboard.
        """
        gross = quantize_currency(gross_salary)
        tax_stat = quantize_currency(tax_and_statutory_deductions)
        net_after_tax = max(ZERO, gross - tax_stat)

        # Everyday living expenses
        daily_living = quantize_currency(to_decimal(daily_transpo) + to_decimal(daily_food))
        monthly_living = quantize_currency(daily_living * Decimal(str(monthly_working_days)))
        biweekly_living = quantize_currency(monthly_living / Decimal("2"))

        money_after_living = max(ZERO, net_after_tax - monthly_living)

        # Utilities and rent share
        my_bills = quantize_currency(my_utility_and_rent_bill)
        money_after_utility = max(ZERO, net_after_tax - monthly_living - my_bills)

        # Additionals / Transfers
        inflows = quantize_currency(additional_inflows)
        outflows = quantize_currency(additional_outflows)
        money_after_additionals = money_after_utility + inflows - outflows

        # Family Remittances & Settlement obligations
        family_remit = self.calculate_family_remittance()["net_to_send"]
        peer_unpaid_receivable = self.calculate_peer_settlements()["total_receivable_unpaid"]

        final_discretionary_surplus = money_after_additionals - family_remit

        return {
            "gross_salary": gross,
            "tax_and_statutory_deductions": tax_stat,
            "net_after_tax": net_after_tax,
            "daily_living_rate": daily_living,
            "working_days": monthly_working_days,
            "monthly_living_expenses": monthly_living,
            "biweekly_living_expenses": biweekly_living,
            "my_utility_and_rent_bill": my_bills,
            "money_after_utility": money_after_utility,
            "additional_inflows": inflows,
            "additional_outflows": outflows,
            "money_after_additionals": money_after_additionals,
            "family_remittance_payable": family_remit,
            "peer_receivable_due": peer_unpaid_receivable,
            "final_discretionary_surplus": final_discretionary_surplus
        }


# ---------------------------------------------------------------------------
# High-Level Dataclasses & API Functions
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field


@dataclass
class CalumpangExpense:
    description: str
    total_amount: Decimal
    paid_by: str = "Dan"
    status: str = "pending"


@dataclass
class CalumpangSummary:
    total_expenses: Decimal
    dan_total_share: Decimal
    peer_total_share: Decimal
    net_peer_owes_dan: Decimal
    expenses_count: int
    items_breakdown: List[Dict[str, Any]]


@dataclass
class RemittanceLineItem:
    description: str
    amount: Decimal
    note: str = ""


@dataclass
class RemittanceSummary:
    gross_amount: Decimal
    total_deductions: Decimal
    net_transfer_amount: Decimal
    recipient_name: str
    items_count: int
    deductions_count: int


@dataclass
class ExecutiveCashFlow:
    total_inflow: Decimal
    total_outflow: Decimal
    net_surplus: Decimal
    savings_rate_pct: Decimal
    net_salary: Decimal
    living_budget: Decimal
    monthly_bills_share: Decimal
    peer_settlement_payable: Decimal
    groceries_remittance: Decimal
    raw_payload: Dict[str, Any]


def calculate_calumpang_settlement(
    expenses: List[CalumpangExpense],
    peer_name: str = "Troy"
) -> CalumpangSummary:
    """Calculate 50/50 peer settlement matching Excel =ROUNDUP(Price/2, 0)."""
    total_expenses = ZERO
    dan_total_share = ZERO
    peer_total_share = ZERO
    items_breakdown = []

    for exp in expenses:
        amt = to_decimal(exp.total_amount)
        if amt <= ZERO:
            continue
        total_expenses += amt
        dan_share = round_up_excel(amt / Decimal("2"), 0)
        peer_share = quantize_currency(amt - dan_share)
        dan_total_share += dan_share
        peer_total_share += peer_share

        items_breakdown.append({
            "description": exp.description,
            "total_amount": amt,
            "dan_share": dan_share,
            "peer_share": peer_share,
            "paid_by": exp.paid_by,
            "status": exp.status,
        })

    # If Dan paid for all, peer owes peer_total_share
    net_owes = peer_total_share

    return CalumpangSummary(
        total_expenses=quantize_currency(total_expenses),
        dan_total_share=quantize_currency(dan_total_share),
        peer_total_share=quantize_currency(peer_total_share),
        net_peer_owes_dan=quantize_currency(net_owes),
        expenses_count=len(expenses),
        items_breakdown=items_breakdown,
    )


def calculate_mama_groceries_remittance(
    items: List[RemittanceLineItem],
    deductions: List[RemittanceLineItem],
    recipient_name: str = "Mama"
) -> RemittanceSummary:
    """Calculate net transfer amount: =SUM(items) - SUM(deductions)."""
    gross = sum((to_decimal(it.amount) for it in items), ZERO)
    total_ded = sum((to_decimal(d.amount) for d in deductions), ZERO)
    net_transfer = max(ZERO, gross - total_ded)

    return RemittanceSummary(
        gross_amount=quantize_currency(gross),
        total_deductions=quantize_currency(total_ded),
        net_transfer_amount=quantize_currency(net_transfer),
        recipient_name=recipient_name,
        items_count=len(items),
        deductions_count=len(deductions),
    )


def generate_executive_cash_flow(
    net_salary: Decimal,
    other_income: Decimal = ZERO,
    monthly_bills_share: Decimal = ZERO,
    living_budget: Decimal = ZERO,
    peer_settlement_payable: Decimal = ZERO,
    groceries_remittance: Decimal = ZERO,
) -> ExecutiveCashFlow:
    """Reconcile executive cash flow waterfall and calculate net surplus and savings rate."""
    inflow = quantize_currency(to_decimal(net_salary) + to_decimal(other_income))
    outflow = quantize_currency(
        to_decimal(monthly_bills_share) +
        to_decimal(living_budget) +
        to_decimal(peer_settlement_payable) +
        to_decimal(groceries_remittance)
    )
    net_surplus = inflow - outflow

    if inflow > ZERO:
        savings_pct = quantize_currency((net_surplus / inflow) * Decimal("100"))
    else:
        savings_pct = ZERO

    return ExecutiveCashFlow(
        total_inflow=inflow,
        total_outflow=outflow,
        net_surplus=net_surplus,
        savings_rate_pct=savings_pct,
        net_salary=to_decimal(net_salary),
        living_budget=to_decimal(living_budget),
        monthly_bills_share=to_decimal(monthly_bills_share),
        peer_settlement_payable=to_decimal(peer_settlement_payable),
        groceries_remittance=to_decimal(groceries_remittance),
        raw_payload={
            "total_inflow": str(inflow),
            "total_outflow": str(outflow),
            "net_surplus": str(net_surplus),
            "savings_rate_pct": str(savings_pct)
        }
    )


# ---------------------------------------------------------------------------
# Calumpang Master Settlement Matrix (M1:U39) & DJ Gastos (A32:C59)
# ---------------------------------------------------------------------------

@dataclass
class MasterMatrixEntry:
    amount: Decimal
    is_paid: bool
    note: str


@dataclass
class MasterPersonSettlement:
    name: str
    items: List[MasterMatrixEntry]
    spotify_addon: Decimal = ZERO
    utilities_addon: Decimal = ZERO
    deductibles: List[Decimal] = field(default_factory=list)
    cash_items: List[Decimal] = field(default_factory=list)

    @property
    def subtotal_selected(self) -> Decimal:
        """=SUMIF(Paid_Flags, TRUE, Amounts)."""
        tot = sum((it.amount for it in self.items if it.is_paid), ZERO)
        if self.spotify_addon > ZERO:
            tot += self.spotify_addon
        if self.utilities_addon > ZERO:
            tot += self.utilities_addon
        return quantize_currency(tot)

    @property
    def total_bank_transfer(self) -> Decimal:
        """=ROUNDUP(Subtotal - Deductibles, 0)."""
        net = self.subtotal_selected - sum(self.deductibles, ZERO)
        return quantize_currency(round_up_excel(max(ZERO, net), 0))


    @property
    def total_cash(self) -> Decimal:
        """=SUM(Cash_Items)."""
        return quantize_currency(sum(self.cash_items, ZERO))


def calculate_master_settlement_matrix(
    troy_entries: Optional[List[Dict[str, Any]]] = None,
    jaco_entries: Optional[List[Dict[str, Any]]] = None,
    dan_entries: Optional[List[Dict[str, Any]]] = None,
    spotify_amount: Decimal = Decimal("57.40"),
    troy_utilities: Decimal = Decimal("3175.00"),
) -> Dict[str, Any]:
    """Calculate Master Matrix matching Calumpang M1:U39."""
    # Build Troy settlement
    troy_items = [
        MasterMatrixEntry(to_decimal(e.get("amount", 0)), bool(e.get("is_paid", True)), str(e.get("note", "")))
        for e in (troy_entries or [])
    ]
    troy = MasterPersonSettlement(
        name="Troy",
        items=troy_items,
        spotify_addon=to_decimal(spotify_amount),
        utilities_addon=to_decimal(troy_utilities),
    )

    # Build Jaco settlement
    jaco_items = [
        MasterMatrixEntry(to_decimal(e.get("amount", 0)), bool(e.get("is_paid", False)), str(e.get("note", "")))
        for e in (jaco_entries or [])
    ]
    jaco = MasterPersonSettlement(name="Jaco", items=jaco_items)

    # Build Dan settlement
    dan_items = [
        MasterMatrixEntry(to_decimal(e.get("amount", 0)), bool(e.get("is_paid", False)), str(e.get("note", "")))
        for e in (dan_entries or [])
    ]
    dan = MasterPersonSettlement(name="Dan", items=dan_items)

    return {
        "troy": {
            "subtotal": str(troy.subtotal_selected),
            "bank_transfer": str(troy.total_bank_transfer),
            "cash": str(troy.total_cash),
            "spotify": str(troy.spotify_addon),
            "utilities": str(troy.utilities_addon),
        },
        "jaco": {
            "subtotal": str(jaco.subtotal_selected),
            "bank_transfer": str(jaco.total_bank_transfer),
            "cash": str(jaco.total_cash),
        },
        "dan": {
            "subtotal": str(dan.subtotal_selected),
            "bank_transfer": str(dan.total_bank_transfer),
            "cash": str(dan.total_cash),
        },
    }
