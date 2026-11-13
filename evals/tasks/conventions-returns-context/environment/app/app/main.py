from fastapi import FastAPI

import app.all_models  # noqa: F401  (registers every table on Base.metadata)
from app.api.router import api_router
from app.db import Base, engine

Base.metadata.create_all(engine)

app = FastAPI(title="Shop API")
app.include_router(api_router)
