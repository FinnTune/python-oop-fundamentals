# 04 — Dependency Injection

## The core idea

A **dependency** is anything a class needs to do its job.
OrderService needs a payment processor — the processor is its dependency.

**Dependency Injection** means: the dependency is provided from outside
rather than created inside the class.

## Without DI — tightly coupled

    class OrderService:
        def __init__(self):
            self.processor = StripePayment("sk_live_abc")  # hardcoded

Problems: can't swap providers, can't test without hitting Stripe,
can't configure from outside.

## With DI — loosely coupled

    class OrderService:
        def __init__(self, processor: PaymentProcessor):
            self.processor = processor   # caller decides which processor

Now the caller controls everything:

    OrderService(processor=StripePayment("sk_live_abc"))   # production
    OrderService(processor=PayPalPayment("pp_id", "pp_sec"))  # staging
    OrderService(processor=FakePaymentProcessor())             # tests

OrderService is identical in all three cases.

## The three injection styles

**Constructor injection** — passed in __init__, stored for the object's lifetime.
Use when the dependency is required and permanent.

**Method injection** — passed into a specific method call.
Use when the dependency varies per call.

**Setter injection** — assigned after construction via a dedicated method.
Use when the dependency is optional or needs to be swapped at runtime.

## Why DI makes testing so much better

Without DI: every test calls real Stripe — slow, costs money, flaky.
With DI: inject a fake that records calls instead of hitting the network.

    fake = FakePaymentProcessor()
    service = OrderService(processor=fake)
    service.place_order(cart, "tok_test")
    assert fake.charges[0] == 79.97   # instant, free, reliable

## The one-sentence principle

Depend on abstractions (interfaces), not on concrete implementations.

## Source files
payment/order_service.py
tests/test_order_service.py
