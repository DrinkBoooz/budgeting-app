"""
Decimal utility functions for high-precision currency, tax, and budget math.
Ensures zero IEEE 754 floating point drift and exact Excel parity.
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN
from typing import Union, Any

ZERO = Decimal("0")
CENT = Decimal("0.01")
PESO = Decimal("1")

def to_decimal(val: Any) -> Decimal:
    """Convert any number, string, or Decimal to Decimal safely."""
    if val is None or val == "":
        return ZERO
    if isinstance(val, Decimal):
        return val
    try:
        clean_str = str(val).strip().replace(",", "").replace("₱", "").replace("$", "")
        return Decimal(clean_str)
    except Exception:
        return ZERO

def quantize_currency(val: Any) -> Decimal:
    """Quantize to 2 decimal places using standard ROUND_HALF_UP."""
    d = to_decimal(val)
    return d.quantize(CENT, rounding=ROUND_HALF_UP)

def round_excel(val: Any, places: int = 2) -> Decimal:
    """Equivalent to Excel's ROUND(val, places) using ROUND_HALF_UP."""
    d = to_decimal(val)
    target = Decimal("10") ** (-places) if places > 0 else Decimal("10") ** abs(places)
    if places == 0:
        return d.quantize(PESO, rounding=ROUND_HALF_UP)
    return d.quantize(target, rounding=ROUND_HALF_UP)

def round_up_excel(val: Any, places: int = 0) -> Decimal:
    """Equivalent to Excel's ROUNDUP(val, places) using ROUND_UP."""
    d = to_decimal(val)
    if places == 0:
        return d.quantize(PESO, rounding=ROUND_UP)
    target = Decimal("10") ** (-places)
    return d.quantize(target, rounding=ROUND_UP)

def round_down_excel(val: Any, places: int = 0) -> Decimal:
    """Equivalent to Excel's ROUNDDOWN(val, places) using ROUND_DOWN."""
    d = to_decimal(val)
    if places == 0:
        return d.quantize(PESO, rounding=ROUND_DOWN)
    target = Decimal("10") ** (-places)
    return d.quantize(target, rounding=ROUND_DOWN)


# Common aliases
round_currency = quantize_currency
round_half_up = round_excel


def quantize_decimal(val: Any, places: int = 2) -> Decimal:
    """Quantize to arbitrary decimal places."""
    return round_excel(val, places=places)
