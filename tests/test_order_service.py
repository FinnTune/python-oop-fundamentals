"""Tests for OrderService, end-to-end order flow, and polymorphism."""

from __future__ import annotations

import unittest
from decimal import Decimal

from payment.discounts import PromoCodeDiscountCalculator
from payment.domain import Address, CartItem, cart_subtotal
from payment.exceptions import InsufficientStockError, PaymentFailedError
from payment.inventory import InMemoryInventory
from payment.order_service import OrderService, order_service_for_tests
from payment.paypal_payment import PayPalPayment
from payment.placed_order import OrderStatus, PlacedOrder
from payment.pricing import (
    NullShippingCalculator,
    NullTaxCalculator,
    StandardTaxCalculator,
    WeightBasedShippingCalculator,
)
from payment.stripe_payment import StripePayment

from tests.fakes import FakePaymentProcessor


def make_cart() -> list[CartItem]:
    """Sample cart — subtotal $79.97 (49.99 + 14.99 * 2)."""
    return [
        CartItem(name="Python Book", price=49.99, quantity=1),
        CartItem(name="USB-C Cable", price=14.99, quantity=2),
    ]


class TestOrderServiceFactory(unittest.TestCase):
    def test_order_service_for_tests_charges_cart_subtotal_only(self):
        fake = FakePaymentProcessor()
        svc = order_service_for_tests(fake)
        cart = make_cart()
        expected = cart_subtotal(cart)
        svc.place_order(cart, "tok_test")
        self.assertEqual(fake.charges[0], expected)


class TestPlaceOrder(unittest.TestCase):
    def setUp(self):
        self.fake = FakePaymentProcessor()
        self.service = order_service_for_tests(self.fake)
        self.cart = make_cart()

    def test_to_dict_has_expected_keys(self):
        result = self.service.place_order(self.cart, "tok_test")
        d = result.to_dict()
        for key in (
            "total",
            "transaction_id",
            "processor",
            "line_items",
            "subtotal",
            "discount",
            "tax",
            "shipping",
            "order_id",
            "placed_at",
            "currency",
            "shipping_address",
            "status",
            "customer_id",
        ):
            self.assertIn(key, d)

    def test_returns_placed_order_dataclass(self):
        result = self.service.place_order(self.cart, "tok_test")
        self.assertIsInstance(result, PlacedOrder)

    def test_correct_total_charged(self):
        self.service.place_order(self.cart, "tok_test")
        self.assertEqual(self.fake.charges[0], Decimal("79.97"))

    def test_passes_payment_token_to_processor(self):
        self.service.place_order(self.cart, "my_secret_tok")
        self.assertEqual(self.fake.tokens, ["my_secret_tok"])

    def test_passes_payment_context_with_order_id(self):
        o = self.service.place_order(self.cart, "tok")
        self.assertIsNotNone(self.fake.contexts[0])
        ctx = self.fake.contexts[0]
        assert ctx is not None
        self.assertEqual(ctx.order_id, o.order_id)
        self.assertEqual(ctx.currency, "USD")

    def test_idempotency_key_and_customer_id_in_context(self):
        self.service.place_order(
            self.cart,
            "tok",
            idempotency_key="idem-abc",
            customer_id="cust-9",
            payment_metadata={"risk": "low"},
        )
        ctx = self.fake.contexts[0]
        assert ctx is not None
        self.assertEqual(ctx.idempotency_key, "idem-abc")
        self.assertEqual(ctx.customer_id, "cust-9")
        self.assertEqual(ctx.metadata["risk"], "low")

    def test_order_count_increments(self):
        self.assertEqual(self.service.order_count, 0)
        self.service.place_order(self.cart, "tok_1")
        self.service.place_order(self.cart, "tok_2")
        self.assertEqual(self.service.order_count, 2)

    def test_empty_cart_raises(self):
        with self.assertRaises(ValueError):
            self.service.place_order([], "tok_test")

    def test_invalid_currency_raises(self):
        with self.assertRaises(ValueError):
            self.service.place_order(self.cart, "tok_test", currency="US")

    def test_invalid_payment_token_raises(self):
        with self.assertRaises(ValueError):
            self.service.place_order(self.cart, "\x00bad")

    def test_failed_payment_raises_and_does_not_record_order(self):
        service = order_service_for_tests(FakePaymentProcessor(should_succeed=False))
        with self.assertRaises(PaymentFailedError):
            service.place_order(self.cart, "tok_test")
        self.assertEqual(service.order_count, 0)

    def test_promo_discount_reduces_charge(self):
        svc = OrderService(
            processor=self.fake,
            tax_calculator=NullTaxCalculator(),
            shipping_calculator=NullShippingCalculator(),
            discount_calculator=PromoCodeDiscountCalculator({"SAVE10": "0.10"}),
            reporter=lambda _m: None,
        )
        svc.place_order(self.cart, "tok", promo_code="SAVE10")
        self.assertEqual(self.fake.charges[0], Decimal("71.97"))

    def test_insufficient_stock_raises_before_charge(self):
        inv = InMemoryInventory({"PYTHON-BOOK": 0})
        cart = [CartItem("Python Book", 49.99, 1, sku="PYTHON-BOOK")]
        svc = OrderService(processor=self.fake, inventory=inv, reporter=lambda _m: None)
        with self.assertRaises(InsufficientStockError):
            svc.place_order(cart, "tok")
        self.assertEqual(self.fake.charges, [])

    def test_get_order_and_customer_history(self):
        self.service.place_order(self.cart, "tok", customer_id="cust-42")
        o = self.service.get_order(self.service.order_history_snapshot()[0].order_id)
        self.assertIsNotNone(o)
        assert o is not None
        self.assertEqual(o.customer_id, "cust-42")
        hist = self.service.orders_for_customer("cust-42")
        self.assertEqual(len(hist), 1)

    def test_transaction_id_in_result(self):
        result = self.service.place_order(self.cart, "tok_test")
        self.assertEqual(result.transaction_id, self.fake.get_last_transaction_id())

    def test_currency_defaults_to_usd_and_is_echoed(self):
        r = self.service.place_order(self.cart, "tok")
        self.assertEqual(r.currency, "USD")

    def test_custom_currency(self):
        r = self.service.place_order(self.cart, "tok", currency="EUR")
        self.assertEqual(r.currency, "EUR")

    def test_shipping_address_none_in_payload(self):
        r = self.service.place_order(self.cart, "tok")
        self.assertIsNone(r.shipping_address)

    def test_shipping_address_round_trips_as_dict(self):
        addr = Address("10 Oak", "Austin", "TX", "73301", country="US", line2="Ste 2")
        r = self.service.place_order(self.cart, "tok", shipping_address=addr)
        self.assertEqual(r.shipping_address, addr.to_dict())

    def test_line_items_match_cart_lines(self):
        r = self.service.place_order(self.cart, "tok")
        self.assertEqual(len(r.line_items), len(self.cart))
        self.assertEqual(r.line_items[0]["name"], "Python Book")

    def test_tax_and_shipping_applied_when_configured(self):
        cart = [
            CartItem("A", 50.0, 1, tax_category="general"),
            CartItem("B", 10.0, 1, tax_category="exempt"),
        ]
        addr = Address("1 Main", "Town", "CA", "90001")
        svc = OrderService(
            processor=self.fake,
            tax_calculator=StandardTaxCalculator(default_rate=0.10, reduced_rate=0.05),
            shipping_calculator=WeightBasedShippingCalculator(
                base_fee=5.0, per_kg=2.0, free_subtotal_at=9999.0
            ),
            reporter=lambda _m: None,
        )
        svc.place_order(cart, "tok_x", shipping_address=addr)
        self.assertEqual(self.fake.charges[0], Decimal("70.00"))

    def test_default_tax_and_shipping_strategies_integration(self):
        cart = [
            CartItem("Book", 34.99, 1, tax_category="reduced", weight_kg=0.0),
            CartItem("Cable", 10.0, 1, tax_category="general", weight_kg=0.0),
        ]
        addr = Address("1", "C", "R", "P")
        svc = OrderService(self.fake, reporter=lambda _m: None)
        svc.place_order(cart, "tok", shipping_address=addr)
        self.assertEqual(self.fake.charges[0], Decimal("52.50"))

    def test_mutating_returned_order_does_not_corrupt_history(self):
        result = self.service.place_order(self.cart, "tok_1")
        result.total = Decimal("-1.00")
        self.assertEqual(self.service.order_history_snapshot()[0].total, Decimal("79.97"))

    def test_history_snapshot_is_deep_copy(self):
        self.service.place_order(self.cart, "tok_1")
        snap = self.service.order_history_snapshot()
        snap[0].total = Decimal("-1.00")
        self.assertEqual(self.service.order_history_snapshot()[0].total, Decimal("79.97"))


class TestRefund(unittest.TestCase):
    def setUp(self):
        self.fake = FakePaymentProcessor()
        self.service = order_service_for_tests(self.fake)
        self.cart = make_cart()

    def test_refund_returns_true(self):
        self.service.place_order(self.cart, "tok_test")
        self.assertTrue(self.service.refund_last_order())

    def test_refund_marks_refunded_and_keeps_history(self):
        self.service.place_order(self.cart, "tok_test")
        self.assertTrue(self.service.refund_last_order())
        self.assertEqual(self.service.order_count, 1)
        self.assertEqual(self.service.paid_order_count, 0)
        snap = self.service.order_history_snapshot()[0]
        self.assertEqual(snap.status, OrderStatus.REFUNDED)

    def test_refund_with_no_orders(self):
        self.assertFalse(self.service.refund_last_order())

    def test_correct_id_refunded(self):
        self.service.place_order(self.cart, "tok_test")
        expected = self.fake.get_last_transaction_id()
        self.service.refund_last_order()
        self.assertIn(expected, self.fake.refunds)

    def test_refund_failure_leaves_order_in_history(self):
        bad_refund = FakePaymentProcessor(should_succeed=True, refund_succeeds=False)
        svc = order_service_for_tests(bad_refund)
        svc.place_order(self.cart, "tok")
        self.assertFalse(svc.refund_last_order())
        self.assertEqual(svc.order_count, 1)
        self.assertEqual(bad_refund.refunds, [])

    def test_refund_stack_is_lifo(self):
        self.service.place_order(self.cart, "tok_1")
        self.service.place_order(self.cart, "tok_2")
        first_tx = self.service.order_history_snapshot()[0].transaction_id
        self.service.refund_last_order()
        self.assertEqual(self.service.order_count, 2)
        self.assertEqual(self.service.paid_order_count, 1)
        self.assertEqual(self.service.order_history_snapshot()[0].transaction_id, first_tx)
        self.assertEqual(self.service.order_history_snapshot()[1].status, OrderStatus.REFUNDED)

    def test_refund_order_by_id_marks_that_order(self):
        a = self.service.place_order(self.cart, "tok_a")
        b = self.service.place_order(self.cart, "tok_b")
        self.assertTrue(self.service.refund_order(a.order_id))
        self.assertEqual(self.service.order_count, 2)
        self.assertEqual(self.service.paid_order_count, 1)
        self.assertEqual(self.service.get_order(a.order_id).status, OrderStatus.REFUNDED)
        remaining = self.service.get_order(b.order_id)
        assert remaining is not None
        self.assertEqual(remaining.status, OrderStatus.PAID)

    def test_refund_order_unknown_id_returns_false(self):
        self.service.place_order(self.cart, "tok")
        self.assertFalse(self.service.refund_order("ORD-NOPE"))

    def test_refund_order_malformed_id_returns_false(self):
        self.assertFalse(self.service.refund_order("\x00"))


class TestPolymorphism(unittest.TestCase):
    """Same OrderService code works with any processor — that is polymorphism."""

    def setUp(self):
        self.cart = make_cart()

    def test_stripe(self):
        result = order_service_for_tests(StripePayment("sk_test_abc")).place_order(
            self.cart, "tok_visa"
        )
        self.assertEqual(result.processor, "StripePayment")
        self.assertEqual(result.total, Decimal("79.97"))

    def test_paypal(self):
        result = order_service_for_tests(PayPalPayment("pp_id", "pp_sec")).place_order(
            self.cart, "tok_pp"
        )
        self.assertEqual(result.processor, "PayPalPayment")
        self.assertEqual(result.total, Decimal("79.97"))

    def test_fake(self):
        result = order_service_for_tests(FakePaymentProcessor()).place_order(self.cart, "tok_fake")
        self.assertEqual(result.processor, "FakePaymentProcessor")

    def test_two_instances_independent(self):
        a = order_service_for_tests(StripePayment("sk_test_aaa"))
        b = order_service_for_tests(StripePayment("sk_test_bbb"))
        a.place_order(self.cart, "tok_1")
        a.place_order(self.cart, "tok_2")
        b.place_order(self.cart, "tok_3")
        self.assertEqual(a.order_count, 2)
        self.assertEqual(b.order_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
