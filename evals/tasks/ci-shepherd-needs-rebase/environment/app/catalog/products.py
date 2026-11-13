"""Products in the catalogue."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price_pence: int


PRODUCTS = [
    Product("TEA-001", "Earl Grey tea", 450),
    Product("TEA-002", "English breakfast tea", 399),
    Product("COF-001", "Colombian coffee beans", 899),
    Product("MUG-001", "Enamel mug", 1200),
]
