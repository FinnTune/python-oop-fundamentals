"""Tests for the payment processor interface contract."""

from __future__ import annotations

import unittest

from payment.processor import PaymentProcessor


class TestPaymentProcessorInterface(unittest.TestCase):
    def test_cannot_instantiate_abstract_class(self):
        with self.assertRaises(TypeError) as ctx:
            PaymentProcessor()  # type: ignore[misc]
        msg = str(ctx.exception).lower()
        self.assertIn("abstract", msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
