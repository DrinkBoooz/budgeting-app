"""Apartment Expenditures, Dentist Tracker, and Expedition Splitting Engine.

Implements all 6 sub-ledgers from Dan BudgetingV3.xlsx 'Apt Expenses':
1. House / IKEA Expenditures (=(Count*Price)-Discount)
2. Application Expenses (Drug Test, Neuro Psych, NBI, TOR, Medical)
3. Dentist & Braces Tracker (Billed items - Deductibles, Progress Bar)
4. Maple Grove SnR Food
5. Ate Joy & Lorraine Mini-Ledgers
6. Noella & James Expedition (=ROUNDUP(Price*Count/Divisor, 0))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .decimal_utils import to_decimal, quantize_currency, round_up_excel, ZERO


@dataclass
class ExpenditureItem:
    """An expenditure item with count, price, discount, and note."""
    item: str
    count: Decimal = Decimal("1")
    price: Decimal = ZERO
    discount: Decimal = ZERO
    note: str = ""

    @property
    def total_price(self) -> Decimal:
        """Calculate total price: (count * price) - discount."""
        c = to_decimal(self.count)
        p = to_decimal(self.price)
        d = to_decimal(self.discount)
        return max(ZERO, quantize_currency((c * p) - d))


@dataclass
class SubtotalItem:
    """A standard item with count, price, and note."""
    label: str
    count: Decimal = Decimal("1")
    price: Decimal = ZERO
    note: str = ""

    @property
    def subtotal(self) -> Decimal:
        c = to_decimal(self.count)
        p = to_decimal(self.price)
        return quantize_currency(c * p)


@dataclass
class ExpeditionItem:
    """An expedition shared expenditure with dynamic divisor."""
    label: str
    count: Decimal = Decimal("1")
    price: Decimal = ZERO
    divisor: Decimal = Decimal("1")
    note: str = ""

    @property
    def subtotal(self) -> Decimal:
        """=IFERROR(ROUNDUP(Price*Count/Divisor, 0), 0)"""
        c = to_decimal(self.count)
        p = to_decimal(self.price)
        div = to_decimal(self.divisor)
        if div <= ZERO:
            return ZERO
        return quantize_currency(round_up_excel((p * c) / div, 0))



@dataclass
class DentistSummary:
    total_billed: Decimal
    total_paid: Decimal
    pure_dentist_remaining: Decimal
    combined_grand_total: Decimal
    payments_made_count: int
    progress_pct: Decimal
    progress_bar: str
    billed_items: List[Dict[str, Any]]
    deductible_items: List[Dict[str, Any]]


def calculate_house_expenditures(items: List[ExpenditureItem]) -> Dict[str, Any]:
    """Calculate House / IKEA expenditures matching Apt Expenses A1:G22."""
    grand_total = ZERO
    rows = []
    for it in items:
        tot = it.total_price
        grand_total += tot
        rows.append({
            "item": it.item,
            "count": str(it.count),
            "price": str(it.price),
            "discount": str(it.discount),
            "total_price": str(tot),
            "note": it.note,
        })
    return {
        "grand_total": str(quantize_currency(grand_total)),
        "items": rows,
    }


def calculate_application_expenses(items: List[SubtotalItem]) -> Dict[str, Any]:
    """Calculate Application expenses matching Apt Expenses A33:E42."""
    subtotal = ZERO
    rows = []
    for it in items:
        sub = it.subtotal
        subtotal += sub
        rows.append({
            "label": it.label,
            "count": str(it.count),
            "price": str(it.price),
            "subtotal": str(sub),
            "note": it.note,
        })
    return {
        "subtotal": str(quantize_currency(subtotal)),
        "items": rows,
    }


def calculate_dentist_tracker(
    billed: List[SubtotalItem],
    deductibles: List[SubtotalItem],
    app_expenses_subtotal: Decimal = Decimal("2420.00"),
) -> DentistSummary:
    """Calculate Dentist tracker, deductibles, combined balance, and progress bar."""
    total_billed = sum((it.subtotal for it in billed), ZERO)
    # Deductibles are negative in Excel or positive amounts paid
    total_deductible_abs = sum((abs(it.subtotal) for it in deductibles if it.subtotal != ZERO), ZERO)
    
    pure_remaining = max(ZERO, total_billed - total_deductible_abs)
    # Workbook D67 = D42 (App 2420) + D54 (Dentist 37500) + D65 (Deductibles -8000) = 31920
    combined = app_expenses_subtotal + total_billed - total_deductible_abs

    # Progress: B14 / A14
    if total_billed > ZERO:
        ratio = (total_deductible_abs / total_billed)
        pct = quantize_currency(ratio * Decimal("100"))
        # REPT("█", ROUND((B14/A14)*10, 0)) & REPT("░", 10 - ROUND(...))
        blocks_filled = int(round(float(ratio) * 10))
        blocks_filled = max(0, min(10, blocks_filled))
        progress_bar = ("█" * blocks_filled) + ("░" * (10 - blocks_filled))
    else:
        pct = ZERO
        progress_bar = "░" * 10

    payments_count = len([d for d in deductibles if d.subtotal != ZERO])

    return DentistSummary(
        total_billed=quantize_currency(total_billed),
        total_paid=quantize_currency(total_deductible_abs),
        pure_dentist_remaining=quantize_currency(pure_remaining),
        combined_grand_total=quantize_currency(combined),
        payments_made_count=payments_count,
        progress_pct=pct,
        progress_bar=progress_bar,
        billed_items=[{"label": b.label, "count": str(b.count), "price": str(b.price), "subtotal": str(b.subtotal), "note": b.note} for b in billed],
        deductible_items=[{"label": d.label, "count": str(d.count), "price": str(d.price), "subtotal": str(d.subtotal), "note": d.note} for d in deductibles],
    )


def calculate_expedition_expenses(items: List[ExpeditionItem]) -> Dict[str, Any]:
    """Calculate Noella & James Expedition expenses with N-person divisors."""
    subtotal = ZERO
    rows = []
    for it in items:
        sub = it.subtotal
        subtotal += sub
        rows.append({
            "label": it.label,
            "count": str(it.count),
            "price": str(it.price),
            "divisor": str(it.divisor),
            "subtotal": str(sub),
            "note": it.note,
        })
    return {
        "subtotal": str(quantize_currency(subtotal)),
        "items": rows,
    }
