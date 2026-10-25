"""Tests for high-precision Decimal math and Excel rounding parity."""

from decimal import Decimal
import pytest
from app.core.decimal_utils import (
    to_decimal,
    round_currency,
    round_up_excel,
    round_half_up,
    quantize_decimal,
)


def test_to_decimal_various_inputs():
    assert to_decimal(100) == Decimal("100")
    assert to_decimal(100.5) == Decimal("100.5")
    assert to_decimal("250.75") == Decimal("250.75")
    assert to_decimal(" 1,234.50 ") == Decimal("1234.50")
    assert to_decimal(None) == Decimal("0.00")
    assert to_decimal("") == Decimal("0.00")
    assert to_decimal("invalid") == Decimal("0.00")


def test_round_currency():
    assert round_currency(Decimal("100.254")) == Decimal("100.25")
    assert round_currency(Decimal("100.255")) == Decimal("100.26")
    assert round_currency(Decimal("100.256")) == Decimal("100.26")


def test_round_up_excel_parity():
    """Verify Excel ROUNDUP(val, 0) behavior used in Calumpang 50/50 division."""
    # 45 / 2 = 22.5 -> 23
    assert round_up_excel(Decimal("45") / Decimal("2"), 0) == Decimal("23")
    # 111 / 2 = 55.5 -> 56
    assert round_up_excel(Decimal("111") / Decimal("2"), 0) == Decimal("56")
    # 227 / 2 = 113.5 -> 114
    assert round_up_excel(Decimal("227") / Decimal("2"), 0) == Decimal("114")
    # 1034 / 2 = 517.0 -> 517
    assert round_up_excel(Decimal("1034") / Decimal("2"), 0) == Decimal("517")
    # 500 / 2 = 250.0 -> 250
    assert round_up_excel(Decimal("500") / Decimal("2"), 0) == Decimal("250")
    # 0 -> 0
    assert round_up_excel(Decimal("0"), 0) == Decimal("0")
    # Decimal places
    assert round_up_excel(Decimal("12.341"), 2) == Decimal("12.35")
    assert round_up_excel(Decimal("12.340"), 2) == Decimal("12.34")


def test_quantize_decimal():
    assert quantize_decimal(Decimal("123.456"), places=2) == Decimal("123.46")
    assert quantize_decimal(Decimal("123.4"), places=2) == Decimal("123.40")
    assert quantize_decimal(Decimal("123.4"), places=4) == Decimal("123.4000")
