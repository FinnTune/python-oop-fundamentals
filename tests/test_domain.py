"""Tests for payment.domain — addresses, cart lines, and small helpers."""

from __future__ import annotations

import re
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime
from decimal import Decimal

from payment.domain import Address, CartItem, cart_subtotal, generate_order_id, utc_now_iso


class TestAddress(unittest.TestCase):
    def test_to_dict_contains_all_fields(self):
        addr = Address(
            line1="742 Evergreen Terrace",
            line2="Unit B",
            city="Springfield",
            region="IL",
            postal_code="62704",
            country="US",
        )
        d = addr.to_dict()
        self.assertEqual(d["line1"], "742 Evergreen Terrace")
        self.assertEqual(d["line2"], "Unit B")
        self.assertEqual(d["city"], "Springfield")
        self.assertEqual(d["region"], "IL")
        self.assertEqual(d["postal_code"], "62704")
        self.assertEqual(d["country"], "US")

    def test_default_country_and_empty_line2(self):
        addr = Address("1 Main", "Town", "CA", "90001")
        self.assertEqual(addr.country, "US")
        self.assertEqual(addr.line2, "")
        d = addr.to_dict()
        self.assertEqual(d["line2"], "")

    def test_frozen_dataclass_cannot_assign(self):
        addr = Address("1", "C", "R", "P")
        with self.assertRaises(FrozenInstanceError):
            addr.city = "Other"  # type: ignore[misc]

    def test_address_field_length_limit(self):
        with self.assertRaises(ValueError):
            Address("x" * 300, "C", "R", "P")


class TestCartItem(unittest.TestCase):
    def test_subtotal_single(self):
        self.assertEqual(CartItem("Book", 29.99, 1).subtotal, Decimal("29.99"))

    def test_subtotal_multiple(self):
        self.assertEqual(CartItem("Cable", 14.99, 3).subtotal, Decimal("44.97"))

    def test_line_dict_includes_sku_and_tax_category(self):
        line = CartItem("Mug", 12.0, 2, sku="MUG-01", tax_category="reduced")
        d = line.to_line_dict()
        self.assertEqual(d["sku"], "MUG-01")
        self.assertEqual(d["tax_category"], "reduced")
        self.assertAlmostEqual(d["subtotal"], 24.0, places=2)

    def test_invalid_quantity_raises(self):
        with self.assertRaises(ValueError):
            CartItem("X", 1.0, 0)

    def test_negative_price_raises(self):
        with self.assertRaises(ValueError):
            CartItem("X", -1.0, 1)

    def test_invalid_weight_raises(self):
        with self.assertRaises(ValueError):
            CartItem("X", 1.0, 1, weight_kg=-0.1)
        with self.assertRaises(ValueError):
            CartItem("X", 1.0, 1, weight_kg=float("nan"))
        with self.assertRaises(ValueError):
            CartItem("X", 1.0, 1, weight_kg=float("inf"))

    def test_zero_unit_price_allowed(self):
        item = CartItem("Free sample", 0.0, 1)
        self.assertEqual(item.subtotal, Decimal("0.00"))

    def test_to_line_dict_includes_weight(self):
        d = CartItem("Heavy", 10.0, 2, sku="H-1", weight_kg=3.5).to_line_dict()
        self.assertEqual(d["weight_kg"], 3.5)
        self.assertAlmostEqual(d["unit_price"], 10.0, places=2)
        self.assertEqual(d["quantity"], 2)

    def test_unit_price_quantized_before_line_subtotal(self):
        # Unit price is stored quantized to cents; 10.005 USD/ea becomes 10.00.
        self.assertEqual(CartItem("X", Decimal("10.005"), 3).subtotal, Decimal("30.00"))

    def test_line_subtotal_quantized(self):
        self.assertEqual(CartItem("X", Decimal("10.017"), 1).subtotal, Decimal("10.02"))


class TestCartSubtotal(unittest.TestCase):
    def test_empty_cart(self):
        self.assertEqual(cart_subtotal([]), Decimal("0.00"))

    def test_sums_line_subtotals_and_rounds(self):
        items = [
            CartItem("A", 10.0, 1),
            CartItem("B", 20.0, 2),
        ]
        self.assertEqual(cart_subtotal(items), Decimal("50.00"))


class TestOrderIdAndTimestamp(unittest.TestCase):
    def test_generate_order_id_format(self):
        oid = generate_order_id()
        self.assertTrue(oid.startswith("ORD-"))
        self.assertEqual(len(oid), len("ORD-") + 12)
        self.assertTrue(re.fullmatch(r"ORD-[0-9A-F]{12}", oid))

    def test_generate_order_ids_are_unique(self):
        ids = {generate_order_id() for _ in range(256)}
        self.assertEqual(len(ids), 256)

    def test_utc_now_iso_is_parseable_utc(self):
        s = utc_now_iso()
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        self.assertIsNotNone(dt.tzinfo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
