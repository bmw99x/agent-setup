"""Loyalty account and the points rules."""

from dataclasses import dataclass

POINTS_PER_CURRENCY_UNIT = 1
BONUS_THRESHOLD_CENTS = 10_000
BONUS_POINTS = 25


class InsufficientPoints(Exception):
    pass


@dataclass
class LoyaltyAccount:
    customer_id: int
    points: int = 0

    def redeem(self, points):
        if points <= 0:
            raise ValueError("points to redeem must be positive")
        if points > self.points:
            raise InsufficientPoints(f"customer {self.customer_id} has {self.points} points, tried to redeem {points}")
        self.points -= points


def points_for(total_cents):
    points = total_cents // 100 * POINTS_PER_CURRENCY_UNIT
    if total_cents >= BONUS_THRESHOLD_CENTS:
        points += BONUS_POINTS
    return points
