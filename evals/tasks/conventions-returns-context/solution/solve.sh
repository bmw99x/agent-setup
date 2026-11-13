#!/bin/bash
set -euo pipefail
cd /app
mkdir -p app/returns
touch app/returns/__init__.py
cat > app/returns/enums.py <<'PY'
import enum


class ReturnStatus(str, enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
PY
cat > app/returns/models.py <<'PY'
from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.returns.enums import ReturnStatus


class Return(Base):
    __tablename__ = "returns"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    reason: Mapped[str] = mapped_column(String(1000))
    status: Mapped[ReturnStatus] = mapped_column(Enum(ReturnStatus), default=ReturnStatus.REQUESTED)
PY
cat > app/returns/repository.py <<'PY'
from sqlalchemy.orm import Session

from app.returns.models import Return


class ReturnRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, return_id: int) -> Return | None:
        return self.session.get(Return, return_id)

    def save(self, item: Return) -> Return:
        self.session.add(item)
        self.session.commit()
        return item
PY
cat > app/returns/service.py <<'PY'
from app.orders.repository import OrderRepository
from app.returns.enums import ReturnStatus
from app.returns.models import Return
from app.returns.repository import ReturnRepository


class ReturnNotFoundError(Exception):
    pass


class ReturnOrderNotFoundError(Exception):
    pass


class ReturnAlreadyDecidedError(Exception):
    pass


class ReturnService:
    def __init__(self, repository: ReturnRepository, orders: OrderRepository) -> None:
        self.repository = repository
        self.orders = orders

    def open(self, order_id: int, reason: str) -> Return:
        if self.orders.get(order_id) is None:
            raise ReturnOrderNotFoundError(order_id)
        return self.repository.save(Return(order_id=order_id, reason=reason, status=ReturnStatus.REQUESTED))

    def get(self, return_id: int) -> Return:
        item = self.repository.get(return_id)
        if item is None:
            raise ReturnNotFoundError(return_id)
        return item

    def decide(self, return_id: int, outcome: ReturnStatus) -> Return:
        item = self.get(return_id)
        if item.status is not ReturnStatus.REQUESTED:
            raise ReturnAlreadyDecidedError(return_id)
        item.status = outcome
        return self.repository.save(item)
PY
cat > app/returns/schemas.py <<'PY'
from pydantic import BaseModel, ConfigDict

from app.returns.enums import ReturnStatus


class ReturnDatum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    reason: str
    status: ReturnStatus


class UpsertReturnDatum(BaseModel):
    order_id: int
    reason: str
PY
cat > app/returns/dependencies.py <<'PY'
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.orders.repository import OrderRepository
from app.returns.repository import ReturnRepository
from app.returns.service import ReturnService


def get_return_service(session: Annotated[Session, Depends(get_session)]) -> ReturnService:
    return ReturnService(ReturnRepository(session), OrderRepository(session))
PY
cat > app/returns/routes.py <<'PY'
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_staff
from app.returns.dependencies import get_return_service
from app.returns.enums import ReturnStatus
from app.returns.schemas import ReturnDatum, UpsertReturnDatum
from app.returns.service import (
    ReturnAlreadyDecidedError,
    ReturnNotFoundError,
    ReturnOrderNotFoundError,
    ReturnService,
)

router = APIRouter(prefix="/returns", tags=["returns"], dependencies=[Depends(require_staff)])
Service = Annotated[ReturnService, Depends(get_return_service)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReturnDatum)
def open_return(body: UpsertReturnDatum, service: Service) -> ReturnDatum:
    try:
        return ReturnDatum.model_validate(service.open(body.order_id, body.reason))
    except ReturnOrderNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")


@router.get("/{return_id}", response_model=ReturnDatum)
def get_return(return_id: int, service: Service) -> ReturnDatum:
    try:
        return ReturnDatum.model_validate(service.get(return_id))
    except ReturnNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Return not found")


def _decide(service: ReturnService, return_id: int, outcome: ReturnStatus) -> ReturnDatum:
    try:
        return ReturnDatum.model_validate(service.decide(return_id, outcome))
    except ReturnNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Return not found")
    except ReturnAlreadyDecidedError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Return already decided")


@router.post("/{return_id}/approve", response_model=ReturnDatum)
def approve_return(return_id: int, service: Service) -> ReturnDatum:
    return _decide(service, return_id, ReturnStatus.APPROVED)


@router.post("/{return_id}/reject", response_model=ReturnDatum)
def reject_return(return_id: int, service: Service) -> ReturnDatum:
    return _decide(service, return_id, ReturnStatus.REJECTED)
PY
cat > app/all_models/__init__.py <<'PY'
"""Every ORM model, imported so `Base.metadata` knows all tables."""

from app.orders.models import Order
from app.returns.models import Return

__all__ = ["Order", "Return"]
PY
cat > app/api/router.py <<'PY'
from fastapi import APIRouter

from app.orders.routes import router as orders_router
from app.returns.routes import router as returns_router

api_router = APIRouter()
api_router.include_router(orders_router)
api_router.include_router(returns_router)
PY
