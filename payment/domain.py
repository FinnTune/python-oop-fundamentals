from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


def generate_order_id() -> str:
    return f"ORD-{uuid.uuid4().hex[:12].upper()}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Address:
    """Minimal shipping address — enough to quote delivery and audit an order."""

    line1: str
    city: str
    region: str
    postal_code: str
    country: str = "US"
    line2: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "line1": self.line1,
            "line2": self.line2,
            "city": self.city,
            "region": self.region,
            "postal_code": self.postal_code,
            "country": self.country,
        }


@dataclass
class CartItem:
    """One sellable line on an order — inventory and pricing hooks stay explicit."""

    name: str
    price: float
    quantity: int
    sku: str = ""
    tax_category: str = "general"
    weight_kg: float = 0.0

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("Cart line quantity must be at least 1.")
        if self.price < 0:
            raise ValueError("Unit price cannot be negative.")

    @property
    def subtotal(self) -> float:
        return round(self.price * self.quantity, 2)

    def to_line_dict(self) -> Dict[str, Any]:
        return {
            "sku": self.sku,
            "name": self.name,
            "unit_price": self.price,
            "quantity": self.quantity,
            "tax_category": self.tax_category,
            "weight_kg": self.weight_kg,
            "subtotal": self.subtotal,
        }


def cart_subtotal(items: List[CartItem]) -> float:
    return round(sum(i.subtotal for i in items), 2)
