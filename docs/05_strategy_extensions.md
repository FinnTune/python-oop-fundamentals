# Strategy pattern beyond payments — inventory, discounts, and catalog data.

## What you already know

Tax and shipping are **strategies**: pluggable objects injected into
``OrderService`` so checkout logic stays the same while rules change.

This doc adds three more strategies and richer order records.

## Inventory (`payment/inventory.py`)

Before charging, ``OrderService`` calls ``inventory.reserve(cart)``. If stock is
insufficient, ``InsufficientStockError`` is raised and **no charge** happens.

On failed payment, reserved units are **restored**. On refund, stock goes back via
``inventory.restore(...)``.

| Class | Role |
|---|---|
| ``NullInventory`` | Always succeeds (tests) |
| ``InMemoryInventory`` | Dict of SKU → quantity |

## Discounts (`payment/discounts.py`)

``DiscountCalculator`` subtracts from the merchandise subtotal before tax/shipping
are added to the total.

| Class | Role |
|---|---|
| ``NullDiscountCalculator`` | No discount (tests) |
| ``PercentageDiscountCalculator`` | Flat % off subtotal |
| ``PromoCodeDiscountCalculator`` | Code → rate map, e.g. ``SAVE10`` |

Pass ``promo_code=`` into ``place_order`` to activate promo-based calculators.

## Catalog (`payment/catalog.py`)

``Product`` is a frozen master record; ``to_cart_item(quantity)`` builds a live
``CartItem``. ``SAMPLE_CATALOG`` matches the SKUs used in ``main.py``.

## Order lifecycle

``PlacedOrder`` now tracks ``status`` (``paid`` / ``refunded``), ``discount``,
``customer_id``, and ``promo_code``. Refunded orders **stay in history** with
``status=refunded`` so you can audit past transactions.

Query helpers:

- ``get_order(order_id)``
- ``orders_for_customer(customer_id)``
- ``paid_order_count`` vs ``order_count``

## Domain errors (`payment/exceptions.py`)

| Exception | When |
|---|---|
| ``PaymentFailedError`` | Processor declined charge |
| ``InsufficientStockError`` | Not enough stock |
| ``OrderNotFoundError`` | Reserved for future lookup APIs |

## Source files

```
payment/inventory.py
payment/discounts.py
payment/catalog.py
payment/exceptions.py
payment/placed_order.py   # OrderStatus enum
tests/test_inventory.py
tests/test_discounts.py
tests/test_catalog.py
```
