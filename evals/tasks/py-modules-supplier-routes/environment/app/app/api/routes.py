import gzip
import json

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.catalogue.products import ProductStore

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    price_pence: int = Field(gt=0)


def _gzip_json(payload: object) -> Response:
    body = gzip.compress(json.dumps(payload, separators=(",", ":")).encode())
    return Response(content=body, media_type="application/json", headers={"Content-Encoding": "gzip"})


def _store(request: Request) -> ProductStore:
    return request.app.state.products


@router.get("")
def list_products(request: Request) -> Response:
    return _gzip_json([product.to_json() for product in _store(request).all()])


@router.get("/{product_id}")
def get_product(product_id: int, request: Request) -> dict:
    product = _store(request).get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.to_json()


@router.post("", status_code=201)
def create_product(body: ProductCreate, request: Request) -> dict:
    return _store(request).add(body.sku, body.name, body.price_pence).to_json()
