"""
Payment and checkout **teaching** package: processors, pricing strategies, orders.

**Security posture**  
This code prioritizes clarity for learning. :mod:`payment.security` documents realistic
hardening (validation, redaction, fingerprinting) but **does not** satisfy PCI-DSS,
SOC2, or your organization's requirements by itself. Never use the bundled stubs for
real cardholder data without a full security review.

Public re-exports below support ``from payment import …`` in exercises and demos.
"""

from payment.domain import Address, CartItem
from payment.order_service import OrderService, order_service_for_tests
from payment.payment_context import PaymentContext
from payment.paypal_payment import PayPalPayment
from payment.placed_order import PlacedOrder
from payment.pricing import (
    NullShippingCalculator,
    NullTaxCalculator,
    ShippingCalculator,
    StandardTaxCalculator,
    TaxCalculator,
    WeightBasedShippingCalculator,
)
from payment.processor import PaymentProcessor
from payment.stripe_payment import StripePayment

__all__ = [
    "Address",
    "CartItem",
    "NullShippingCalculator",
    "NullTaxCalculator",
    "OrderService",
    "PaymentContext",
    "PayPalPayment",
    "PlacedOrder",
    "PaymentProcessor",
    "ShippingCalculator",
    "StandardTaxCalculator",
    "StripePayment",
    "TaxCalculator",
    "WeightBasedShippingCalculator",
    "order_service_for_tests",
]
