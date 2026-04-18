from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from payment.domain import Address, CartItem


class TaxCalculator(ABC):
    """Strategy object — swap tax logic without changing OrderService."""

    @abstractmethod
    def tax_for_cart(self, items: List[CartItem], subtotal: float) -> float:
        pass


class StandardTaxCalculator(TaxCalculator):
    """
    Simple mixed-rate model: per-line category chooses a rate.
    `exempt` and `reduced` are common real-world buckets for teaching.
    """

    def __init__(
        self,
        default_rate: float = 0.0825,
        reduced_rate: float = 0.02,
    ):
        self._default_rate = default_rate
        self._reduced_rate = reduced_rate

    def tax_for_cart(self, items: List[CartItem], subtotal: float) -> float:
        _ = subtotal
        tax = 0.0
        for item in items:
            if item.tax_category == "exempt":
                continue
            rate = self._reduced_rate if item.tax_category == "reduced" else self._default_rate
            tax += item.subtotal * rate
        return round(tax, 2)


class NullTaxCalculator(TaxCalculator):
    """Use in tests or for tax-free jurisdictions."""

    def tax_for_cart(self, items: List[CartItem], subtotal: float) -> float:
        _ = items, subtotal
        return 0.0


class ShippingCalculator(ABC):
    @abstractmethod
    def shipping_for_cart(
        self,
        items: List[CartItem],
        subtotal: float,
        address: Optional[Address],
    ) -> float:
        pass


class WeightBasedShippingCalculator(ShippingCalculator):
    """Base fee plus per-kilogram surcharge on total cart weight."""

    def __init__(self, base_fee: float = 5.99, per_kg: float = 1.25, free_subtotal_at: float = 100.0):
        self._base = base_fee
        self._per_kg = per_kg
        self._free_subtotal_at = free_subtotal_at

    def shipping_for_cart(
        self,
        items: List[CartItem],
        subtotal: float,
        address: Optional[Address],
    ) -> float:
        if address is None:
            return 0.0
        if subtotal >= self._free_subtotal_at:
            return 0.0
        total_kg = sum(i.weight_kg * i.quantity for i in items)
        return round(self._base + total_kg * self._per_kg, 2)


class NullShippingCalculator(ShippingCalculator):
    def shipping_for_cart(
        self,
        items: List[CartItem],
        subtotal: float,
        address: Optional[Address],
    ) -> float:
        _ = items, subtotal, address
        return 0.0
