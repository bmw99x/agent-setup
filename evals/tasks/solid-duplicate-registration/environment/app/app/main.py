from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app.members.routes import router as members_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Clubhouse", lifespan=lifespan)
    app.include_router(members_router)
    return app


app = create_app()
