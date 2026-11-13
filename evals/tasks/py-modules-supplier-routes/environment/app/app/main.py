from fastapi import FastAPI

from app.api.routes import router
from app.catalogue.products import ProductStore


def create_app() -> FastAPI:
    app = FastAPI(title="Catalogue API")
    app.state.products = ProductStore()
    app.include_router(router)
    return app


app = create_app()
