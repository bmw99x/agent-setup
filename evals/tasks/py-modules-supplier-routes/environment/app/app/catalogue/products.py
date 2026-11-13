from dataclasses import asdict, dataclass
from itertools import count


@dataclass(frozen=True)
class Product:
    id: int
    sku: str
    name: str
    price_pence: int

    def to_json(self) -> dict:
        return asdict(self)


class ProductStore:
    """In-memory product catalogue; swapped for the database-backed store in deployment."""

    def __init__(self) -> None:
        self._products: dict[int, Product] = {}
        self._ids = count(1)

    def add(self, sku: str, name: str, price_pence: int) -> Product:
        product = Product(id=next(self._ids), sku=sku, name=name, price_pence=price_pence)
        self._products[product.id] = product
        return product

    def get(self, product_id: int) -> Product | None:
        return self._products.get(product_id)

    def all(self) -> list[Product]:
        return list(self._products.values())
