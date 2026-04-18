"""
Currency-safe decimal arithmetic for totals that must match human expectations.

**Why Decimals (not binary floats)**  
Binary ``float`` cannot represent most decimal fractions exactly; money calculations
with floats accumulate rounding error. :class:`decimal.Decimal` plus explicit
quantization avoids "0.1 + 0.2" style surprises in billing.

**Rounding**  
``money_quantize`` uses ``ROUND_HALF_EVEN`` (banker's rounding) to limit bias when
many half-cent adjustments occur. Regulatory regimes may mandate other rules — swap
the rounding mode deliberately if your jurisdiction requires it.

**Rates vs amounts**  
Use :func:`as_money` for currency amounts (2 decimal places) and :func:`as_rate` for
multipliers like sales-tax rates so values such as ``0.0825`` are not crushed to
``0.08``.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

_TWO_PLACES = Decimal("0.01")


def money_quantize(value: Decimal) -> Decimal:
    """Quantize ``value`` to two fractional digits using half-even rounding."""
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_EVEN)


def as_money(value: Decimal | float | str | int) -> Decimal:
    """Parse user or literal input into a currency-scaled, quantized ``Decimal``."""
    if isinstance(value, Decimal):
        return money_quantize(value)
    return money_quantize(Decimal(str(value)))


def as_rate(value: Decimal | float | str | int) -> Decimal:
    """
    Parse a percentage multiplier (e.g. ``0.0825``) without cent-style quantization.

    Tax and discount *rates* often need more than two decimal places; running them
    through :func:`as_money` would corrupt them.
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
