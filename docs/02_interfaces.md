# 02 — Interfaces (Abstract Base Classes)

## The problem

You have StripePayment. You add PayPalPayment. Without an interface,
every function that uses a processor needs to branch:

    if isinstance(processor, StripePayment):
        processor.charge(...)
    elif isinstance(processor, PayPalPayment):
        processor.pay(...)        # different method name!

Add Square and you add another branch. This never stops.

## The contract

An interface says: "claim to be a PaymentProcessor and you MUST have
these exact methods." Every implementation agrees on the same names
and signatures.

    from abc import ABC, abstractmethod

    class PaymentProcessor(ABC):

        @abstractmethod
        def charge(self, amount: float, token: str) -> bool: pass

        @abstractmethod
        def refund(self, charge_id: str) -> bool: pass

        @abstractmethod
        def get_last_transaction_id(self) -> str: pass

## What ABC enforces

If a subclass forgets to implement any abstract method, Python raises
a TypeError the moment you try to create an instance — before the bug
reaches a user.

## You cannot instantiate the interface itself

    PaymentProcessor()   # TypeError — it exists only to be inherited from

## Source files
payment/processor.py
payment/stripe_payment.py
payment/paypal_payment.py
