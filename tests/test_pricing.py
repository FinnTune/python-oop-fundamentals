"""Tests for tax and shipping strategy objects."""

from __future__ import annotations

import unittest

from payment.domain import Address, CartItem
from payment.pricing import (
    NullShippingCalculator,
    NullTaxCalculator,
    ShippingCalculator,
    StandardTaxCalculator,
    TaxCalculator,
    WeightBasedShippingCalculator,
)


class TestStandardTaxCalculator(unittest.TestCase):
    def setUp(self):
        self.calc = StandardTaxCalculator(default_rate=0.10, reduced_rate=0.05)

    def test_general_category_uses_default_rate(self):
        items = [CartItem("A", 100.0, 1, tax_category="general")]
        self.assertAlmostEqual(self.calc.tax_for_cart(items, 100.0), 10.0, places=2)

    def test_reduced_category_uses_reduced_rate(self):
        items = [CartItem("Book", 100.0, 1, tax_category="reduced")]
        self.assertAlmostEqual(self.calc.tax_for_cart(items, 100.0), 5.0, places=2)

    def test_exempt_category_pays_no_tax(self):
        items = [CartItem("Food", 100.0, 1, tax_category="exempt")]
        self.assertAlmostEqual(self.calc.tax_for_cart(items, 100.0), 0.0, places=2)

    def test_unknown_category_falls_back_to_default_rate(self):
        items = [CartItem("Odd", 50.0, 1, tax_category="luxury-unknown")]
        self.assertAlmostEqual(self.calc.tax_for_cart(items, 50.0), 5.0, places=2)

    def test_mixed_lines(self):
        items = [
            CartItem("G", 50.0, 1, tax_category="general"),
            CartItem("R", 50.0, 1, tax_category="reduced"),
            CartItem("E", 50.0, 1, tax_category="exempt"),
        ]
        # 50*0.10 + 50*0.05 + 0 = 7.50
        self.assertAlmostEqual(self.calc.tax_for_cart(items, 150.0), 7.50, places=2)

    def test_subtotal_argument_is_ignored(self):
        items = [CartItem("A", 10.0, 1)]
        self.assertAlmostEqual(self.calc.tax_for_cart(items, 9999.0), 1.0, places=2)


class TestNullTaxCalculator(unittest.TestCase):
    def test_always_zero(self):
        items = [CartItem("A", 100.0, 1, tax_category="general")]
        self.assertEqual(NullTaxCalculator().tax_for_cart(items, 100.0), 0.0)


class TestWeightBasedShippingCalculator(unittest.TestCase):
    def setUp(self):
        self.addr = Address("1 Ship", "Town", "CA", "90001")

    def test_no_address_returns_zero(self):
        calc = WeightBasedShippingCalculator(base_fee=9.0, per_kg=9.0, free_subtotal_at=0.0)
        items = [CartItem("W", 10.0, 1, weight_kg=99.0)]
        self.assertEqual(calc.shipping_for_cart(items, 10.0, None), 0.0)

    def test_free_shipping_at_or_above_threshold(self):
        calc = WeightBasedShippingCalculator(base_fee=5.0, per_kg=1.0, free_subtotal_at=100.0)
        items = [CartItem("Big", 100.0, 1, weight_kg=50.0)]
        self.assertEqual(calc.shipping_for_cart(items, 100.0, self.addr), 0.0)

    def test_just_below_threshold_charges_shipping(self):
        calc = WeightBasedShippingCalculator(base_fee=4.0, per_kg=2.0, free_subtotal_at=100.0)
        items = [CartItem("Almost", 99.99, 1, weight_kg=1.0)]
        # 4 + 1*2 = 6
        self.assertAlmostEqual(calc.shipping_for_cart(items, 99.99, self.addr), 6.0, places=2)

    def test_weight_scales_with_quantity(self):
        calc = WeightBasedShippingCalculator(base_fee=0.0, per_kg=3.0, free_subtotal_at=9999.0)
        items = [CartItem("Brick", 5.0, 4, weight_kg=0.5)]
        # total kg = 4 * 0.5 = 2 → 2 * 3 = 6
        self.assertAlmostEqual(calc.shipping_for_cart(items, 20.0, self.addr), 6.0, places=2)

    def test_rounds_to_two_decimals(self):
        calc = WeightBasedShippingCalculator(base_fee=1.0, per_kg=0.333, free_subtotal_at=9999.0)
        items = [CartItem("X", 1.0, 1, weight_kg=1.0)]
        self.assertAlmostEqual(calc.shipping_for_cart(items, 1.0, self.addr), 1.33, places=2)


class TestNullShippingCalculator(unittest.TestCase):
    def test_always_zero_even_with_address(self):
        addr = Address("1", "C", "R", "P")
        items = [CartItem("A", 10.0, 1)]
        self.assertEqual(NullShippingCalculator().shipping_for_cart(items, 10.0, addr), 0.0)


class TestAbstractPricingClasses(unittest.TestCase):
    def test_cannot_instantiate_tax_calculator_interface(self):
        with self.assertRaises(TypeError):
            TaxCalculator()  # type: ignore[misc]

    def test_cannot_instantiate_shipping_calculator_interface(self):
        with self.assertRaises(TypeError):
            ShippingCalculator()  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main(verbosity=2)
