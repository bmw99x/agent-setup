"""How many loyalty points an order earns."""

TIER_MULTIPLIER = {"standard": 1.0, "silver": 1.25, "gold": 1.5}


def points_for(amount_pence: int, tier: str) -> int:
    """One point per whole pound spent, scaled by the member's tier."""
    return int(amount_pence // 100 * TIER_MULTIPLIER[tier])
