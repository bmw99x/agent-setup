"""Gift cards (behind GIFT_CARDS_ENABLED, staging only for now)."""

import os
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class GiftCard:
    code: str
    balance: Decimal


_CARDS = {"GC-100": GiftCard("GC-100", Decimal("100.00")), "GC-25": GiftCard("GC-25", Decimal("25.00"))}


def gift_cards_enabled() -> bool:
    return os.environ.get("GIFT_CARDS_ENABLED", "false").lower() == "true"


def lookup(code: str) -> GiftCard | None:
    return _CARDS.get(code.strip().upper())


def apply_gift_card(total: Decimal, code: str) -> Decimal:
    card = lookup(code)
    return max(total - card.balance, Decimal("0"))
