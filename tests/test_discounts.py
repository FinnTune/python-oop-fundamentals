"""Tests for payment.discounts."""

from __future__ import annotations

import unittest
from decimal import Decimal

from payment.discounts import (
    NullDiscountCalculator,
    PercentageDiscountCalculator,
    PromoCodeDiscountCalculator,
)
from payment.domain import CartItem


class TestDiscountCalculators(unittest.TestCase):
    def setUp(self):
        self.cart = [CartItem("A", 100, 1)]
        self.subtotal = Decimal("100.00")

    def test_null_is_zero(self):
        self.assertEqual(
            NullDiscountCalculator().discount_for_cart(self.cart, self.subtotal),
            Decimal("0.00"),
        )

    def test_percentage(self):
        calc = PercentageDiscountCalculator("0.15")
        self.assertEqual(calc.discount_for_cart(self.cart, self.subtotal), Decimal("15.00"))

    def test_promo_code_match(self):
        calc = PromoCodeDiscountCalculator({"SAVE10": "0.10"})
        d = calc.discount_for_cart(self.cart, self.subtotal, promo_code="save10")
        self.assertEqual(d, Decimal("10.00"))

    def test_promo_code_unknown(self):
        calc = PromoCodeDiscountCalculator({"SAVE10": "0.10"})
        self.assertEqual(
            calc.discount_for_cart(self.cart, self.subtotal, promo_code="NOPE"),
            Decimal("0.00"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
