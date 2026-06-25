"""
Product catalog — reusable definitions that become :class:`~payment.domain.CartItem` lines.

Separating **catalog data** from **cart instances** mirrors how shops store master
product records separately from per-session basket lines (price snapshots, quantity).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from payment.domain import CartItem, PriceInput


@dataclass(frozen=True)
class Product:
    """Read-only product master record."""

    sku: str
    name: str
    unit_price: PriceInput
    tax_category: str = "general"
    weight_kg: float = 0.0
    description: str = ""

    def to_cart_item(self, quantity: int = 1) -> CartItem:
        return CartItem(
            name=self.name,
            price=self.unit_price,
            quantity=quantity,
            sku=self.sku,
            tax_category=self.tax_category,
            weight_kg=self.weight_kg,
        )


# Sample catalog aligned with ``main.py`` demo SKUs.
SAMPLE_CATALOG: dict[str, Product] = {
    "BOOK-CC-001": Product(
        sku="BOOK-CC-001",
        name="Clean Code (book)",
        unit_price=Decimal("34.99"),
        tax_category="reduced",
        weight_kg=0.6,
        description="Robert C. Martin — software craftsmanship classic.",
    ),
    "KB-MECH-87": Product(
        sku="KB-MECH-87",
        name="Mechanical Keyboard",
        unit_price=Decimal("89.99"),
        tax_category="general",
        weight_kg=1.1,
    ),
    "HUB-USBC-7N1": Product(
        sku="HUB-USBC-7N1",
        name="USB-C Hub",
        unit_price=Decimal("24.99"),
        tax_category="general",
        weight_kg=0.2,
    ),
    "NB-A5-LIN": Product(
        sku="NB-A5-LIN",
        name="Notebook (A5)",
        unit_price=Decimal("19.99"),
        tax_category="general",
        weight_kg=0.3,
    ),
    "MON-27-4K": Product(
        sku="MON-27-4K",
        name="Monitor",
        unit_price=Decimal("399.99"),
        tax_category="general",
        weight_kg=6.4,
    ),
}


def build_cart_from_catalog(items: list[tuple[str, int]]) -> list[CartItem]:
    """
    Build a cart from ``(sku, quantity)`` pairs using :data:`SAMPLE_CATALOG`.

    Raises:
        KeyError: unknown SKU.
    """
    return [SAMPLE_CATALOG[sku].to_cart_item(qty) for sku, qty in items]
