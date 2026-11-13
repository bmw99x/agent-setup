from decimal import Decimal

CENT = Decimal("0.01")

# zone code -> (base charge, charge per kg), GBP
ZONE_RATES: dict[str, tuple[Decimal, Decimal]] = {
    "uk": (Decimal("3.50"), Decimal("0.80")),
    "eu": (Decimal("7.00"), Decimal("1.90")),
    "us": (Decimal("11.00"), Decimal("2.60")),
    "row": (Decimal("14.00"), Decimal("3.40")),
}


def shipping_cost(zone: str, weight_kg: Decimal) -> Decimal:
    """Price a parcel of `weight_kg` sent to `zone`."""
    if weight_kg <= 0:
        raise ValueError(f"parcel weight must be positive, got {weight_kg}")
    base, per_kg = ZONE_RATES[zone]
    return (base + per_kg * weight_kg).quantize(CENT)
