from app.db import current_connection
from app.domain.order import OrderPlaced
from app.events.bus import subscribe
from app.repositories.sales_ledger_repository import SalesLedgerRepository


@subscribe(OrderPlaced)
def record_sale(event):
    SalesLedgerRepository(current_connection()).book(event.order_id, event.total_cents)
