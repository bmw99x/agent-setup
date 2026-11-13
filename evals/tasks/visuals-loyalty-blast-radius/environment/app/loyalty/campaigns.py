from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

from loyalty.ledger import PointsLedger
from loyalty.points import points_for


def build_rules() -> dict[str, Callable[[int], int]]:
    """Bonus rules by campaign code; each maps a basket total in pence to bonus points."""
    return {
        "DOUBLEGOLD": partial(points_for, tier="gold"),
        "FLAT50": lambda _amount: 50,
    }


@dataclass
class BonusCampaign:
    ledger: PointsLedger

    def apply(self, code: str, member_id: str, amount_pence: int) -> int:
        rule = build_rules()[code]
        bonus = rule(amount_pence)
        self.ledger.credit(member_id, bonus)
        return bonus
