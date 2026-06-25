"""Tests for payment.catalog."""

from __future__ import annotations

import unittest
from decimal import Decimal

from payment.catalog import SAMPLE_CATALOG, Product, build_cart_from_catalog


class TestCatalog(unittest.TestCase):
    def test_sample_catalog_has_expected_skus(self):
        self.assertIn("BOOK-CC-001", SAMPLE_CATALOG)
        self.assertIn("MON-27-4K", SAMPLE_CATALOG)

    def test_product_to_cart_item(self):
        p = Product(sku="X-1", name="Widget", unit_price=Decimal("9.99"))
        item = p.to_cart_item(2)
        self.assertEqual(item.sku, "X-1")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.subtotal, Decimal("19.98"))

    def test_build_cart_from_catalog(self):
        cart = build_cart_from_catalog([("BOOK-CC-001", 1), ("NB-A5-LIN", 2)])
        self.assertEqual(len(cart), 2)
        self.assertEqual(cart[0].sku, "BOOK-CC-001")
        self.assertEqual(cart[1].quantity, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
