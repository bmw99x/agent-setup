from fastapi import FastAPI

from app.customers.routes import router as customers_router
from app.orders.routes import router as orders_router

app = FastAPI(title="shop-api")
app.include_router(customers_router)
app.include_router(orders_router)
