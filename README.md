# Python OOP Fundamentals

A runnable reference for core OOP concepts taught through a small but realistic
**payment and checkout** domain: processors, pricing strategies, inventory, discounts,
and order lifecycle.

## Concepts covered

| Concept | Plain-English meaning | Where to look |
|---|---|---|
| **Class** | Blueprint for objects | `payment/stripe_payment.py` |
| **`self`** | Each instance keeps its own data | `StripePayment`, `OrderService` |
| **Interface (ABC)** | Contract every processor must implement | `payment/processor.py` |
| **Polymorphism** | Same `charge()` call, different providers | `main.py`, `OrderService` |
| **Dependency injection** | Dependencies passed in, not created inside | `OrderService.__init__` |
| **Strategy pattern** | Swappable tax, shipping, discount, inventory rules | `payment/pricing.py`, `discounts.py`, `inventory.py` |

## Repo layout

```
python-oop-fundamentals/
├── payment/
│   ├── processor.py          # PaymentProcessor interface (ABC)
│   ├── stripe_payment.py     # concrete processor #1
│   ├── paypal_payment.py     # concrete processor #2
│   ├── order_service.py      # checkout orchestration + DI
│   ├── domain.py             # Address, CartItem, helpers
│   ├── pricing.py            # tax & shipping strategies
│   ├── discounts.py          # promo / percentage discounts
│   ├── inventory.py          # stock reservation
│   ├── catalog.py            # Product catalog → cart lines
│   ├── placed_order.py       # PlacedOrder + OrderStatus
│   ├── payment_context.py    # charge metadata
│   ├── money.py                # Decimal money helpers
│   └── security.py           # validation & safe logging
├── tests/                    # pytest suite (domain, pricing, security, …)
├── docs/                     # concept guides 01–05
├── main.py                   # interactive demo — start here
├── pyproject.toml            # project metadata + ruff/mypy
├── requirements.txt          # pinned pytest stack
└── .github/workflows/test.yml
```

## Quickstart

```bash
git clone https://github.com/YOUR_USERNAME/python-oop-fundamentals.git
cd python-oop-fundamentals
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install ruff mypy   # optional: match CI lint/type checks
python main.py
python -m pytest tests/ -v
python -m ruff check payment tests main.py
python -m mypy payment
```

## Learning path

Read the docs in order, then open the matching source:

| Doc | Source |
|---|---|
| `docs/01_classes_and_self.md` | `payment/stripe_payment.py` |
| `docs/02_interfaces.md` | `payment/processor.py` |
| `docs/03_polymorphism.md` | `payment/order_service.py` |
| `docs/04_dependency_injection.md` | `tests/test_order_service.py`, `tests/fakes.py` |
| `docs/05_strategy_extensions.md` | `inventory.py`, `discounts.py`, `catalog.py` |
| — | `main.py` (end-to-end demo) |

## Security note

This is **teaching code** with fake payment stubs. See `payment/security.py` and
package docstrings for validation/redaction helpers and honest limits. Do not process
real cardholder data without a full security review and compliant infrastructure.

## License

Copyright (C) 2026 Andre Teetor

This project is licensed under the GNU General Public License v2.0 —
see the [LICENSE](LICENSE) file for details.
