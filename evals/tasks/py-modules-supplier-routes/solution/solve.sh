#!/bin/bash
# Generic gzip helper in app/api/gzip.py; one routes module per resource under app/api/routes/
# (namespace package, no __init__.py) and a small app/api/router.py that includes them.
set -euo pipefail
cd /app
mkdir -p app/api/routes_tmp
cat > app/api/gzip.py <<'PY'
import gzip
import json

from fastapi import Response


def gzip_json(payload: object) -> Response:
    body = gzip.compress(json.dumps(payload, separators=(",", ":")).encode())
    return Response(content=body, media_type="application/json", headers={"Content-Encoding": "gzip"})
PY
cat > app/api/routes_tmp/products.py <<'PY'
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.api.gzip import gzip_json
from app.catalogue.products import ProductStore

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    price_pence: int = Field(gt=0)


def _store(request: Request) -> ProductStore:
    return request.app.state.products


@router.get("")
def list_products(request: Request) -> Response:
    return gzip_json([product.to_json() for product in _store(request).all()])


@router.get("/{product_id}")
def get_product(product_id: int, request: Request) -> dict:
    product = _store(request).get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.to_json()


@router.post("", status_code=201)
def create_product(body: ProductCreate, request: Request) -> dict:
    return _store(request).add(body.sku, body.name, body.price_pence).to_json()
PY
cat > app/api/routes_tmp/suppliers.py <<'PY'
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.api.gzip import gzip_json
from app.catalogue.suppliers import SupplierStore

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=320)
    lead_time_days: int = Field(ge=0)


def _store(request: Request) -> SupplierStore:
    return request.app.state.suppliers


@router.get("")
def list_suppliers(request: Request) -> Response:
    return gzip_json([supplier.to_json() for supplier in _store(request).all()])


@router.get("/{supplier_id}")
def get_supplier(supplier_id: int, request: Request) -> dict:
    supplier = _store(request).get(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier.to_json()


@router.post("", status_code=201)
def create_supplier(body: SupplierCreate, request: Request) -> dict:
    return _store(request).add(body.name, body.email, body.lead_time_days).to_json()
PY
rm app/api/routes.py
mv app/api/routes_tmp app/api/routes
cat > app/api/router.py <<'PY'
from fastapi import APIRouter

from app.api.routes import products, suppliers

router = APIRouter()
router.include_router(products.router)
router.include_router(suppliers.router)
PY
cat > app/catalogue/suppliers.py <<'PY'
from dataclasses import asdict, dataclass
from itertools import count


@dataclass(frozen=True)
class Supplier:
    id: int
    name: str
    email: str
    lead_time_days: int

    def to_json(self) -> dict:
        return asdict(self)


class SupplierStore:
    """In-memory supplier list; swapped for the database-backed store in deployment."""

    def __init__(self) -> None:
        self._suppliers: dict[int, Supplier] = {}
        self._ids = count(1)

    def add(self, name: str, email: str, lead_time_days: int) -> Supplier:
        supplier = Supplier(id=next(self._ids), name=name, email=email, lead_time_days=lead_time_days)
        self._suppliers[supplier.id] = supplier
        return supplier

    def get(self, supplier_id: int) -> Supplier | None:
        return self._suppliers.get(supplier_id)

    def all(self) -> list[Supplier]:
        return list(self._suppliers.values())
PY
cat > app/main.py <<'PY'
from fastapi import FastAPI

from app.api.router import router
from app.catalogue.products import ProductStore
from app.catalogue.suppliers import SupplierStore


def create_app() -> FastAPI:
    app = FastAPI(title="Catalogue API")
    app.state.products = ProductStore()
    app.state.suppliers = SupplierStore()
    app.include_router(router)
    return app


app = create_app()
PY
cat > tests/test_suppliers.py <<'PY'
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_create_and_get_supplier(client):
    created = client.post("/suppliers", json={"name": "Acme", "email": "a@acme.test", "lead_time_days": 3})
    assert created.status_code == 201
    assert client.get(f"/suppliers/{created.json()['id']}").json()["name"] == "Acme"


def test_supplier_list_is_gzipped(client):
    client.post("/suppliers", json={"name": "Acme", "email": "a@acme.test", "lead_time_days": 3})
    response = client.get("/suppliers")
    assert response.headers["content-encoding"] == "gzip"
    assert len(response.json()) == 1
PY
