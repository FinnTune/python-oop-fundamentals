from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from payment.money import as_money, money_quantize
from payment.security import validate_address_fields, validate_cart_line_label

PriceInput = Decimal | float | str | int


def generate_order_id() -> str:
    """
    Create a unique opaque order identifier (UUID-based).

    Uses :mod:`uuid` (version 4) suitable for public correlation IDs. This does not
    by itself authenticate callers — always authorize refund/actions server-side.
    """
    return f"ORD-{uuid.uuid4().hex[:12].upper()}"


def utc_now_iso() -> str:
    """UTC timestamp with second resolution, for audit trails."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Address:
    """
    Minimal shipping address for quoting shipping and persisting on ``PlacedOrder``.

    **Privacy:** Treat as PII. Do not log full addresses at info level in production;
    prefer structured logging with redaction or hashed identifiers where policy allows.

    Fields are length-bounded via :func:`payment.security.validate_address_fields`
    to reduce accidental huge payloads.
    """

    line1: str
    city: str
    region: str
    postal_code: str
    country: str = "US"
    line2: str = ""

    def __post_init__(self) -> None:
        validate_address_fields(
            self.line1,
            self.city,
            self.region,
            self.postal_code,
            country=self.country,
            line2=self.line2,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "line1": self.line1,
            "line2": self.line2,
            "city": self.city,
            "region": self.region,
            "postal_code": self.postal_code,
            "country": self.country,
        }


class CartItem:
    """
    One sellable line on an order — unit ``price`` is stored as :class:`~decimal.Decimal`.

    **Validation:** Quantity, non-negative price, bounded string fields, and sane
    ``weight_kg`` (finite, non-negative) help reject garbage input early.

    **Security note:** ``name`` / ``sku`` are not HTML-escaped here; if you render them
    in a browser, apply your framework's escaping to prevent XSS.
    """

    __slots__ = ("name", "_price", "quantity", "sku", "tax_category", "weight_kg")

    def __init__(
        self,
        name: str,
        price: PriceInput,
        quantity: int,
        sku: str = "",
        tax_category: str = "general",
        weight_kg: float = 0.0,
    ) -> None:
        if quantity < 1:
            raise ValueError("Cart line quantity must be at least 1.")
        if math.isnan(weight_kg) or math.isinf(weight_kg) or weight_kg < 0:
            raise ValueError("weight_kg must be a finite, non-negative number.")
        coerced = as_money(price)
        if coerced < Decimal("0"):
            raise ValueError("Unit price cannot be negative.")
        validate_cart_line_label(name=name, sku=sku, tax_category=tax_category)
        self.name = name
        self._price = coerced
        self.quantity = quantity
        self.sku = sku
        self.tax_category = tax_category
        self.weight_kg = weight_kg

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def subtotal(self) -> Decimal:
        return money_quantize(self.price * Decimal(self.quantity))

    def to_line_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "name": self.name,
            "unit_price": float(self.price),
            "quantity": self.quantity,
            "tax_category": self.tax_category,
            "weight_kg": self.weight_kg,
            "subtotal": float(self.subtotal),
        }

    def __repr__(self) -> str:
        return (
            f"CartItem(name={self.name!r}, price={self.price}, quantity={self.quantity}, "
            f"sku={self.sku!r}, tax_category={self.tax_category!r}, weight_kg={self.weight_kg})"
        )


def cart_subtotal(items: list[CartItem]) -> Decimal:
    """Sum of line subtotals, quantized to currency precision."""
    if not items:
        return Decimal("0.00")
    return money_quantize(sum((i.subtotal for i in items), start=Decimal("0")))
