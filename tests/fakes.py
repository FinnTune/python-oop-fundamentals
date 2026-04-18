"""Test doubles shared across test modules."""

from __future__ import annotations

from typing import List, Optional

from payment.processor import PaymentProcessor


class FakePaymentProcessor(PaymentProcessor):
    """
    Implements PaymentProcessor but records calls instead of hitting an API.
    """

    def __init__(
        self,
        should_succeed: bool = True,
        *,
        refund_succeeds: Optional[bool] = None,
    ):
        self.should_succeed = should_succeed
        self._refund_succeeds = should_succeed if refund_succeeds is None else refund_succeeds
        self.charges: List[float] = []
        self.refunds: List[str] = []
        self.tokens: List[str] = []
        self._last_transaction_id = ""

    def charge(self, amount: float, token: str) -> bool:
        self.tokens.append(token)
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
