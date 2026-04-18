from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from payment.domain import Address, CartItem, cart_subtotal, generate_order_id, utc_now_iso
from payment.pricing import (
    NullShippingCalculator,
    NullTaxCalculator,
    ShippingCalculator,
    StandardTaxCalculator,
    TaxCalculator,
    WeightBasedShippingCalculator,
)
from payment.processor import PaymentProcessor
# We import ONLY the processor interface — never StripePayment or PayPalPayment directly.
# This is the key principle: depend on abstractions, not implementations.

# Stable import paths for teaching scripts: `from payment.order_service import CartItem`.
__all__ = ["OrderService", "CartItem", "Address", "order_service_for_tests"]


class OrderService:
    """
    Handles placing and refunding orders.

    KEY CONCEPTS:
    - Dependency Injection : receives its processor from outside, never creates one
    - Polymorphism         : calls .charge() without knowing which processor it has
    - self                 : each OrderService instance tracks its own order history
    - Strategy objects     : tax and shipping are pluggable calculators (more DI)
    """

    def __init__(
        self,
        processor: PaymentProcessor,
        *,
        tax_calculator: Optional[TaxCalculator] = None,
        shipping_calculator: Optional[ShippingCalculator] = None,
    ):
        self.processor = processor
        self._tax = tax_calculator or StandardTaxCalculator()
        self._shipping = shipping_calculator or WeightBasedShippingCalculator()
        self._order_history: List[Dict[str, Any]] = []

    def place_order(
        self,
        cart: List[CartItem],
        payment_token: str,
        *,
        shipping_address: Optional[Address] = None,
        currency: str = "USD",
    ) -> Dict[str, Any]:
        if not cart:
            raise ValueError("Cannot place an order with an empty cart.")

        subtotal = cart_subtotal(cart)
        tax = self._tax.tax_for_cart(cart, subtotal)
        shipping = self._shipping.shipping_for_cart(cart, subtotal, shipping_address)
        total = round(subtotal + tax + shipping, 2)

        print(f"\n{'='*45}")
        print(f"  Placing order — {len(cart)} line(s)")
        print(f"    Subtotal:  ${subtotal:.2f} {currency}")
        print(f"    Tax:       ${tax:.2f}")
        print(f"    Shipping:  ${shipping:.2f}")
        print(f"    Total:     ${total:.2f}")
        print(f"{'='*45}")

        success = self.processor.charge(amount=total, token=payment_token)

        if not success:
            raise RuntimeError("Payment failed. Order not placed.")

        transaction_id = self.processor.get_last_transaction_id()
        order: Dict[str, Any] = {
            "order_id": generate_order_id(),
            "placed_at": utc_now_iso(),
            "currency": currency,
            "line_items": [i.to_line_dict() for i in cart],
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "total": total,
            "transaction_id": transaction_id,
            "processor": type(self.processor).__name__,
            "shipping_address": shipping_address.to_dict() if shipping_address else None,
        }
        self._order_history.append(deepcopy(order))
        print(f"  Order confirmed! {order['order_id']} — tx {transaction_id}\n")
        return order

    def refund_last_order(self) -> bool:
        if not self._order_history:
            print("No orders to refund.")
            return False

        last = self._order_history[-1]
        print(f"\nRefunding order {last['order_id']} ({last['transaction_id']})...")
        success = self.processor.refund(last["transaction_id"])
        if success:
            self._order_history.pop()
        return success

    @property
    def order_count(self) -> int:
        return len(self._order_history)

    def order_history_snapshot(self) -> List[Dict[str, Any]]:
        """Immutable-style view for demos/tests — avoids accidental mutation of history."""
        return deepcopy(self._order_history)


def order_service_for_tests(processor: PaymentProcessor) -> OrderService:
    """Factory with zero tax/shipping so unit tests stay deterministic and simple."""
    return OrderService(
        processor=processor,
        tax_calculator=NullTaxCalculator(),
        shipping_calculator=NullShippingCalculator(),
    )
