from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from reports.models import Order


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_account(self, account_id: int) -> list[Order]:
        query = (
            select(Order)
            .where(Order.account_id == account_id)
            .options(selectinload(Order.customer))
            .order_by(Order.placed_at, Order.id)
        )
        return list(self.session.scalars(query))
