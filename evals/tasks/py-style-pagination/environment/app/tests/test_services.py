from app.customers.service import list_customers
from app.invoices.service import list_invoices


def test_list_customers_returns_everyone():
    assert len(list_customers()) == 300


def test_list_invoices_returns_everything():
    assert len(list_invoices()) == 500
