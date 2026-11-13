from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentCustomerId, StaffRole
from app.db import get_session
from app.orders.exceptions import OrderNotFoundError, OrderStateError
from app.orders.schemas import OrderDatum, ShipOrder
from app.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(session: Annotated[AsyncSession, Depends(get_session)]) -> OrderService:
    return OrderService(session)


Service = Annotated[OrderService, Depends(get_order_service)]


@router.get("", response_model=list[OrderDatum])
async def list_my_orders(customer_id: CurrentCustomerId, service: Service):
    return await service.list_for_customer(customer_id)


@router.get("/{order_id}", response_model=OrderDatum)
async def read_order(order_id: UUID, customer_id: CurrentCustomerId, service: Service):
    try:
        return await service.get_for_customer(order_id, customer_id)
    except OrderNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from error


@router.post("/{order_id}/cancel", response_model=OrderDatum)
async def cancel_order(order_id: UUID, customer_id: CurrentCustomerId, service: Service):
    try:
        return await service.cancel(order_id, customer_id)
    except OrderNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from error
    except OrderStateError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.post("/{order_id}/ship", response_model=OrderDatum)
async def ship_order(order_id: UUID, body: ShipOrder, _: StaffRole, service: Service):
    try:
        return await service.mark_shipped(order_id, body.tracking_number)
    except OrderNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from error
    except OrderStateError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.post("/{order_id}/deliver", response_model=OrderDatum)
async def deliver_order(order_id: UUID, _: StaffRole, service: Service):
    try:
        return await service.mark_delivered(order_id)
    except OrderNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from error
    except OrderStateError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
