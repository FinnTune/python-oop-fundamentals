"""
Successful checkout snapshot — the in-memory record produced after a captured charge.

**Serialization:** :meth:`PlacedOrder.to_dict` converts ``Decimal`` amounts to Python
``float`` for convenience. That loses exact decimal representation; for accounting
exports prefer strings (e.g. ``format(decimal, 'f')``) or a schema that preserves
decimals.

**Privacy:** ``shipping_address`` and ``customer_id`` may be PII. Apply retention
limits, access controls, and encryption at rest when you persist these records.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


class OrderStatus(str, Enum):
    """Lifecycle state for an order stored in :class:`~payment.order_service.OrderService`."""

    PAID = "paid"
    REFUNDED = "refunded"


@dataclass
class PlacedOrder:
    """
    Snapshot of one order (mutate only if you own the instance).

    ``processor`` stores the concrete class name for debugging only.
    """

    order_id: str
    placed_at: str
    currency: str
    line_items: list[dict[str, Any]]
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal
    transaction_id: str
    processor: str
    shipping_address: dict[str, str] | None
    customer_id: str = ""
    status: OrderStatus = OrderStatus.PAID
    promo_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Plain dict with floats for money — convenient for scripts and naive JSON."""
        return {
            "order_id": self.order_id,
            "placed_at": self.placed_at,
            "currency": self.currency,
            "line_items": deepcopy(self.line_items),
            "subtotal": float(self.subtotal),
            "discount": float(self.discount),
            "tax": float(self.tax),
            "shipping": float(self.shipping),
            "total": float(self.total),
            "transaction_id": self.transaction_id,
            "processor": self.processor,
            "shipping_address": deepcopy(self.shipping_address)
            if self.shipping_address is not None
            else None,
            "customer_id": self.customer_id,
            "status": self.status.value,
            "promo_code": self.promo_code,
        }
