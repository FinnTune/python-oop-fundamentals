from dataclasses import dataclass
from typing import List
from payment.processor import PaymentProcessor
# We import ONLY the interface — never StripePayment or PayPalPayment directly.
# This is the key principle: depend on abstractions, not implementations.


@dataclass
class CartItem:
    """A single item in a shopping cart."""
    name: str
    price: float
    quantity: int

    @property
    def subtotal(self) -> float:
        return self.price * self.quantity


class OrderService:
    """
    Handles placing and refunding orders.

    KEY CONCEPTS:
    - Dependency Injection : receives its processor from outside, never creates one
    - Polymorphism         : calls .charge() without knowing which processor it has
    - self                 : each OrderService instance tracks its own order history
    """

    def __init__(self, processor: PaymentProcessor):
        # DEPENDENCY INJECTION — constructor style.
        # The caller decides which processor to use and passes it in.
        # OrderService stores it and uses it, but never creates it.
        self.processor = processor
        self._order_history: List[dict] = []

    def place_order(self, cart: List[CartItem], payment_token: str) -> dict:
        if not cart:
            raise ValueError("Cannot place an order with an empty cart.")

        total = sum(item.subtotal for item in cart)

        print(f"\n{'='*45}")
        print(f"  Placing order — {len(cart)} item(s), total: ${total:.2f}")
        print(f"{'='*45}")

        # POLYMORPHISM — this line works for Stripe, PayPal, or any future processor.
        # Python looks at what self.processor actually IS and calls the right .charge().
        success = self.processor.charge(amount=total, token=payment_token)

        if not success:
            raise RuntimeError("Payment failed. Order not placed.")

        transaction_id = self.processor.get_last_transaction_id()
        order = {
            "items": [{"name": i.name, "subtotal": i.subtotal} for i in cart],
            "total": total,
            "transaction_id": transaction_id,
            "processor": type(self.processor).__name__,
        }
        self._order_history.append(order)
        print(f"  Order confirmed! Transaction: {transaction_id}\n")
        return order

    def refund_last_order(self) -> bool:
        if not self._order_history:
            print("No orders to refund.")
            return False

        last = self._order_history[-1]
        print(f"\nRefunding order {last['transaction_id']}...")
        success = self.processor.refund(last["transaction_id"])
        if success:
            self._order_history.pop()
        return success

    @property
    def order_count(self) -> int:
        return len(self._order_history)
