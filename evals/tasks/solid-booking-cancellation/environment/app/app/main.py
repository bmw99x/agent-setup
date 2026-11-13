from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bookings.routes import router as bookings_router
from app.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="StayHub", lifespan=lifespan)
    app.include_router(bookings_router)
    return app


app = create_app()
