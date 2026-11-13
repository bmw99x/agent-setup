"""Business logic for customers, orders and invoices."""

import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from app.repositories.customers import CustomerRepository
from app.repositories.invoices import InvoiceRepository
from app.repositories.orders import OrderRepository

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SUPPORTED_COUNTRIES = frozenset({"GB", "IE", "FR", "DE", "NL"})


class CustomerNotFoundError(Exception):
    """Raised when a customer id does not exist or is archived."""

    def __init__(self, customer_id: int) -> None:
        super().__init__(f"Customer {customer_id} not found")
        self.customer_id = customer_id


class DuplicateEmailError(Exception):
    """Raised when another customer already uses the email address."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Email {email} is already registered")
        self.email = email


class InvalidCustomerError(Exception):
    """Raised when customer details fail validation."""


@dataclass(frozen=True)
class Customer:
    id: int
    name: str
    email: str
    country: str


def _to_customer(row: sqlite3.Row) -> Customer:
    return Customer(id=row["id"], name=row["name"], email=row["email"], country=row["country"])


class CustomerService:
    """Registers and maintains customers."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._customers = CustomerRepository(connection)

    def register(self, name: str, email: str, country: str) -> Customer:
        """Register a new customer after validating their details."""
        name = name.strip()
        email = email.strip().lower()
        country = country.strip().upper()
        if not name:
            raise InvalidCustomerError("Name is required")
        if not EMAIL_PATTERN.match(email):
            raise InvalidCustomerError(f"Invalid email: {email}")
        if country not in SUPPORTED_COUNTRIES:
            raise InvalidCustomerError(f"Unsupported country: {country}")
        if self._customers.get_by_email(email) is not None:
            raise DuplicateEmailError(email)
        customer_id = self._customers.add(name, email, country)
        return Customer(id=customer_id, name=name, email=email, country=country)

    def get(self, customer_id: int) -> Customer:
        """Return an active customer or raise."""
        row = self._customers.get(customer_id)
        if row is None or row["archived"]:
            raise CustomerNotFoundError(customer_id)
        return _to_customer(row)

    def list_active(self) -> list[Customer]:
        """Return every customer that has not been archived."""
        return [_to_customer(row) for row in self._customers.list_active()]

    def change_email(self, customer_id: int, email: str) -> Customer:
        """Change a customer's email, keeping emails unique."""
        customer = self.get(customer_id)
        email = email.strip().lower()
        if not EMAIL_PATTERN.match(email):
            raise InvalidCustomerError(f"Invalid email: {email}")
        existing = self._customers.get_by_email(email)
        if existing is not None and existing["id"] != customer_id:
            raise DuplicateEmailError(email)
        self._customers.update_email(customer_id, email)
        return Customer(id=customer.id, name=customer.name, email=email, country=customer.country)

    def archive(self, customer_id: int) -> None:
        """Archive a customer so they no longer appear in listings."""
        self.get(customer_id)
        self._customers.archive(customer_id)

    def search(self, term: str) -> list[Customer]:
        """Return active customers whose name or email contains the term, case-insensitively."""
        needle = term.strip().lower()
        if not needle:
            return []
        return [
            customer
            for customer in self.list_active()
            if needle in customer.name.lower() or needle in customer.email.lower()
        ]

    def by_country(self) -> dict[str, list[Customer]]:
        """Group active customers by country code."""
        grouped: dict[str, list[Customer]] = {}
        for customer in self.list_active():
            grouped.setdefault(customer.country, []).append(customer)
        return grouped


# --- Orders -----------------------------------------------------------------

VAT_RATE = Decimal("0.20")
MAX_ORDER_LINES = 50
ORDER_STATUSES = ("draft", "placed", "paid", "cancelled")


class OrderNotFoundError(Exception):
    """Raised when an order id does not exist."""

    def __init__(self, order_id: int) -> None:
        super().__init__(f"Order {order_id} not found")
        self.order_id = order_id


class InvalidOrderStateError(Exception):
    """Raised when an order transition is not allowed from its current status."""

    def __init__(self, order_id: int, status: str, action: str) -> None:
        super().__init__(f"Cannot {action} order {order_id} in status {status}")
        self.order_id = order_id
        self.status = status
        self.action = action


class OrderLineError(Exception):
    """Raised when an order line is invalid."""


@dataclass(frozen=True)
class OrderLine:
    sku: str
    quantity: int
    unit_price_pence: int

    @property
    def total_pence(self) -> int:
        return self.quantity * self.unit_price_pence


@dataclass(frozen=True)
class OrderTotals:
    net_pence: int
    vat_pence: int

    @property
    def gross_pence(self) -> int:
        return self.net_pence + self.vat_pence


def _vat_for(net_pence: int) -> int:
    vat = (Decimal(net_pence) * VAT_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(vat)


def _now() -> str:
    return datetime.now(UTC).isoformat()


class OrderService:
    """Creates orders and moves them through their lifecycle."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._orders = OrderRepository(connection)
        self._customers = CustomerService(connection)

    def create_draft(self, customer_id: int) -> int:
        """Open an empty draft order for an active customer."""
        self._customers.get(customer_id)
        return self._orders.add(customer_id, "draft", _now())

    def status(self, order_id: int) -> str:
        """Return the order's current status."""
        return self._get(order_id)["status"]

    def add_line(self, order_id: int, sku: str, quantity: int, unit_price_pence: int) -> None:
        """Add a line to a draft order."""
        order = self._get(order_id)
        self._require_status(order, "draft", "add a line to")
        if quantity <= 0:
            raise OrderLineError("Quantity must be positive")
        if unit_price_pence < 0:
            raise OrderLineError("Unit price cannot be negative")
        if not sku.strip():
            raise OrderLineError("SKU is required")
        if len(self._orders.lines(order_id)) >= MAX_ORDER_LINES:
            raise OrderLineError(f"An order holds at most {MAX_ORDER_LINES} lines")
        self._orders.add_line(order_id, sku.strip().upper(), quantity, unit_price_pence)

    def remove_line(self, order_id: int, sku: str) -> None:
        """Remove every line for a SKU from a draft order."""
        order = self._get(order_id)
        self._require_status(order, "draft", "remove a line from")
        removed = self._orders.remove_line(order_id, sku.strip().upper())
        if removed == 0:
            raise OrderLineError(f"Order {order_id} has no line for {sku}")

    def lines(self, order_id: int) -> list[OrderLine]:
        """Return the order's lines in the order they were added."""
        self._get(order_id)
        return [
            OrderLine(sku=row["sku"], quantity=row["quantity"], unit_price_pence=row["unit_price_pence"])
            for row in self._orders.lines(order_id)
        ]

    def totals(self, order_id: int) -> OrderTotals:
        """Compute net and VAT totals for the order."""
        net = sum(line.total_pence for line in self.lines(order_id))
        return OrderTotals(net_pence=net, vat_pence=_vat_for(net))

    def place(self, order_id: int) -> None:
        """Place a draft order that has at least one line."""
        order = self._get(order_id)
        self._require_status(order, "draft", "place")
        if not self._orders.lines(order_id):
            raise OrderLineError("Cannot place an empty order")
        self._orders.set_status(order_id, "placed")

    def mark_paid(self, order_id: int) -> None:
        """Record payment for a placed order."""
        order = self._get(order_id)
        self._require_status(order, "placed", "mark paid")
        self._orders.set_status(order_id, "paid")

    def cancel(self, order_id: int) -> None:
        """Cancel a draft or placed order. Paid orders must be refunded instead."""
        order = self._get(order_id)
        if order["status"] not in ("draft", "placed"):
            raise InvalidOrderStateError(order_id, order["status"], "cancel")
        self._orders.set_status(order_id, "cancelled")

    def duplicate(self, order_id: int) -> int:
        """Open a new draft for the same customer with a copy of the order's lines."""
        order = self._get(order_id)
        new_order_id = self.create_draft(order["customer_id"])
        for line in self.lines(order_id):
            self._orders.add_line(new_order_id, line.sku, line.quantity, line.unit_price_pence)
        return new_order_id

    def change_quantity(self, order_id: int, sku: str, quantity: int) -> None:
        """Replace the quantity of a SKU on a draft order, keeping its unit price."""
        order = self._get(order_id)
        self._require_status(order, "draft", "change a line on")
        if quantity <= 0:
            raise OrderLineError("Quantity must be positive")
        sku = sku.strip().upper()
        matching = [line for line in self.lines(order_id) if line.sku == sku]
        if not matching:
            raise OrderLineError(f"Order {order_id} has no line for {sku}")
        self._orders.remove_line(order_id, sku)
        self._orders.add_line(order_id, sku, quantity, matching[0].unit_price_pence)

    def for_customer(self, customer_id: int) -> list[int]:
        """Return the ids of a customer's orders."""
        self._customers.get(customer_id)
        return [row["id"] for row in self._orders.for_customer(customer_id)]

    def _get(self, order_id: int) -> sqlite3.Row:
        row = self._orders.get(order_id)
        if row is None:
            raise OrderNotFoundError(order_id)
        return row

    @staticmethod
    def _require_status(order: sqlite3.Row, expected: str, action: str) -> None:
        if order["status"] != expected:
            raise InvalidOrderStateError(order["id"], order["status"], action)


# --- Invoices ---------------------------------------------------------------

INVOICE_NUMBER_PREFIX = "INV"
INVOICE_NUMBER_WIDTH = 6


class InvoiceNotFoundError(Exception):
    """Raised when an invoice id does not exist."""

    def __init__(self, invoice_id: int) -> None:
        super().__init__(f"Invoice {invoice_id} not found")
        self.invoice_id = invoice_id


class InvoiceAlreadyIssuedError(Exception):
    """Raised when an order already has an invoice."""

    def __init__(self, order_id: int) -> None:
        super().__init__(f"Order {order_id} already has an invoice")
        self.order_id = order_id


class InvoiceVoidedError(Exception):
    """Raised when acting on an invoice that has been voided."""


@dataclass(frozen=True)
class Invoice:
    id: int
    order_id: int
    number: str
    net_pence: int
    vat_pence: int
    issued_at: str
    voided: bool

    @property
    def gross_pence(self) -> int:
        return self.net_pence + self.vat_pence


@dataclass(frozen=True)
class VatSummary:
    invoice_count: int
    net_pence: int
    vat_pence: int


def _to_invoice(row: sqlite3.Row) -> Invoice:
    return Invoice(
        id=row["id"],
        order_id=row["order_id"],
        number=row["number"],
        net_pence=row["net_pence"],
        vat_pence=row["vat_pence"],
        issued_at=row["issued_at"],
        voided=bool(row["voided"]),
    )


def _format_number(sequence: int) -> str:
    return f"{INVOICE_NUMBER_PREFIX}-{sequence:0{INVOICE_NUMBER_WIDTH}d}"


class InvoiceService:
    """Issues invoices for paid orders and reports VAT."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._invoices = InvoiceRepository(connection)
        self._orders = OrderService(connection)

    def issue(self, order_id: int, issued_at: str | None = None) -> Invoice:
        """Issue the invoice for a paid order. An order gets at most one invoice."""
        status = self._orders.status(order_id)
        if status != "paid":
            raise InvalidOrderStateError(order_id, status, "invoice")
        if self._invoices.for_order(order_id) is not None:
            raise InvoiceAlreadyIssuedError(order_id)
        totals = self._orders.totals(order_id)
        number = _format_number(self._invoices.count() + 1)
        issued = issued_at or _now()
        invoice_id = self._invoices.add(order_id, number, totals.net_pence, totals.vat_pence, issued)
        return self.get(invoice_id)

    def get(self, invoice_id: int) -> Invoice:
        """Return an invoice or raise."""
        row = self._invoices.get(invoice_id)
        if row is None:
            raise InvoiceNotFoundError(invoice_id)
        return _to_invoice(row)

    def for_order(self, order_id: int) -> Invoice | None:
        """Return the order's invoice, if one was issued."""
        row = self._invoices.for_order(order_id)
        return None if row is None else _to_invoice(row)

    def void(self, invoice_id: int) -> Invoice:
        """Void an invoice. Voiding twice is an error."""
        invoice = self.get(invoice_id)
        if invoice.voided:
            raise InvoiceVoidedError(f"Invoice {invoice.number} is already void")
        self._invoices.void(invoice_id)
        return self.get(invoice_id)

    def vat_summary(self, start: str, end: str) -> VatSummary:
        """Sum net and VAT over non-void invoices issued in [start, end)."""
        rows = self._invoices.issued_between(start, end)
        return VatSummary(
            invoice_count=len(rows),
            net_pence=sum(row["net_pence"] for row in rows),
            vat_pence=sum(row["vat_pence"] for row in rows),
        )

    def vat_check(self, invoice_id: int) -> bool:
        """True when the stored VAT matches VAT_RATE applied to the stored net."""
        invoice = self.get(invoice_id)
        if invoice.voided:
            raise InvoiceVoidedError(f"Invoice {invoice.number} is void")
        return invoice.vat_pence == _vat_for(invoice.net_pence)

    def statement(self, customer_id: int) -> list[Invoice]:
        """Return the customer's non-void invoices, oldest first."""
        invoices = []
        for order_id in self._orders.for_customer(customer_id):
            invoice = self.for_order(order_id)
            if invoice is not None and not invoice.voided:
                invoices.append(invoice)
        return sorted(invoices, key=lambda invoice: invoice.issued_at)
