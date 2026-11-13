from reports.orders_report import render_orders_report
from reports.repository import OrderRepository


def test_orders_report_matches_snapshot(db_session, seeded_account, snapshot):
    assert render_orders_report(OrderRepository(db_session), seeded_account) == snapshot("orders")


def test_orders_report_query_count(db_session, seeded_account, assert_max_queries):
    with assert_max_queries(3):
        render_orders_report(OrderRepository(db_session), seeded_account)
