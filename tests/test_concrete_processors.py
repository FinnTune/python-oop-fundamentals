"""Smoke tests for concrete PaymentProcessor implementations."""

from __future__ import annotations

import unittest

from payment.paypal_payment import PayPalPayment
from payment.stripe_payment import StripePayment


class TestStripePayment(unittest.TestCase):
    def setUp(self):
        self.p = StripePayment("sk_test_123456789")

    def test_charge_updates_last_transaction_id(self):
        self.assertEqual(self.p.get_last_transaction_id(), "")
        self.assertTrue(self.p.charge(12.34, "tok_visa_4242"))
        self.assertTrue(self.p.get_last_transaction_id().startswith("ch_stripe_"))

    def test_refund_returns_true(self):
        self.assertTrue(self.p.charge(1.0, "tok_a"))
        self.assertTrue(self.p.refund(self.p.get_last_transaction_id()))


class TestPayPalPayment(unittest.TestCase):
    def setUp(self):
        self.p = PayPalPayment("client_id_xx", "secret_yy")

    def test_charge_updates_last_transaction_id(self):
        self.assertEqual(self.p.get_last_transaction_id(), "")
        self.assertTrue(self.p.charge(9.99, "tok_paypal_abc"))
        tid = self.p.get_last_transaction_id()
        self.assertTrue(tid.startswith("PAYID-"))

    def test_refund_returns_true(self):
        self.assertTrue(self.p.charge(2.0, "tok_b"))
        self.assertTrue(self.p.refund(self.p.get_last_transaction_id()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
