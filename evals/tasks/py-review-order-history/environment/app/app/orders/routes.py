from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderDatum
from app.orders.service import OrderNotFoundError, OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(session: Annotated[AsyncSession, Depends(get_session)]) -> OrderService:
    return OrderService(OrderRepository(session))


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.get("/{order_id}", response_model=OrderDatum)
async def read_order(order_id: UUID, service: OrderServiceDep) -> OrderDatum:
    try:
        order = await service.get_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Order not found") from exc
    return OrderDatum.model_validate(order)
