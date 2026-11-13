class OrderNotFoundError(Exception):
    pass


class OrderStateError(Exception):
    """The order is not in a status that allows the requested change."""
