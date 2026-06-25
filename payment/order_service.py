"""
Order orchestration: pricing, payment capture, and in-memory order history.

**Design (OOP teaching)**  
Dependency-injected :class:`~payment.processor.PaymentProcessor`, pricing
strategies, inventory, and discounts; polymorphism on ``charge`` / ``refund``;
``reporter`` isolates IO.

**Security (demos vs production)**  
- ``place_order`` never passes ``payment_token`` to ``reporter`` — custom reporters
  must also avoid logging tokens or PII unless policy allows.
- Inputs are validated (currency, token bounds, metadata size, etc.) via
  :mod:`payment.security`.
- This package does **not** implement vault storage, TLS, or PCI scope reduction;
  treat it as learning code unless you harden it for real card data.

Stable import paths for teaching scripts: ``from payment.order_service import CartItem``.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

from payment.discounts import DiscountCalculator, NullDiscountCalculator
from payment.domain import Address, CartItem, cart_subtotal, generate_order_id, utc_now_iso
from payment.exceptions import PaymentFailedError
from payment.inventory import InventoryService, NullInventory
from payment.money import money_quantize
from payment.payment_context import PaymentContext
from payment.placed_order import OrderStatus, PlacedOrder
from payment.pricing import (
    NullShippingCalculator,
    NullTaxCalculator,
    ShippingCalculator,
    StandardTaxCalculator,
    TaxCalculator,
    WeightBasedShippingCalculator,
)
from payment.processor import PaymentProcessor
from payment.security import (
    normalize_currency,
    validate_customer_id,
    validate_idempotency_key,
    validate_order_id_query,
    validate_payment_metadata,
    validate_payment_token,
)

Reporter = Callable[[str], None]

__all__ = ["OrderService", "CartItem", "Address", "PlacedOrder", "order_service_for_tests"]


def _cart_from_line_items(line_items: list[dict]) -> list[CartItem]:
    """Rebuild cart lines from a stored order snapshot (for inventory restore)."""
    return [
        CartItem(
            name=str(li["name"]),
            price=li["unit_price"],
            quantity=int(li["quantity"]),
            sku=str(li.get("sku", "")),
            tax_category=str(li.get("tax_category", "general")),
            weight_kg=float(li.get("weight_kg", 0.0)),
        )
        for li in line_items
    ]


class OrderService:
    """
    Place orders (charge + persist snapshot) and refund by stack or by ``order_id``.

    **Concepts:** dependency injection, strategy objects, injectable ``reporter``.

    **Thread-safety:** not synchronized; use one instance per request/worker or add locks
    if you share history across threads.
    """

    def __init__(
        self,
        processor: PaymentProcessor,
        *,
        tax_calculator: TaxCalculator | None = None,
        shipping_calculator: ShippingCalculator | None = None,
        discount_calculator: DiscountCalculator | None = None,
        inventory: InventoryService | None = None,
        reporter: Reporter = print,
    ):
        self.processor = processor
        self._tax = tax_calculator or StandardTaxCalculator()
        self._shipping = shipping_calculator or WeightBasedShippingCalculator()
        self._discount = discount_calculator or NullDiscountCalculator()
        self._inventory = inventory or NullInventory()
        self._reporter = reporter
        self._order_history: list[PlacedOrder] = []

    def place_order(
        self,
        cart: list[CartItem],
        payment_token: str,
        *,
        shipping_address: Address | None = None,
        currency: str = "USD",
        idempotency_key: str = "",
        customer_id: str = "",
        payment_metadata: dict[str, str] | None = None,
        promo_code: str = "",
    ) -> PlacedOrder:
        """
        Compute totals, reserve stock, charge, and record a :class:`PlacedOrder`.

        **Secrets:** ``payment_token`` is only forwarded to ``processor`` — never log it.

        **Raises:**
            ``ValueError`` — invalid cart, token, currency, or metadata.
            :exc:`~payment.exceptions.InsufficientStockError` — not enough inventory.
            :exc:`~payment.exceptions.PaymentFailedError` — processor declined the charge.
        """
        if not cart:
            raise ValueError("Cannot place an order with an empty cart.")

        token = validate_payment_token(payment_token)
        currency_norm = normalize_currency(currency)
        idem = validate_idempotency_key(idempotency_key)
        cust = validate_customer_id(customer_id)
        meta = validate_payment_metadata(payment_metadata)
        promo = promo_code.strip()

        subtotal = cart_subtotal(cart)
        discount = self._discount.discount_for_cart(cart, subtotal, promo_code=promo)
        if discount > subtotal:
            discount = subtotal
        tax = self._tax.tax_for_cart(cart, subtotal)
        shipping = self._shipping.shipping_for_cart(cart, subtotal, shipping_address)
        total = money_quantize(subtotal - discount + tax + shipping)

        self._reporter(f"\n{'='*45}")
        self._reporter(f"  Placing order — {len(cart)} line(s)")
        self._reporter(f"    Subtotal:  ${subtotal:.2f} {currency_norm}")
        if discount > 0:
            self._reporter(f"    Discount:  -${discount:.2f}" + (f" ({promo})" if promo else ""))
        self._reporter(f"    Tax:       ${tax:.2f}")
        self._reporter(f"    Shipping:  ${shipping:.2f}")
        self._reporter(f"    Total:     ${total:.2f}")
        self._reporter(f"{'='*45}")

        self._inventory.reserve(cart)

        order_id = generate_order_id()
        context = PaymentContext(
            currency=currency_norm,
            idempotency_key=idem,
            order_id=order_id,
            customer_id=cust,
            metadata=meta,
        )
        try:
            success = self.processor.charge(amount=total, token=token, context=context)
        except Exception:
            self._inventory.restore(cart)
            raise

        if not success:
            self._inventory.restore(cart)
            raise PaymentFailedError("Payment failed. Order not placed.")

        transaction_id = self.processor.get_last_transaction_id()
        order = PlacedOrder(
            order_id=order_id,
            placed_at=utc_now_iso(),
            currency=currency_norm,
            line_items=[i.to_line_dict() for i in cart],
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            shipping=shipping,
            total=total,
            transaction_id=transaction_id,
            processor=type(self.processor).__name__,
            shipping_address=shipping_address.to_dict() if shipping_address else None,
            customer_id=cust,
            status=OrderStatus.PAID,
            promo_code=promo,
        )
        self._order_history.append(deepcopy(order))
        self._reporter(f"  Order confirmed! {order.order_id} — tx {transaction_id}\n")
        return order

    def get_order(self, order_id: str) -> PlacedOrder | None:
        """Return a deep copy of the newest matching order, or ``None``."""
        try:
            oid = validate_order_id_query(order_id)
        except (TypeError, ValueError):
            return None
        for o in reversed(self._order_history):
            if o.order_id == oid:
                return deepcopy(o)
        return None

    def orders_for_customer(self, customer_id: str) -> list[PlacedOrder]:
        """All orders (paid or refunded) for ``customer_id``, oldest first."""
        cust = validate_customer_id(customer_id)
        if not cust:
            return []
        return deepcopy([o for o in self._order_history if o.customer_id == cust])

    @property
    def paid_order_count(self) -> int:
        return sum(1 for o in self._order_history if o.status is OrderStatus.PAID)

    def refund_last_order(self) -> bool:
        """Refund the most recent **paid** order."""
        for idx in range(len(self._order_history) - 1, -1, -1):
            o = self._order_history[idx]
            if o.status is not OrderStatus.PAID:
                continue
            return self._refund_at_index(idx)
        self._reporter("No paid orders to refund.")
        return False

    def refund_order(self, order_id: str) -> bool:
        """
        Refund a specific **paid** order by business ``order_id`` (newest match wins).

        Invalid ``order_id`` strings return ``False`` without raising.
        """
        try:
            oid = validate_order_id_query(order_id)
        except (TypeError, ValueError):
            self._reporter("Invalid order_id for refund.")
            return False

        for idx in range(len(self._order_history) - 1, -1, -1):
            o = self._order_history[idx]
            if o.order_id == oid and o.status is OrderStatus.PAID:
                return self._refund_at_index(idx)
        self._reporter(f"No paid order found for id {oid!r}.")
        return False

    def _refund_at_index(self, idx: int) -> bool:
        o = self._order_history[idx]
        self._reporter(f"\nRefunding order {o.order_id} ({o.transaction_id})...")
        success = self.processor.refund(o.transaction_id)
        if success:
            o.status = OrderStatus.REFUNDED
            self._inventory.restore(_cart_from_line_items(o.line_items))
        return success

    @property
    def order_count(self) -> int:
        return len(self._order_history)

    def order_history_snapshot(self) -> list[PlacedOrder]:
        """Deep copy of all orders — safe to mutate for UI without touching history."""
        return deepcopy(self._order_history)


def order_service_for_tests(
    processor: PaymentProcessor,
    *,
    reporter: Reporter | None = None,
) -> OrderService:
    """
    Build an :class:`OrderService` with null tax/shipping/discount/inventory for tests.

    Default reporter is silent so tests do not spam stdout.
    """
    rep: Reporter = reporter if reporter is not None else (lambda _msg: None)
    return OrderService(
        processor=processor,
        tax_calculator=NullTaxCalculator(),
        shipping_calculator=NullShippingCalculator(),
        discount_calculator=NullDiscountCalculator(),
        inventory=NullInventory(),
        reporter=rep,
    )
