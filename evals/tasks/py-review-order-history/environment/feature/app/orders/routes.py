from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderDatum, OrderHistoryDatum, OrderWithLinesDatum
from app.orders.service import OrderNotFoundError, OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrderService:
    return OrderService(OrderRepository(session), session)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.get("/{order_id}", response_model=OrderDatum)
async def read_order(order_id: UUID, service: OrderServiceDep) -> OrderDatum:
    try:
        order = await service.get_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Order not found") from exc
    return OrderDatum.model_validate(order)


@router.get("/{order_id}/lines", response_model=OrderWithLinesDatum)
async def read_order_with_lines(order_id: UUID, service: OrderServiceDep) -> OrderWithLinesDatum:
    try:
        order = await service.get_order_with_lines(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Order not found") from exc
    return OrderWithLinesDatum.model_validate(order)


@router.get("/customers/{customer_id}/history", response_model=OrderHistoryDatum)
async def read_order_history(customer_id: UUID, service: OrderServiceDep) -> OrderHistoryDatum:
    history = await service.order_history(customer_id)
    return OrderHistoryDatum.from_history(history)
