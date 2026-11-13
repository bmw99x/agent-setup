from stock.items import Item


def format_report(items: list[Item]) -> str:
    return "\n".join(f"{item.sku}\t{item.name}\t{item.quantity}" for item in items)
