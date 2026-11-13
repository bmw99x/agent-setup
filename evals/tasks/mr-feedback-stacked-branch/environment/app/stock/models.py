"""Catalogue items and their stock levels."""

from dataclasses import dataclass
from datetime import date, timedelta

CYCLE_COUNT_PERIOD = timedelta(days=90)


@dataclass(frozen=True)
class Item:
    sku: str
    on_hand: int
    reorder_level: int
    last_counted: date
    discontinued: bool = False
