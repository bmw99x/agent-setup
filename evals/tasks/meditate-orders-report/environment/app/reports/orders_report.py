import csv
import io

from reports.repository import OrderRepository


def render_orders_report(repository: OrderRepository, account_id: int) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["order_id", "placed_at", "customer", "total"])
    for order in repository.list_for_account(account_id):
        writer.writerow([order.id, order.placed_at.isoformat(), order.customer.name, order.total])
    return buffer.getvalue()
