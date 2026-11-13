from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.refunds.dependencies import get_refund_service
from app.refunds.service import RefundAlreadyIssuedError, RefundNotFoundError, RefundService

router = APIRouter(prefix="/refunds", tags=["refunds"])


class RefundDatum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: Decimal
    status: str


@router.post("/{refund_id}/issue", response_model=RefundDatum)
def issue_refund(refund_id: int, service: Annotated[RefundService, Depends(get_refund_service)]) -> RefundDatum:
    try:
        return RefundDatum.model_validate(service.issue(refund_id))
    except RefundNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Refund not found")
    except RefundAlreadyIssuedError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Refund already issued")
