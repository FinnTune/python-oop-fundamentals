"""Domain-specific errors for checkout — clearer than bare ``ValueError`` / ``RuntimeError``."""

from __future__ import annotations


class PaymentError(Exception):
    """Base class for payment-domain failures."""


class PaymentFailedError(PaymentError):
    """The processor declined or failed to capture funds."""


class InsufficientStockError(PaymentError):
    """A cart line requests more units than inventory holds."""

    def __init__(self, sku: str, requested: int, available: int) -> None:
        self.sku = sku
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for {sku!r}: requested {requested}, available {available}."
        )


class OrderNotFoundError(PaymentError):
    """No matching order exists for the given identifier."""

    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        super().__init__(f"Order not found: {order_id!r}.")
