from payment.processor import PaymentProcessor


class StripePayment(PaymentProcessor):
    """
    Concrete implementation of PaymentProcessor for Stripe.

    KEY CONCEPTS:
    - Class       : StripePayment is the blueprint
    - self        : each instance keeps its own api_key and charge history
    - Inheritance : StripePayment inherits the contract from PaymentProcessor
    """

    def __init__(self, api_key: str):
        # __init__ runs when you write StripePayment(api_key="...")
        # self.api_key stores the key ON THIS SPECIFIC INSTANCE.
        # Two StripePayment objects with different keys never interfere.
        self.api_key = api_key
        self._last_charge_id: str = ""
        # Leading underscore = internal — use get_last_transaction_id() instead.

    def charge(self, amount: float, token: str) -> bool:
        # self lets us read this instance's api_key and write to its _last_charge_id.
        print(f"[Stripe] Charging ${amount:.2f} with key {self.api_key[:8]}...")
        # In production you would call the Stripe SDK here.
        self._last_charge_id = f"ch_stripe_{token[:6]}"
        print(f"[Stripe] Success. Charge ID: {self._last_charge_id}")
        return True

    def refund(self, charge_id: str) -> bool:
        print(f"[Stripe] Refunding {charge_id}...")
        print(f"[Stripe] Refund complete.")
        return True

    def get_last_transaction_id(self) -> str:
        return self._last_charge_id
