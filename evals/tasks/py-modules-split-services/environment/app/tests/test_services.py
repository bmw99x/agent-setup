import pytest

from app.db import connect
from app.services import (
    CustomerNotFoundError,
    CustomerService,
    DuplicateEmailError,
    InvalidCustomerError,
    InvalidOrderStateError,
    InvoiceAlreadyIssuedError,
    InvoiceService,
    InvoiceVoidedError,
    OrderLineError,
    OrderService,
)


@pytest.fixture
def connection():
    return connect()


@pytest.fixture
def customer(connection):
    return CustomerService(connection).register("Ada Lovelace", "ADA@example.com ", "gb")


def _paid_order(connection, customer_id: int) -> int:
    orders = OrderService(connection)
    order_id = orders.create_draft(customer_id)
    orders.add_line(order_id, "kettle", 2, 1999)
    orders.add_line(order_id, "mug", 4, 450)
    orders.place(order_id)
    orders.mark_paid(order_id)
    return order_id


def test_register_normalises_details(customer):
    assert customer.email == "ada@example.com"
    assert customer.country == "GB"


def test_register_rejects_duplicate_email(connection, customer):
    with pytest.raises(DuplicateEmailError):
        CustomerService(connection).register("Ada Two", "ada@example.com", "IE")


def test_register_rejects_unsupported_country(connection):
    with pytest.raises(InvalidCustomerError):
        CustomerService(connection).register("Bob", "bob@example.com", "US")


def test_archived_customer_is_not_found(connection, customer):
    customers = CustomerService(connection)
    customers.archive(customer.id)
    with pytest.raises(CustomerNotFoundError):
        customers.get(customer.id)
    assert customers.list_active() == []


def test_change_email(connection, customer):
    updated = CustomerService(connection).change_email(customer.id, "lovelace@example.com")
    assert updated.email == "lovelace@example.com"


def test_search_and_group(connection, customer):
    customers = CustomerService(connection)
    customers.register("Bob", "bob@example.ie", "IE")
    assert [c.name for c in customers.search("ADA")] == ["Ada Lovelace"]
    assert sorted(customers.by_country()) == ["GB", "IE"]


def test_order_totals_include_vat(connection, customer):
    orders = OrderService(connection)
    order_id = orders.create_draft(customer.id)
    orders.add_line(order_id, "kettle", 2, 1999)
    totals = orders.totals(order_id)
    assert totals.net_pence == 3998
    assert totals.vat_pence == 800
    assert totals.gross_pence == 4798


def test_cannot_place_empty_order(connection, customer):
    orders = OrderService(connection)
    order_id = orders.create_draft(customer.id)
    with pytest.raises(OrderLineError):
        orders.place(order_id)


def test_cannot_add_line_after_placing(connection, customer):
    orders = OrderService(connection)
    order_id = orders.create_draft(customer.id)
    orders.add_line(order_id, "kettle", 1, 1999)
    orders.place(order_id)
    with pytest.raises(InvalidOrderStateError):
        orders.add_line(order_id, "mug", 1, 450)


def test_cannot_cancel_paid_order(connection, customer):
    order_id = _paid_order(connection, customer.id)
    with pytest.raises(InvalidOrderStateError):
        OrderService(connection).cancel(order_id)


def test_change_quantity_and_duplicate(connection, customer):
    orders = OrderService(connection)
    order_id = orders.create_draft(customer.id)
    orders.add_line(order_id, "kettle", 1, 1999)
    orders.change_quantity(order_id, "KETTLE", 3)
    copy_id = orders.duplicate(order_id)
    assert [(line.sku, line.quantity) for line in orders.lines(copy_id)] == [("KETTLE", 3)]


def test_issue_invoice_numbers_sequentially(connection, customer):
    invoices = InvoiceService(connection)
    first = invoices.issue(_paid_order(connection, customer.id), issued_at="2026-01-05T10:00:00")
    second = invoices.issue(_paid_order(connection, customer.id), issued_at="2026-01-06T10:00:00")
    assert (first.number, second.number) == ("INV-000001", "INV-000002")
    assert first.gross_pence == 5798 + 1160


def test_invoice_only_once(connection, customer):
    order_id = _paid_order(connection, customer.id)
    invoices = InvoiceService(connection)
    invoices.issue(order_id)
    with pytest.raises(InvoiceAlreadyIssuedError):
        invoices.issue(order_id)


def test_cannot_invoice_unpaid_order(connection, customer):
    orders = OrderService(connection)
    order_id = orders.create_draft(customer.id)
    with pytest.raises(InvalidOrderStateError):
        InvoiceService(connection).issue(order_id)


def test_void_and_vat_summary(connection, customer):
    invoices = InvoiceService(connection)
    kept = invoices.issue(_paid_order(connection, customer.id), issued_at="2026-02-01T09:00:00")
    voided = invoices.issue(_paid_order(connection, customer.id), issued_at="2026-02-02T09:00:00")
    invoices.void(voided.id)
    with pytest.raises(InvoiceVoidedError):
        invoices.void(voided.id)
    summary = invoices.vat_summary("2026-02-01", "2026-03-01")
    assert summary.invoice_count == 1
    assert summary.vat_pence == kept.vat_pence
    assert invoices.vat_check(kept.id)
    assert [invoice.id for invoice in invoices.statement(customer.id)] == [kept.id]
