#!/bin/bash
cat > /app/app/products/schemas.py <<'PY'
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.validation.schemas import AppBaseModel


class ProductDatum(AppBaseModel):
    id: UUID
    name: str
    sku: str
    price: Decimal
    description: str | None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class ProductUpsertDatum(AppBaseModel):
    name: str = Field(..., max_length=255)
    sku: str
    price: Decimal = Field(..., gt=0)
    description: str | None = None


@dataclass
class ProductUpsertMany:
    data: list[ProductUpsertDatum]
PY
