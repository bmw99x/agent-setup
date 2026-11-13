from sqlalchemy.orm import Session

from app.orders.models import Order


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id)

    def add(self, order: Order) -> Order:
        self.session.add(order)
        self.session.commit()
        return order
