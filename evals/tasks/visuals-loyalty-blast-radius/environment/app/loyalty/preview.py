from loyalty import points


def preview_points(basket_pence: int, tier: str) -> str:
    """The 'you will earn N points' line shown on the basket page."""
    return f"You will earn {points.points_for(basket_pence, tier)} points"
