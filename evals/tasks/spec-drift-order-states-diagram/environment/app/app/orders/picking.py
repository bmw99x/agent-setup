"""Warehouse picking: which zone a SKU is picked from."""

FAST_MOVER_ZONE = "A"


def pick_zone(sku_velocity_per_day: float) -> str:
    return FAST_MOVER_ZONE if sku_velocity_per_day >= 20 else "C"
