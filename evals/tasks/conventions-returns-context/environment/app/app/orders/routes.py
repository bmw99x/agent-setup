from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_staff
from app.auth.tokens import User
from app.orders.dependencies import get_order_service
from app.orders.schemas import OrderDatum, UpsertOrderDatum
from app.orders.service import OrderNotFoundError, OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderDatum)
def place_order(
    body: UpsertOrderDatum,
    service: Annotated[OrderService, Depends(get_order_service)],
    _: Annotated[User, Depends(require_staff)],
) -> OrderDatum:
    return OrderDatum.model_validate(service.place(body.customer_email, body.total))


@router.get("/{order_id}", response_model=OrderDatum)
def get_order(
    order_id: int,
    service: Annotated[OrderService, Depends(get_order_service)],
    _: Annotated[User, Depends(require_staff)],
) -> OrderDatum:
    try:
        return OrderDatum.model_validate(service.get(order_id))
    except OrderNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
