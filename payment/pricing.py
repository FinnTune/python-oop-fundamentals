"""
Pluggable tax and shipping **strategies** (Strategy pattern).

:class:`OrderService` depends on these abstractions so you can swap implementations
without editing checkout logic. All monetary outputs are :class:`~decimal.Decimal`
values compatible with :func:`payment.money.money_quantize`.

These calculators operate on trusted ``CartItem`` data from your domain layer; if
prices or weights came from a client, re-validate server-side before pricing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from payment.domain import Address, CartItem
from payment.money import as_money, as_rate, money_quantize


class TaxCalculator(ABC):
    """Strategy object — swap tax logic without changing OrderService."""

    @abstractmethod
    def tax_for_cart(self, items: list[CartItem], subtotal: Decimal) -> Decimal:
        pass


class StandardTaxCalculator(TaxCalculator):
    """
    Simple mixed-rate model: per-line category chooses a rate.
    `exempt` and `reduced` are common real-world buckets for teaching.
    """

    def __init__(
        self,
        default_rate: Decimal | float | str = Decimal("0.0825"),
        reduced_rate: Decimal | float | str = Decimal("0.02"),
    ):
        # Rates are not currency; do not run them through as_money (that rounds to cents).
        self._default_rate = as_rate(default_rate)
        self._reduced_rate = as_rate(reduced_rate)

    def tax_for_cart(self, items: list[CartItem], subtotal: Decimal) -> Decimal:
        _ = subtotal
        tax = Decimal("0.00")
        for item in items:
            if item.tax_category == "exempt":
                continue
            rate = self._reduced_rate if item.tax_category == "reduced" else self._default_rate
            tax += item.subtotal * rate
        return money_quantize(tax)


class NullTaxCalculator(TaxCalculator):
    """Use in tests or for tax-free jurisdictions."""

    def tax_for_cart(self, items: list[CartItem], subtotal: Decimal) -> Decimal:
        _ = items, subtotal
        return Decimal("0.00")


class ShippingCalculator(ABC):
    @abstractmethod
    def shipping_for_cart(
        self,
        items: list[CartItem],
        subtotal: Decimal,
        address: Address | None,
    ) -> Decimal:
        pass


class WeightBasedShippingCalculator(ShippingCalculator):
    """Base fee plus per-kilogram surcharge on total cart weight."""

    def __init__(
        self,
        base_fee: Decimal | float | str = Decimal("5.99"),
        per_kg: Decimal | float | str = Decimal("1.25"),
        free_subtotal_at: Decimal | float | str = Decimal("100.00"),
    ):
        self._base = as_money(base_fee)
        self._per_kg = as_money(per_kg)
        self._free_subtotal_at = as_money(free_subtotal_at)

    def shipping_for_cart(
        self,
        items: list[CartItem],
        subtotal: Decimal,
        address: Address | None,
    ) -> Decimal:
        if address is None:
            return Decimal("0.00")
        if subtotal >= self._free_subtotal_at:
            return Decimal("0.00")
        total_kg = Decimal(str(sum(i.weight_kg * i.quantity for i in items)))
        return money_quantize(self._base + total_kg * self._per_kg)


class NullShippingCalculator(ShippingCalculator):
    def shipping_for_cart(
        self,
        items: list[CartItem],
        subtotal: Decimal,
        address: Address | None,
    ) -> Decimal:
        _ = items, subtotal, address
        return Decimal("0.00")
