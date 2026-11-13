from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price_pence: int
    image_key: str
