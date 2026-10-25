"""Unit tests for Pajah Toga rental calculations."""

from decimal import Decimal
import pytest
from app.core.pajah_engine import (
    DEFAULT_OWNERS,
    PajahOwnerRecord,
    calculate_pajah_summary,
)


def test_pajah_owners_and_prices():
    """Verify 8 owners, prices (₱500/₱650 + ₱100 = ₱600/₱750, Sum = ₱1,350)."""
    assert len(DEFAULT_OWNERS) == 8
    owner = PajahOwnerRecord(
        owner_name="Dan",
        owned=1,
        price_pictorial=Decimal("500.00"),
        price_grad=Decimal("650.00"),
        dan_addon=Decimal("100.00"),
        active_rentals=2,
    )
    assert owner.pictorial_fprice == Decimal("600.00")
    assert owner.grad_fprice == Decimal("750.00")
    assert owner.sum_package_price == Decimal("1350.00")
    assert owner.total_revenue == Decimal("2700.00")


def test_pajah_summary_defaults():
    """Verify default summary totals."""
    summary = calculate_pajah_summary()
    assert summary["total_owned"] == 8
    # Dan and Rj have 1 active rental each by default
    assert summary["total_rentals"] == 2
    # 8 * 1,350 = 10,800.00
    assert summary["total_potential_sum"] == "10800.00"
    # 2 * 1,350 = 2,700.00
    assert summary["total_active_revenue"] == "2700.00"
    assert len(summary["owners"]) == 8
