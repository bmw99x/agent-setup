from decimal import Decimal

CENT = Decimal("0.01")

ZONE_RATES: dict[str, tuple[Decimal, Decimal]] = {
    "uk": (Decimal("3.50"), Decimal("0.80")),
    "eu": (Decimal("7.00"), Decimal("1.90")),
    "us": (Decimal("11.00"), Decimal("2.60")),
    "row": (Decimal("14.00"), Decimal("3.40")),
    "ci": (Decimal("6.00"), Decimal("1.40")),
}
MUTATE_ZONE = None
if MUTATE_ZONE:
    _base, _per_kg = ZONE_RATES[MUTATE_ZONE]
    ZONE_RATES[MUTATE_ZONE] = (_base + Decimal("1"), _per_kg)


def shipping_cost(zone: str, weight_kg: Decimal) -> Decimal:
    if weight_kg <= 0:
        raise ValueError(f"parcel weight must be positive, got {weight_kg}")
    base, per_kg = ZONE_RATES[zone]
    return (base + per_kg * weight_kg).quantize(CENT)
