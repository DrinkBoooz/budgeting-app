"""Graduation & Pictorial Toga ("Pajah") Rental Tracking Engine.

Implements Dan BudgetingV3.xlsx 'Pajah Rent' sheet logic:
- 8 Toga Owners: Dan, Christian, Harvin, Jiom, Josh, Noella, Rj, Troy
- Price calculation:
  * Price Pictorial (₱500) + Dan add-on (₱100) = Pictorial Fprice (₱600)
  * Price Grad (₱650) + Dan add-on (₱100) = Grad Fprice (₱750)
  * Sum Package = Pictorial Fprice + Grad Fprice (₱1,350)
- Tracks active rentals count and revenue per owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .decimal_utils import to_decimal, quantize_currency, ZERO

DEFAULT_OWNERS = [
    "Dan",
    "Christian",
    "Harvin",
    "Jiom",
    "Josh",
    "Noella",
    "Rj",
    "Troy",
]


@dataclass
class PajahOwnerRecord:
    owner_name: str
    owned: int = 1
    price_pictorial: Decimal = Decimal("500.00")
    price_grad: Decimal = Decimal("650.00")
    dan_addon: Decimal = Decimal("100.00")
    active_rentals: int = 0

    @property
    def pictorial_fprice(self) -> Decimal:
        return quantize_currency(to_decimal(self.price_pictorial) + to_decimal(self.dan_addon))

    @property
    def grad_fprice(self) -> Decimal:
        return quantize_currency(to_decimal(self.price_grad) + to_decimal(self.dan_addon))

    @property
    def sum_package_price(self) -> Decimal:
        return quantize_currency(self.pictorial_fprice + self.grad_fprice)

    @property
    def total_revenue(self) -> Decimal:
        return quantize_currency(self.sum_package_price * Decimal(str(self.active_rentals)))


def calculate_pajah_summary(records: Optional[List[PajahOwnerRecord]] = None) -> Dict[str, Any]:
    """Calculate Pajah rental totals across all owners."""
    owners = records or [
        PajahOwnerRecord(owner_name=name, active_rentals=1 if name in ["Dan", "Rj"] else 0)
        for name in DEFAULT_OWNERS
    ]

    total_owned = sum(o.owned for o in owners)
    total_rentals = sum(o.active_rentals for o in owners)
    total_potential_sum = sum((o.sum_package_price for o in owners), ZERO)
    total_active_revenue = sum((o.total_revenue for o in owners), ZERO)

    rows = []
    for o in owners:
        rows.append({
            "owner_name": o.owner_name,
            "owned": o.owned,
            "price_pictorial": str(o.price_pictorial),
            "price_grad": str(o.price_grad),
            "dan_addon": str(o.dan_addon),
            "pictorial_fprice": str(o.pictorial_fprice),
            "grad_fprice": str(o.grad_fprice),
            "sum": str(o.sum_package_price),
            "active_rentals": o.active_rentals,
            "total_revenue": str(o.total_revenue),
        })

    return {
        "total_owned": total_owned,
        "total_rentals": total_rentals,
        "total_potential_sum": str(quantize_currency(total_potential_sum)),
        "total_active_revenue": str(quantize_currency(total_active_revenue)),
        "owners": rows,
    }
