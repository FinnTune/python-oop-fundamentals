# 03 — Polymorphism

**Poly** = many. **Morph** = form. One call, many possible behaviours.

## Without polymorphism

    if isinstance(processor, StripePayment):
        processor.charge(amount, token)
    elif isinstance(processor, PayPalPayment):
        processor.charge(amount, token)   # same thing, different branch

You write the same logic for every type. Exhausting and fragile.

## With polymorphism

    def process_payment(processor: PaymentProcessor, amount, token):
        processor.charge(amount, token)   # works for any processor

    process_payment(StripePayment("sk_live_abc"), 49.99, "tok_visa")
    process_payment(PayPalPayment("pp_id", "pp_sec"), 49.99, "tok_pp")

Same function. Two different behaviours. Zero if statements.

## How Python resolves it

When you call `processor.charge(...)`, Python looks at what
`processor` actually IS at runtime and dispatches to that class's
implementation automatically. The type hint is just documentation.

## The analogy

A power socket is an interface. Any plug that fits it works — phone
charger, lamp, laptop. The socket doesn't know or care what's plugged
in. Each device provides its own behaviour behind the same contract.

## Source file
payment/order_service.py
