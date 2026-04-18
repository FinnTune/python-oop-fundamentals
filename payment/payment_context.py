"""
Structured metadata for a :meth:`~payment.processor.PaymentProcessor.charge` call.

Fields are intentionally plain strings so they map easily to HTTP headers or JSON.
Do **not** put secrets (API keys, raw card data, full PAN) into ``metadata`` —
provider SDKs have dedicated parameters for credentials.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PaymentContext:
    """
    Correlation and routing data accompanying a charge attempt.

    Attributes:
        currency: ISO 4217 code (validated at the :class:`~payment.order_service.OrderService`
            boundary when orders are placed through that API).
        idempotency_key: Client-supplied key so retries do not duplicate charges; keep
            unguessable if exposed publicly.
        order_id: Business identifier generated before the charge in our flow.
        customer_id: Opaque tenant/user reference — still PII in many jurisdictions.
        metadata: Small string map for risk/fraud tags; size-limited when using
            :func:`payment.security.validate_payment_metadata`.

    Security:
        This object is safe to pass to loggers **only** if your logging policy allows
        ``customer_id`` / ``order_id``. Never log payment tokens here.
    """

    currency: str = "USD"
    idempotency_key: str = ""
    order_id: str = ""
    customer_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)
