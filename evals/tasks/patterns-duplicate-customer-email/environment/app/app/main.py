from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.customers.routes import router as customers_router
from app.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(customers_router)
