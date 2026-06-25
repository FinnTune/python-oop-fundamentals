"""
Interactive walkthrough for the ``payment`` package (OOP concepts).

Uses **fake** processors and demo API keys. Do not point this script at production
credentials or real cardholder data. See ``payment.security`` and package
docstrings for security expectations and limitations.
"""

from decimal import Decimal

from payment import (
    Address,
    InMemoryInventory,
    NullShippingCalculator,
    NullTaxCalculator,
    OrderService,
    PayPalPayment,
    PromoCodeDiscountCalculator,
    StripePayment,
    build_cart_from_catalog,
)
from payment.domain import CartItem
from payment.order_service import order_service_for_tests
from payment.processor import PaymentProcessor


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


def process_payment(processor: PaymentProcessor, amount: Decimal, token: str):
    """Knows nothing about Stripe or PayPal — just calls .charge()."""
    success = processor.charge(amount=amount, token=token, context=None)
    print(f"Outcome: {'success' if success else 'failed'}")


process_payment(stripe, Decimal("29.99"), "tok_visa_4242")
process_payment(paypal, Decimal("29.99"), "tok_paypal_abc")


# ── CONCEPT 4 — Dependency Injection ─────────────────
separator("CONCEPT 4 — Dependency Injection (payments + pricing strategies)")

cart = [
    CartItem(
        name="Clean Code (book)",
        price=34.99,
        quantity=1,
        sku="BOOK-CC-001",
        tax_category="reduced",
        weight_kg=0.6,
    ),
    CartItem(
        name="Mechanical Keyboard",
        price=89.99,
        quantity=1,
        sku="KB-MECH-87",
        tax_category="general",
        weight_kg=1.1,
    ),
    CartItem(
        name="USB-C Hub",
        price=24.99,
        quantity=2,
        sku="HUB-USBC-7N1",
        tax_category="general",
        weight_kg=0.2,
    ),
]

office_addr = Address(
    line1="742 Evergreen Terrace",
    city="Springfield",
    region="IL",
    postal_code="62704",
    country="US",
)

stripe_service = OrderService(processor=stripe)
order = stripe_service.place_order(
    cart,
    payment_token="tok_visa_4242424242424242",
    shipping_address=office_addr,
)
print(
    f"Placed via: {order.processor}, "
    f"order {order.order_id}, "
    f"subtotal ${order.subtotal:.2f}, "
    f"tax ${order.tax:.2f}, "
    f"ship ${order.shipping:.2f}, "
    f"charged ${order.total:.2f}",
)

paypal_service = OrderService(
    processor=paypal,
    tax_calculator=NullTaxCalculator(),
    shipping_calculator=NullShippingCalculator(),
)
order = paypal_service.place_order(
    cart,
    payment_token="tok_paypal_approved_id",
    shipping_address=office_addr,
)
print(
    "Same cart with null tax/shipping strategies "
    f"(still passes address): charged ${order.total:.2f}",
)

small_cart = [
    CartItem(
        name="Notebook (A5)",
        price=19.99,
        quantity=1,
        sku="NB-A5-LIN",
        tax_category="general",
        weight_kg=0.3,
    ),
]
print("\n  (Subtotal under $100 — weight-based shipping applies.)")
stripe_service.place_order(
    small_cart,
    payment_token="tok_visa_4242424242424242",
    shipping_address=office_addr,
)


# ── CONCEPT 5 — self keeps instances independent ──────
separator("CONCEPT 5 — self keeps instances independent")

small = [CartItem("Sticker Pack", 9.99, 1, sku="STICK-001", weight_kg=0.05)]
big = [CartItem("Monitor", 399.99, 1, sku="MON-27-4K", weight_kg=6.4)]

service_a = order_service_for_tests(StripePayment("sk_live_aaa"))
service_b = order_service_for_tests(StripePayment("sk_live_bbb"))

service_a.place_order(small, "tok_1")
service_a.place_order(big, "tok_2")
service_b.place_order(small, "tok_3")

print(f"service_a order count: {service_a.order_count}")   # 2
print(f"service_b order count: {service_b.order_count}")   # 1


# ── CONCEPT 6 — More strategies: catalog, inventory, promo codes ──
separator("CONCEPT 6 — Catalog + inventory + promo discount")

catalog_cart = build_cart_from_catalog(
    [
        ("BOOK-CC-001", 1),
        ("NB-A5-LIN", 2),
    ]
)
stock = InMemoryInventory(
    {
        "BOOK-CC-001": 3,
        "NB-A5-LIN": 5,
    }
)
promo_service = OrderService(
    processor=StripePayment("sk_live_promo"),
    inventory=stock,
    discount_calculator=PromoCodeDiscountCalculator({"SAVE10": "0.10"}),
)
placed = promo_service.place_order(
    catalog_cart,
    "tok_visa_promo",
    shipping_address=office_addr,
    promo_code="SAVE10",
    customer_id="demo-customer-1",
)
print(
    f"Catalog order {placed.order_id}: discount ${placed.discount:.2f}, "
    f"charged ${placed.total:.2f}, stock BOOK left {stock.available('BOOK-CC-001')}"
)
lookup = promo_service.get_order(placed.order_id)
if lookup:
    print(f"Lookup by id: {lookup.order_id} status={lookup.status.value}")
else:
    print("Lookup by id: —")
promo_service.refund_order(placed.order_id)
refunded = promo_service.get_order(placed.order_id)
assert refunded is not None
print(
    f"After refund: status={refunded.status.value}, "
    f"stock BOOK restored to {stock.available('BOOK-CC-001')}"
)


# ── EXTRA — Richer data in history ────────────────────
separator("EXTRA — Order snapshot (line items + audit fields)")

snap = service_a.order_history_snapshot()
if snap:
    last = snap[-1]
    print(f"Last order: {last.order_id} at {last.placed_at}")
    for line in last.line_items:
        sku = line["sku"] or "—"
        title = line["name"][:28]
        qty = line["quantity"]
        sub = line["subtotal"]
        print(f"  {sku:12}  {title:28}  x{qty}  ${sub:.2f}")

separator("Done — run: python -m pytest tests/ -v")
