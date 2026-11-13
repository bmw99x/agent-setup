from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from orders import api
from orders.models import Base, Order

ROWS = [
    ("A-001", "paid", "Ada Lovelace", "120.00", False),
    ("A-002", "pending", "Alan Turing", "15.50", False),
    ("A-003", "paid", "Grace Hopper", "80.00", True),
    ("A-004", "refunded", "Ada Byron", "42.00", False),
    ("A-005", "paid", "Edsger Dijkstra", "300.00", False),
]


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all(
            Order(reference=r, status=st, customer_name=c, total=Decimal(t), is_archived=a)
            for r, st, c, t, a in ROWS
        )
        s.commit()
        yield s


def refs(result: dict) -> list[str]:
    return [item["reference"] for item in result["items"]]


def test_default_listing_hides_archived(session):
    result = api.list_orders(session, {})
    assert refs(result) == ["A-001", "A-002", "A-004", "A-005"]
    assert result["total"] == 4


def test_include_archived(session):
    assert api.list_orders(session, {"includeArchived": "true"})["total"] == 5


def test_status_filter(session):
    result = api.list_orders(session, {"status": "paid,refunded"})
    assert refs(result) == ["A-001", "A-004", "A-005"]


def test_customer_name_is_case_insensitive_substring(session):
    assert refs(api.list_orders(session, {"customerName": "ada"})) == ["A-001", "A-004"]


def test_total_range(session):
    result = api.list_orders(session, {"minTotal": "40", "maxTotal": "150"})
    assert refs(result) == ["A-001", "A-004"]
    assert result["total"] == 2


def test_pagination(session):
    result = api.list_orders(session, {"page": "2", "pageSize": "2"})
    assert refs(result) == ["A-004", "A-005"]
    assert result["total"] == 4
    assert result["page"] == 2


def test_inverted_total_range_is_rejected(session):
    with pytest.raises(ValueError):
        api.list_orders(session, {"minTotal": "100", "maxTotal": "10"})


def test_export_csv(session):
    text = api.export_orders_csv(session, {"status": "paid", "includeArchived": "true"})
    assert text.splitlines() == [
        "reference,status,customer,total",
        "A-001,paid,Ada Lovelace,120.00",
        "A-003,paid,Grace Hopper,80.00",
        "A-005,paid,Edsger Dijkstra,300.00",
    ]
