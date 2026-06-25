"""
Promotional discount strategies (Strategy pattern — same idea as tax/shipping).

Discounts reduce the merchandise subtotal before tax and shipping are added to
the grand total. Real systems differ on whether tax applies pre- or post-discount;
this teaching model keeps tax/shipping calculators unchanged for clarity.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from payment.domain import CartItem
from payment.money import as_rate, money_quantize


class DiscountCalculator(ABC):
    @abstractmethod
    def discount_for_cart(
        self,
        items: list[CartItem],
        subtotal: Decimal,
        *,
        promo_code: str = "",
    ) -> Decimal:
        pass


class NullDiscountCalculator(DiscountCalculator):
    """No discount — default for tests and baseline checkout."""

    def discount_for_cart(
        self,
        items: list[CartItem],
        subtotal: Decimal,
        *,
        promo_code: str = "",
    ) -> Decimal:
        _ = items, subtotal, promo_code
        return Decimal("0.00")


class PercentageDiscountCalculator(DiscountCalculator):
    """Flat percentage off the entire subtotal (ignores ``promo_code``)."""

    def __init__(self, rate: Decimal | float | str) -> None:
        self._rate = as_rate(rate)

    def discount_for_cart(
        self,
        items: list[CartItem],
        subtotal: Decimal,
        *,
        promo_code: str = "",
    ) -> Decimal:
        _ = items, promo_code
        return money_quantize(subtotal * self._rate)


class PromoCodeDiscountCalculator(DiscountCalculator):
    """
    Map promo codes to percentage rates, e.g. ``{"SAVE10": "0.10"}``.

    Unknown or blank codes yield zero discount.
    """

    def __init__(self, codes: dict[str, Decimal | float | str]) -> None:
        self._codes = {k.strip().upper(): as_rate(v) for k, v in codes.items()}

    def discount_for_cart(
        self,
        items: list[CartItem],
        subtotal: Decimal,
        *,
        promo_code: str = "",
    ) -> Decimal:
        _ = items
        code = promo_code.strip().upper()
        if not code or code not in self._codes:
            return Decimal("0.00")
        return money_quantize(subtotal * self._codes[code])
