import unittest
from typing import List

from payment.processor import PaymentProcessor
from payment.order_service import OrderService, CartItem
from payment.stripe_payment import StripePayment
from payment.paypal_payment import PayPalPayment


class FakePaymentProcessor(PaymentProcessor):
    """
    A test double — implements the interface but records calls instead of
    hitting any real API. This is the direct payoff of dependency injection:
    you can inject a fake and test behaviour without network calls.
    """
    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed
        self.charges: List[float] = []
        self.refunds: List[str] = []
        self._last_transaction_id = ""

    def charge(self, amount: float, token: str) -> bool:
        if self.should_succeed:
            self._last_transaction_id = f"fake_ch_{len(self.charges) + 1}"
            self.charges.append(amount)
        return self.should_succeed

    def refund(self, charge_id: str) -> bool:
        if self.should_succeed:
            self.refunds.append(charge_id)
        return self.should_succeed

    def get_last_transaction_id(self) -> str:
        return self._last_transaction_id


def make_cart() -> List[CartItem]:
    """Sample cart — total $79.97 (49.99 + 14.99 * 2)."""
    return [
        CartItem(name="Python Book", price=49.99, quantity=1),
        CartItem(name="USB-C Cable", price=14.99, quantity=2),
    ]


class TestCartItem(unittest.TestCase):
    def test_subtotal_single(self):
        self.assertAlmostEqual(CartItem("Book", 29.99, 1).subtotal, 29.99, places=2)

    def test_subtotal_multiple(self):
        self.assertAlmostEqual(CartItem("Cable", 14.99, 3).subtotal, 44.97, places=2)


class TestPlaceOrder(unittest.TestCase):
    def setUp(self):
        self.fake = FakePaymentProcessor()
        self.service = OrderService(processor=self.fake)
        self.cart = make_cart()

    def test_returns_dict_with_expected_keys(self):
        result = self.service.place_order(self.cart, "tok_test")
        for key in ("total", "transaction_id", "processor", "items"):
            self.assertIn(key, result)

    def test_correct_total_charged(self):
        self.service.place_order(self.cart, "tok_test")
        self.assertAlmostEqual(self.fake.charges[0], 79.97, places=2)

    def test_order_count_increments(self):
        self.assertEqual(self.service.order_count, 0)
        self.service.place_order(self.cart, "tok_1")
        self.service.place_order(self.cart, "tok_2")
        self.assertEqual(self.service.order_count, 2)

    def test_empty_cart_raises(self):
        with self.assertRaises(ValueError):
            self.service.place_order([], "tok_test")

    def test_failed_payment_raises(self):
        service = OrderService(processor=FakePaymentProcessor(should_succeed=False))
        with self.assertRaises(RuntimeError):
            service.place_order(self.cart, "tok_test")

    def test_transaction_id_in_result(self):
        result = self.service.place_order(self.cart, "tok_test")
        self.assertEqual(result["transaction_id"], self.fake.get_last_transaction_id())


class TestRefund(unittest.TestCase):
    def setUp(self):
        self.fake = FakePaymentProcessor()
        self.service = OrderService(processor=self.fake)
        self.cart = make_cart()

    def test_refund_returns_true(self):
        self.service.place_order(self.cart, "tok_test")
        self.assertTrue(self.service.refund_last_order())

    def test_refund_decrements_count(self):
        self.service.place_order(self.cart, "tok_test")
        self.service.refund_last_order()
        self.assertEqual(self.service.order_count, 0)

    def test_refund_with_no_orders(self):
        self.assertFalse(self.service.refund_last_order())

    def test_correct_id_refunded(self):
        self.service.place_order(self.cart, "tok_test")
        expected = self.fake.get_last_transaction_id()
        self.service.refund_last_order()
        self.assertIn(expected, self.fake.refunds)


class TestPolymorphism(unittest.TestCase):
    """Same OrderService code works with any processor — that is polymorphism."""

    def setUp(self):
        self.cart = make_cart()

    def test_stripe(self):
        result = OrderService(StripePayment("sk_test_abc")).place_order(self.cart, "tok_visa")
        self.assertEqual(result["processor"], "StripePayment")
        self.assertAlmostEqual(result["total"], 79.97, places=2)

    def test_paypal(self):
        result = OrderService(PayPalPayment("pp_id", "pp_sec")).place_order(self.cart, "tok_pp")
        self.assertEqual(result["processor"], "PayPalPayment")
        self.assertAlmostEqual(result["total"], 79.97, places=2)

    def test_fake(self):
        result = OrderService(FakePaymentProcessor()).place_order(self.cart, "tok_fake")
        self.assertEqual(result["processor"], "FakePaymentProcessor")

    def test_two_instances_independent(self):
        """self keeps each instance's history separate."""
        a = OrderService(StripePayment("sk_test_aaa"))
        b = OrderService(StripePayment("sk_test_bbb"))
        a.place_order(self.cart, "tok_1")
        a.place_order(self.cart, "tok_2")
        b.place_order(self.cart, "tok_3")
        self.assertEqual(a.order_count, 2)
        self.assertEqual(b.order_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
