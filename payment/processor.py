from abc import ABC, abstractmethod


class PaymentProcessor(ABC):
    """
    Interface — the contract every payment processor must honour.
    Inherit from this class and implement all three methods.
    Python will raise a TypeError if any method is missing.
    """

    @abstractmethod
    def charge(self, amount: float, token: str) -> bool:
        """
        Charge the customer.
        amount : dollars to charge, e.g. 49.99
        token  : a payment token from the frontend (Stripe/PayPal format)
        Returns True on success, False on failure.
        """
        pass

    @abstractmethod
    def refund(self, charge_id: str) -> bool:
        """
        Refund a previous charge by its ID.
        Returns True on success, False on failure.
        """
        pass

    @abstractmethod
    def get_last_transaction_id(self) -> str:
        """
        Return the ID of the most recent transaction,
        or an empty string if none has been made yet.
        """
        pass
