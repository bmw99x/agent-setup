def order_total(lines: list[tuple[int, float]]) -> float:
    return sum(qty * price for qty, price in lines)
