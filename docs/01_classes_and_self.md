# 01 — Classes and `self`

## The problem

You need to connect to Stripe. Without a class, you store everything in plain variables:

    stripe_api_key = "sk_live_abc"
    stripe_last_charge = ""

Add a test environment and it doubles. Add a third and it collapses.
A **class** bundles related data and behaviour into a reusable blueprint.

## Blueprint vs instance

    class StripePayment:
        def __init__(self, api_key):
            self.api_key = api_key          # stored on THIS instance
            self._last_charge_id = ""

    prod = StripePayment(api_key="sk_live_abc")   # instance 1
    test = StripePayment(api_key="sk_test_xyz")   # instance 2

`prod` and `test` are independent. Charging on one never affects the other.

## What is `self`?

`self` is how an object refers to its own data. When you write:

    prod.charge(50, "tok_visa")

Python rewrites it internally as:

    StripePayment.charge(prod, 50, "tok_visa")

The object `prod` is passed as the first argument. Inside the method
that argument is called `self`. So `self.api_key` always means
*this instance's* api_key — not any other object's.

## Mental model

Think of `self` as each object's own private notebook. Two instances,
two notebooks, no mixing.

## Source file
payment/stripe_payment.py
