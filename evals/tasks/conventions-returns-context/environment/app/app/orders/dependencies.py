from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.orders.repository import OrderRepository
from app.orders.service import OrderService


def get_order_service(session: Annotated[Session, Depends(get_session)]) -> OrderService:
    return OrderService(OrderRepository(session))
