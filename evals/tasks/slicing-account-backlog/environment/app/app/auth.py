from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status


async def current_customer_id(x_customer_id: Annotated[UUID | None, Header()] = None) -> UUID:
    """Resolved upstream by the gateway, which verifies the session and sets the header."""
    if x_customer_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return x_customer_id


async def require_staff(x_staff_role: Annotated[str | None, Header()] = None) -> str:
    if x_staff_role not in {"support", "admin"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return x_staff_role


CurrentCustomerId = Annotated[UUID, Depends(current_customer_id)]
StaffRole = Annotated[str, Depends(require_staff)]
