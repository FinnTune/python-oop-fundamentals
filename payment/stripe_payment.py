"""
Stripe-shaped :class:`~payment.processor.PaymentProcessor` **stub** for teaching.

**Security**  
- Never prints the full API key — only a short prefix via :func:`~payment.security.redact_secret`.
- Never logs the raw payment token; synthetic charge IDs use
  :func:`~payment.security.token_fingerprint` instead of embedding token substrings.

In production you would call the official Stripe SDK over TLS, use restricted API keys,
webhook signing secrets, idempotency keys on mutating requests, and never handle raw
card numbers on your server (use Elements / Payment Element / Checkout).
"""

from __future__ import annotations

from decimal import Decimal

from payment.payment_context import PaymentContext
from payment.processor import PaymentProcessor
from payment.security import redact_secret, token_fingerprint


class StripePayment(PaymentProcessor):
    """
    Demo processor holding a Stripe-style secret key on the instance (``self.api_key``).

    **Secret handling:** Do not commit real keys; load from the environment in real code.
    """

    def __init__(self, api_key: str):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("api_key must be a non-empty str.")
        self.api_key = api_key.strip()
        self._last_charge_id: str = ""

    def charge(
        self,
        amount: Decimal,
        token: str,
        context: PaymentContext | None = None,
    ) -> bool:
        ctx_note = ""
        if context and (context.order_id or context.idempotency_key):
            # idempotency_key can be sensitive in some designs; here we only show length.
            ik = context.idempotency_key
            ik_safe = f"len={len(ik)}" if ik else ""
            ctx_note = f" (order={context.order_id!r}, idempotency={ik_safe})"
        key_preview = redact_secret(self.api_key, prefix=8)
        print(f"[Stripe] Charging ${amount:.2f} with key {key_preview}{ctx_note}")
        self._last_charge_id = f"ch_stripe_{token_fingerprint(token)}"
        print(f"[Stripe] Success. Charge ID: {self._last_charge_id}")
        return True

    def refund(self, charge_id: str) -> bool:
        print(f"[Stripe] Refunding {charge_id}...")
        print("[Stripe] Refund complete.")
        return True

    def get_last_transaction_id(self) -> str:
        return self._last_charge_id
