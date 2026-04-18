"""
Test doubles shared across test modules.

These fakes record ``Decimal`` charge amounts and optional ``PaymentContext`` values.
They never perform I/O — keep using them instead of live credentials in tests.
"""

from __future__ import annotations

from decimal import Decimal

from payment.payment_context import PaymentContext
from payment.processor import PaymentProcessor


class FakePaymentProcessor(PaymentProcessor):
    """
    Implements PaymentProcessor but records calls instead of hitting an API.
    """

    def __init__(
        self,
        should_succeed: bool = True,
        *,
        refund_succeeds: bool | None = None,
    ):
        self.should_succeed = should_succeed
        self._refund_succeeds = should_succeed if refund_succeeds is None else refund_succeeds
        self.charges: list[Decimal] = []
        self.refunds: list[str] = []
        self.tokens: list[str] = []
        self.contexts: list[PaymentContext | None] = []
        self._last_transaction_id = ""

    def charge(
        self,
        amount: Decimal,
        token: str,
        context: PaymentContext | None = None,
    ) -> bool:
        self.tokens.append(token)
        self.contexts.append(context)
        if self.should_succeed:
            self._last_transaction_id = f"fake_ch_{len(self.charges) + 1}"
            self.charges.append(amount)
        return self.should_succeed

    def refund(self, charge_id: str) -> bool:
        if self._refund_succeeds:
            self.refunds.append(charge_id)
        return self._refund_succeeds

    def get_last_transaction_id(self) -> str:
        return self._last_transaction_id
