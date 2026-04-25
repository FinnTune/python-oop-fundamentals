# Python OOP Fundamentals

A runnable reference for five core OOP concepts taught through a single
real-world example: a payment processing system.

## Concepts covered

| Concept | Plain-English meaning |
|---|---|
| **Class** | A blueprint that defines what an object is and can do |
| **`self`** | How an object refers to its own data |
| **Interface (ABC)** | A contract that guarantees every implementation has the same methods |
| **Polymorphism** | The same method call produces different behaviour depending on the object |
| **Dependency Injection** | Giving an object its dependencies from outside rather than hardcoding them |

## Repo layout
python-oop-fundamentals/
├── payment/
│   ├── init.py           # makes payment an importable package
│   ├── processor.py          # the Interface (Abstract Base Class)
│   ├── stripe_payment.py     # concrete class #1
│   ├── paypal_payment.py     # concrete class #2
│   └── order_service.py      # dependency injection + polymorphism
├── tests/
│   ├── init.py
│   └── test_order_service.py # 16 passing tests using a fake processor
├── docs/
│   ├── 01_classes_and_self.md
│   ├── 02_interfaces.md
│   ├── 03_polymorphism.md
│   └── 04_dependency_injection.md
├── main.py                   # runnable demo — start here
├── requirements.txt
└── README.md
## Quickstart

```bash
git clone https://github.com/YOUR_USERNAME/python-oop-fundamentals.git
cd python-oop-fundamentals
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
python -m pytest tests/ -v
```

## Learning path

Read the docs in order, then open the matching source file:
docs/01_classes_and_self.md     →  payment/stripe_payment.py
docs/02_interfaces.md           →  payment/processor.py
docs/03_polymorphism.md         →  payment/order_service.py
docs/04_dependency_injection.md →  tests/test_order_service.py
main.py                         →  see it all working together

## License

Copyright (C) 2026 Andre Teetor

This project is licensed under the GNU General Public License v2.0 —
see the [LICENSE](LICENSE) file for details.