from payment import StripePayment, PayPalPayment, OrderService
from payment.processor import PaymentProcessor
from payment.order_service import CartItem


def separator(title):
    print(f"\n{'─'*50}\n  {title}\n{'─'*50}")


# ── CONCEPT 1 — Classes and self ─────────────────────
separator("CONCEPT 1 — Classes and self")

prod_stripe = StripePayment(api_key="sk_live_abc123456")
test_stripe = StripePayment(api_key="sk_test_xyz789012")

print(f"Same object? {prod_stripe is test_stripe}")          # False
print(f"prod key:    {prod_stripe.api_key[:7]}...")
print(f"test key:    {test_stripe.api_key[:7]}...")


# ── CONCEPT 2 — Interface enforces the contract ───────
separator("CONCEPT 2 — Interface enforces the contract")

try:
    PaymentProcessor()   # abstract — cannot be instantiated directly
except TypeError as e:
    print(f"Cannot instantiate interface: {e}")

stripe = StripePayment("sk_live_abc123456")
paypal = PayPalPayment("pp_client_id", "pp_secret_key")

print(f"StripePayment is a PaymentProcessor? {isinstance(stripe, PaymentProcessor)}")
print(f"PayPalPayment is a PaymentProcessor? {isinstance(paypal, PaymentProcessor)}")


# ── CONCEPT 3 — Polymorphism ──────────────────────────
separator("CONCEPT 3 — Polymorphism")

def process_payment(processor: PaymentProcessor, amount: float, token: str):
    """Knows nothing about Stripe or PayPal — just calls .charge()."""
    success = processor.charge(amount=amount, token=token)
    print(f"Outcome: {'success' if success else 'failed'}")

process_payment(stripe, 29.99, "tok_visa_4242")
process_payment(paypal, 29.99, "tok_paypal_abc")


# ── CONCEPT 4 — Dependency Injection ─────────────────
separator("CONCEPT 4 — Dependency Injection")

cart = [
    CartItem("Clean Code (book)",   34.99, 1),
    CartItem("Mechanical Keyboard", 89.99, 1),
    CartItem("USB-C Hub",           24.99, 2),
]

stripe_service = OrderService(processor=stripe)
order = stripe_service.place_order(cart, payment_token="tok_visa_4242424242424242")
print(f"Placed via: {order['processor']}, Total: ${order['total']:.2f}")

paypal_service = OrderService(processor=paypal)
order = paypal_service.place_order(cart, payment_token="tok_paypal_approved_id")
print(f"Placed via: {order['processor']}, Total: ${order['total']:.2f}")


# ── CONCEPT 5 — self keeps instances independent ──────
separator("CONCEPT 5 — self keeps instances independent")

small = [CartItem("Sticker Pack", 9.99, 1)]
big   = [CartItem("Monitor",    399.99, 1)]

service_a = OrderService(processor=StripePayment("sk_live_aaa"))
service_b = OrderService(processor=StripePayment("sk_live_bbb"))

service_a.place_order(small, "tok_1")
service_a.place_order(big,   "tok_2")
service_b.place_order(small, "tok_3")

print(f"service_a order count: {service_a.order_count}")   # 2
print(f"service_b order count: {service_b.order_count}")   # 1

separator("Done — run: python -m pytest tests/ -v")
