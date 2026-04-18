"""
Abstract payment gateway contract — implement :meth:`charge`, :meth:`refund`, and
:meth:`get_last_transaction_id` for each provider (Stripe, PayPal, etc.).

**Security expectations for implementors**  
- Treat ``amount`` as authoritative only after *your* server recomputed totals from
  trusted cart data (never trust client-supplied totals alone).
- ``token`` must be a *provider-issued* payment method or session token, not raw PAN/CVV.
  Never log it, cache it in plaintext logs, or embed it in URLs.
- Use ``context.idempotency_key`` on mutating provider calls in production so retries
  do not double-charge.
- Send all traffic to payment APIs over TLS; pin versions of provider SDKs you depend on.

This module defines the interface only — it cannot enforce those rules without concrete
implementations and infrastructure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from payment.payment_context import PaymentContext


class PaymentProcessor(ABC):
    """
    Interface every concrete processor must implement.

    Python raises :exc:`TypeError` if you omit an abstract method on a subclass.
    """

    @abstractmethod
    def charge(
        self,
        amount: Decimal,
        token: str,
        context: PaymentContext | None = None,
    ) -> bool:
        """
        Attempt to capture ``amount`` using ``token``.

        Args:
            amount: Major currency units (e.g. ``Decimal("49.99")`` for USD), already
                quantized to provider expectations by the caller.
            token: Opaque payment credential from your client integration.
            context: Optional correlation metadata (order id, idempotency, customer).

        Returns:
            ``True`` if the provider accepted the charge, ``False`` if it declined
            without raising (implementations may also raise on hard failures).

        Note:
            Return values are simplified for teaching; real SDKs expose rich result
            objects, network errors, and three‑DS / SCA flows.
        """
        ...

    @abstractmethod
    def refund(self, charge_id: str) -> bool:
        """
        Refund a prior capture identified by ``charge_id`` (provider-specific string).

        **Authorization:** In real services, verify the caller may refund this charge
        before invoking the provider.
        """
        ...

    @abstractmethod
    def get_last_transaction_id(self) -> str:
        """Provider reference for the last successful charge, or ``\"\"`` if none."""
        ...
