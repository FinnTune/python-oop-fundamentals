"""
Validation and safe handling for payment-adjacent data.

**What this is for (teaching / demos)**  
Bounds inputs, normalizes identifiers, and avoids embedding raw payment tokens in
synthetic IDs or logs. That reduces *accidental* leakage and foot-guns.

**What this is *not***  
It does not make the project PCI-DSS compliant, “production secure,” or a substitute
for: vaults / KMS, network TLS, provider SDK hardening, WAFs, fraud detection,
key rotation, penetration testing, or organizational security processes.

**Practical rules for real systems**  
Never log PAN/CVV, raw card numbers, or full API secrets. Prefer short-lived
*payment method* IDs from your provider. Load secrets from the environment or a
secret manager, not source code. Treat ``payment_token`` as highly sensitive in transit
and at rest.
"""

from __future__ import annotations

import hashlib
import re

# --- Sizes (defensive defaults; tune per integration) ---

MIN_PAYMENT_TOKEN_LEN = 1
MAX_PAYMENT_TOKEN_LEN = 2048
MAX_IDEMPOTENCY_KEY_LEN = 255
MAX_CUSTOMER_ID_LEN = 128
MAX_METADATA_ENTRIES = 32
MAX_METADATA_KEY_LEN = 64
MAX_METADATA_VALUE_LEN = 512

_MAX_LABEL_LEN = 200
_MAX_SKU_LEN = 64
_MAX_NAME_LEN = 300

MAX_ORDER_ID_QUERY_LEN = 64

_ADDRESS_FIELD_LIMITS: dict[str, int] = {
    "line1": 200,
    "line2": 200,
    "city": 120,
    "region": 120,
    "postal_code": 32,
    # ISO 3166-1 alpha-2 is two letters; allow a few extra for teaching datasets.
    "country": 8,
}

_CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")


def token_fingerprint(token: str, *, length: int = 12) -> str:
    """
    Deterministic, non-reversible *label* derived from a token (for fake IDs / correlation).

    This is **not** a password hash: short tokens could still be brute-forced offline.
    Prefer not to derive public identifiers from secrets at all in production; use
    provider-returned charge IDs only.
    """
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return digest[:length]


def redact_secret(value: str, *, prefix: int = 4) -> str:
    """Return a log-safe preview like ``'sk_liv…'`` (never the full secret)."""
    value = value.strip()
    if not value:
        return ""
    if len(value) <= prefix + 1:
        return "…"
    return f"{value[:prefix]}…"


def normalize_currency(currency: str) -> str:
    """Validate and normalize an ISO 4217-style 3-letter currency code."""
    c = currency.strip().upper()
    if not _CURRENCY_CODE.fullmatch(c):
        raise ValueError(
            "currency must be a 3-letter ISO 4217 code (e.g. 'USD', 'EUR'); "
            f"got {currency!r}."
        )
    return c


def validate_payment_token(token: str) -> str:
    """Strip and validate a payment token; reject NULs and absurd lengths."""
    if not isinstance(token, str):
        raise TypeError("payment_token must be a str.")
    t = token.strip()
    if len(t) < MIN_PAYMENT_TOKEN_LEN or len(t) > MAX_PAYMENT_TOKEN_LEN:
        raise ValueError(
            f"payment_token length must be between {MIN_PAYMENT_TOKEN_LEN} "
            f"and {MAX_PAYMENT_TOKEN_LEN}."
        )
    if "\x00" in t:
        raise ValueError("payment_token must not contain NUL bytes.")
    return t


def validate_idempotency_key(key: str) -> str:
    if not isinstance(key, str):
        raise TypeError("idempotency_key must be a str.")
    k = key.strip()
    if len(k) > MAX_IDEMPOTENCY_KEY_LEN:
        raise ValueError(f"idempotency_key must be at most {MAX_IDEMPOTENCY_KEY_LEN} characters.")
    return k


def validate_customer_id(customer_id: str) -> str:
    if not isinstance(customer_id, str):
        raise TypeError("customer_id must be a str.")
    c = customer_id.strip()
    if len(c) > MAX_CUSTOMER_ID_LEN:
        raise ValueError(f"customer_id must be at most {MAX_CUSTOMER_ID_LEN} characters.")
    return c


def validate_payment_metadata(metadata: dict[str, str] | None) -> dict[str, str]:
    """Copy metadata with size limits; values must be strings (no nested structures)."""
    if not metadata:
        return {}
    if len(metadata) > MAX_METADATA_ENTRIES:
        raise ValueError(f"payment_metadata may have at most {MAX_METADATA_ENTRIES} entries.")
    out: dict[str, str] = {}
    for k, v in metadata.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise TypeError("payment_metadata keys and values must be str.")
        kk = k.strip()
        if len(kk) > MAX_METADATA_KEY_LEN:
            raise ValueError(f"metadata key too long (max {MAX_METADATA_KEY_LEN}).")
        if len(v) > MAX_METADATA_VALUE_LEN:
            raise ValueError(f"metadata value for {kk!r} too long (max {MAX_METADATA_VALUE_LEN}).")
        if "\x00" in kk or "\x00" in v:
            raise ValueError("metadata must not contain NUL bytes.")
        out[kk] = v
    return out


def validate_cart_line_label(*, name: str, sku: str, tax_category: str) -> None:
    if len(name) > _MAX_NAME_LEN:
        raise ValueError(f"line name exceeds {_MAX_NAME_LEN} characters.")
    if len(sku) > _MAX_SKU_LEN:
        raise ValueError(f"sku exceeds {_MAX_SKU_LEN} characters.")
    if len(tax_category) > _MAX_LABEL_LEN:
        raise ValueError(f"tax_category exceeds {_MAX_LABEL_LEN} characters.")
    if "\x00" in name or "\x00" in sku or "\x00" in tax_category:
        raise ValueError("line fields must not contain NUL bytes.")


def validate_order_id_query(order_id: str) -> str:
    """
    Validate an ``order_id`` passed into refund/search paths.

    Keeps lookups bounded and rejects obvious abuse; does not prove the caller is
    authorized to refund that order (always enforce authorization in real systems).
    """
    if not isinstance(order_id, str):
        raise TypeError("order_id must be a str.")
    o = order_id.strip()
    if not o or len(o) > MAX_ORDER_ID_QUERY_LEN or "\x00" in o:
        raise ValueError("order_id is invalid.")
    return o


def validate_address_fields(
    line1: str,
    city: str,
    region: str,
    postal_code: str,
    *,
    country: str,
    line2: str = "",
) -> None:
    fields = {
        "line1": line1,
        "line2": line2,
        "city": city,
        "region": region,
        "postal_code": postal_code,
        "country": country,
    }
    for key, val in fields.items():
        limit = _ADDRESS_FIELD_LIMITS[key]
        if len(val) > limit:
            raise ValueError(f"address {key} exceeds {limit} characters.")
        if "\x00" in val:
            raise ValueError(f"address {key} must not contain NUL bytes.")
