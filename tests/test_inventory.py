"""Tests for payment.inventory."""

from __future__ import annotations

import unittest
from decimal import Decimal

from payment.domain import CartItem
from payment.exceptions import InsufficientStockError
from payment.inventory import InMemoryInventory, NullInventory


class TestNullInventory(unittest.TestCase):
    def test_reserve_and_restore_no_op(self):
        inv = NullInventory()
        cart = [CartItem("X", 10, 1, sku="SKU-1")]
        inv.reserve(cart)
        inv.restore(cart)


class TestInMemoryInventory(unittest.TestCase):
    def setUp(self):
        self.inv = InMemoryInventory({"BOOK-1": 2, "PEN-1": 10})

    def test_reserve_decrements(self):
        cart = [CartItem("Book", 5, 1, sku="BOOK-1")]
        self.inv.reserve(cart)
        self.assertEqual(self.inv.available("BOOK-1"), 1)

    def test_insufficient_stock_raises(self):
        cart = [CartItem("Book", 5, 3, sku="BOOK-1")]
        with self.assertRaises(InsufficientStockError) as ctx:
            self.inv.reserve(cart)
        self.assertEqual(ctx.exception.sku, "BOOK-1")
        self.assertEqual(self.inv.available("BOOK-1"), 2)

    def test_restore_returns_units(self):
        cart = [CartItem("Pen", 1, 2, sku="PEN-1")]
        self.inv.reserve(cart)
        self.inv.restore(cart)
        self.assertEqual(self.inv.available("PEN-1"), 10)

    def test_lines_without_sku_skipped(self):
        cart = [CartItem("Misc", Decimal("1.00"), 99)]
        self.inv.reserve(cart)


if __name__ == "__main__":
    unittest.main(verbosity=2)
