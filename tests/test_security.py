"""Tests for payment.security helpers."""

from __future__ import annotations

import unittest
from decimal import Decimal

from payment.security import (
    normalize_currency,
    redact_secret,
    token_fingerprint,
    validate_customer_id,
    validate_idempotency_key,
    validate_order_id_query,
    validate_payment_metadata,
    validate_payment_token,
)


class TestRedactAndFingerprint(unittest.TestCase):
    def test_redact_short_value(self):
        self.assertEqual(redact_secret("ab"), "…")

    def test_redact_prefix(self):
        self.assertTrue(redact_secret("sk_live_abcdef", prefix=6).startswith("sk_liv"))
        self.assertTrue(redact_secret("sk_live_abcdef", prefix=6).endswith("…"))

    def test_fingerprint_stable(self):
        self.assertEqual(token_fingerprint("tok_a"), token_fingerprint("tok_a"))
        self.assertNotEqual(token_fingerprint("tok_a"), token_fingerprint("tok_b"))


class TestCurrencyAndToken(unittest.TestCase):
    def test_normalize_currency(self):
        self.assertEqual(normalize_currency("  eur  "), "EUR")

    def test_normalize_currency_rejects_garbage(self):
        with self.assertRaises(ValueError):
            normalize_currency("EURO")
        with self.assertRaises(ValueError):
            normalize_currency("US")

    def test_validate_payment_token(self):
        self.assertEqual(validate_payment_token("  tok_1  "), "tok_1")

    def test_token_rejects_nul(self):
        with self.assertRaises(ValueError):
            validate_payment_token("bad\x00tok")


class TestMetadataAndIds(unittest.TestCase):
    def test_validate_metadata_copy(self):
        m = {"a": "1", "b": "2"}
        out = validate_payment_metadata(m)
        self.assertEqual(out, m)
        out["a"] = "x"
        self.assertEqual(m["a"], "1")

    def test_metadata_rejects_non_str(self):
        with self.assertRaises(TypeError):
            validate_payment_metadata({"a": Decimal("1")})  # type: ignore[dict-item]

    def test_order_id_query(self):
        self.assertEqual(validate_order_id_query("  ORD-ABC  "), "ORD-ABC")

    def test_order_id_query_rejects_empty(self):
        with self.assertRaises(ValueError):
            validate_order_id_query("   ")

    def test_idempotency_and_customer_bounds(self):
        self.assertEqual(validate_idempotency_key(""), "")
        self.assertEqual(validate_customer_id(""), "")
        with self.assertRaises(ValueError):
            validate_idempotency_key("x" * 300)
        with self.assertRaises(ValueError):
            validate_customer_id("y" * 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
