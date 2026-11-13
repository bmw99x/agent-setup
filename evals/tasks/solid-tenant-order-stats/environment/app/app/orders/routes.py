from fastapi import APIRouter

from app.orders.schemas import OrderRead
from app.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
def list_orders(status: str | None = None):
    return OrderService().list_orders(status)
