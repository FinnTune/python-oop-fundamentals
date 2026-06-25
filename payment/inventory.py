"""
Stock reservation — another injectable strategy used before charging.

**Teaching point:** ``OrderService`` does not import a global inventory singleton.
You inject ``InventoryService`` so tests can use ``NullInventory`` and demos can
wire ``InMemoryInventory`` with a dict of SKU → quantity.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from payment.domain import CartItem
from payment.exceptions import InsufficientStockError


class InventoryService(ABC):
    @abstractmethod
    def reserve(self, cart: list[CartItem]) -> None:
        """Decrement stock for each SKU in ``cart`` or raise :exc:`InsufficientStockError`."""

    @abstractmethod
    def restore(self, cart: list[CartItem]) -> None:
        """Return units to stock (failed payment or refund)."""


class NullInventory(InventoryService):
    """Always succeeds — use in unit tests and when stock is out of scope."""

    def reserve(self, cart: list[CartItem]) -> None:
        _ = cart

    def restore(self, cart: list[CartItem]) -> None:
        _ = cart


class InMemoryInventory(InventoryService):
    """
    SKU-keyed stock ledger held in a mutable dict (not thread-safe).

    Lines without a ``sku`` skip inventory checks (useful for ad-hoc cart items).
    """

    def __init__(self, stock: dict[str, int]) -> None:
        self._stock = {k: max(0, v) for k, v in stock.items()}

    def available(self, sku: str) -> int:
        return self._stock.get(sku, 0)

    def reserve(self, cart: list[CartItem]) -> None:
        needs: dict[str, int] = {}
        for item in cart:
            if not item.sku:
                continue
            needs[item.sku] = needs.get(item.sku, 0) + item.quantity

        for sku, qty in needs.items():
            have = self._stock.get(sku, 0)
            if have < qty:
                raise InsufficientStockError(sku, qty, have)

        for sku, qty in needs.items():
            self._stock[sku] -= qty

    def restore(self, cart: list[CartItem]) -> None:
        for item in cart:
            if item.sku:
                self._stock[item.sku] = self._stock.get(item.sku, 0) + item.quantity
