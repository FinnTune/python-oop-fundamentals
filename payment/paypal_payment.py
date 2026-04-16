from payment.processor import PaymentProcessor


class PayPalPayment(PaymentProcessor):
    """
    Concrete implementation of PaymentProcessor for PayPal.

    Internally very different from StripePayment (OAuth tokens, two-step
    charge flow) — but the outside world sees exactly the same interface.
    That sameness is what makes polymorphism work.
    """

    def __init__(self, client_id: str, client_secret: str):
        # PayPal uses OAuth credentials instead of a single API key.
        # This is an internal detail — the interface contract doesn't care.
        self.client_id = client_id
        self.client_secret = client_secret
        self._last_transaction_id: str = ""
        self._access_token: str = ""

    def _fetch_access_token(self) -> str:
        # Private helper (leading underscore = internal use only).
        # PayPal requires fetching a token before each API call.
        # In production: POST to PayPal's OAuth endpoint with credentials.
        self._access_token = f"A21AAtoken_{self.client_id[:4]}"
        print(f"[PayPal] Access token obtained.")
        return self._access_token

    def charge(self, amount: float, token: str) -> bool:
        self._fetch_access_token()
        print(f"[PayPal] Creating order for ${amount:.2f}...")
        self._last_transaction_id = f"PAYID-{token[:6].upper()}"
        print(f"[PayPal] Payment captured. ID: {self._last_transaction_id}")
        return True

    def refund(self, charge_id: str) -> bool:
        self._fetch_access_token()
        print(f"[PayPal] Refunding transaction {charge_id}...")
        print(f"[PayPal] Refund complete.")
        return True

    def get_last_transaction_id(self) -> str:
        return self._last_transaction_id
