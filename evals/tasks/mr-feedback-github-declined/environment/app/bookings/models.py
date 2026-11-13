"""Booking records. Amounts are integer pence; times are timezone-aware UTC."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Booking:
    reference: str
    total_pence: int
    check_in: datetime
    member: bool = False
