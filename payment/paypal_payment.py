"""
PayPal-shaped :class:`~payment.processor.PaymentProcessor` **stub** for teaching.

**Security**  
- ``client_secret`` is never printed or exposed via repr.
- ``client_id`` only appears as a short prefix in synthetic token diagnostics.
- Payment tokens are not echoed; capture IDs use :func:`~payment.security.token_fingerprint`.

Production PayPal integrations require OAuth over TLS, correct token lifetimes,
and server-side validation of every callback / webhook.
"""

from __future__ import annotations

from decimal import Decimal

from payment.payment_context import PaymentContext
from payment.processor import PaymentProcessor
from payment.security import redact_secret, token_fingerprint


class PayPalPayment(PaymentProcessor):
    """Demo processor with OAuth-style credentials stored on the instance."""

    def __init__(self, client_id: str, client_secret: str):
        if not isinstance(client_id, str) or not client_id.strip():
            raise ValueError("client_id must be a non-empty str.")
        if not isinstance(client_secret, str) or not client_secret.strip():
            raise ValueError("client_secret must be a non-empty str.")
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self._last_transaction_id: str = ""
        self._access_token: str = ""

    def _fetch_access_token(self) -> str:
        # Demo only — never print real access tokens in production.
        self._access_token = f"A21AAtoken_{self.client_id[:4]}"
        print("[PayPal] Access token obtained (value not logged).")
        return self._access_token

    def charge(
        self,
        amount: Decimal,
        token: str,
        context: PaymentContext | None = None,
    ) -> bool:
        self._fetch_access_token()
        meta = ""
        if context and context.metadata:
            meta = f" meta_keys={list(context.metadata.keys())}"
        cid = redact_secret(self.client_id, prefix=6)
        print(f"[PayPal] Creating order for ${amount:.2f} (client_id {cid})...{meta}")
        self._last_transaction_id = f"PAYID-{token_fingerprint(token).upper()}"
        print(f"[PayPal] Payment captured. ID: {self._last_transaction_id}")
        return True

    def refund(self, charge_id: str) -> bool:
        self._fetch_access_token()
        print(f"[PayPal] Refunding transaction {charge_id}...")
        print("[PayPal] Refund complete.")
        return True

    def get_last_transaction_id(self) -> str:
        return self._last_transaction_id
