#!/bin/bash
# Split app/services.py: one service per file under app/services/ (namespace package, no __init__.py),
# every exception in app/exceptions.py, the shared VAT constant in its own topic module.
set -euo pipefail
cd /app
python3 - <<'PY'
import ast
from pathlib import Path

source = Path("app/services.py").read_text()
lines = source.splitlines()
tree = ast.parse(source)


def segment(name):
    for node in tree.body:
        if getattr(node, "name", None) == name:
            start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
            return "\n".join(lines[start - 1:node.end_lineno])
    raise KeyError(name)


def block(*names):
    return "\n\n\n".join(segment(n) for n in names)


exceptions = [n.name for n in tree.body if isinstance(n, ast.ClassDef) and n.name.endswith("Error")]
Path("app/exceptions.py").write_text('"""Errors raised by the billing services."""\n\n\n' + block(*exceptions) + "\n")

Path("app/vat.py").write_text('''from decimal import ROUND_HALF_UP, Decimal

VAT_RATE = Decimal("0.20")


def vat_for(net_pence: int) -> int:
    vat = (Decimal(net_pence) * VAT_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(vat)
''')

Path("app/clock.py").write_text('''from datetime import UTC, datetime


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()
''')

services = Path("app/services")
services.mkdir()
Path("app/services.py").unlink()

(services / "customers.py").write_text('''import re
import sqlite3
from dataclasses import dataclass

from app.exceptions import CustomerNotFoundError, DuplicateEmailError, InvalidCustomerError
from app.repositories.customers import CustomerRepository

EMAIL_PATTERN = re.compile(r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
SUPPORTED_COUNTRIES = frozenset({"GB", "IE", "FR", "DE", "NL"})


''' + block("Customer", "_to_customer", "CustomerService") + "\n")

(services / "orders.py").write_text('''import sqlite3
from dataclasses import dataclass

from app.clock import utc_now_iso
from app.exceptions import InvalidOrderStateError, OrderLineError, OrderNotFoundError
from app.repositories.orders import OrderRepository
from app.services.customers import CustomerService
from app.vat import vat_for

MAX_ORDER_LINES = 50
ORDER_STATUSES = ("draft", "placed", "paid", "cancelled")


''' + block("OrderLine", "OrderTotals", "OrderService").replace("_vat_for(", "vat_for(").replace("_now()", "utc_now_iso()") + "\n")

(services / "invoices.py").write_text('''import sqlite3
from dataclasses import dataclass

from app.clock import utc_now_iso
from app.exceptions import (
    InvalidOrderStateError,
    InvoiceAlreadyIssuedError,
    InvoiceNotFoundError,
    InvoiceVoidedError,
)
from app.repositories.invoices import InvoiceRepository
from app.services.orders import OrderService
from app.vat import vat_for

INVOICE_NUMBER_PREFIX = "INV"
INVOICE_NUMBER_WIDTH = 6


''' + block("Invoice", "VatSummary", "_to_invoice", "_format_number", "InvoiceService")
    .replace("_vat_for(", "vat_for(").replace("_now()", "utc_now_iso()") + "\n")

test = Path("tests/test_services.py")
text = test.read_text()
start = text.index("from app.services import (")
end = text.index(")", start) + 1
text = text[:start] + '''from app.exceptions import (
    CustomerNotFoundError,
    DuplicateEmailError,
    InvalidCustomerError,
    InvalidOrderStateError,
    InvoiceAlreadyIssuedError,
    InvoiceVoidedError,
    OrderLineError,
)
from app.services.customers import CustomerService
from app.services.invoices import InvoiceService
from app.services.orders import OrderService''' + text[end:]
test.write_text(text)
PY
