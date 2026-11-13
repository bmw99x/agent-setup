FLAT_FEE_PENCE = 395
PER_KG_OVER_LIMIT_PENCE = 120
FLAT_LIMIT_KG = 2


def delivery_fee(weight_kg: float) -> int:
    if weight_kg <= FLAT_LIMIT_KG:
        return FLAT_FEE_PENCE
    extra_kg = -(-(weight_kg - FLAT_LIMIT_KG) // 1)
    return FLAT_FEE_PENCE + int(extra_kg) * PER_KG_OVER_LIMIT_PENCE
