from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.orders.routes import router as orders_router
from app.tenancy import TENANT_HEADER, UnknownTenantError, current_tenant


def create_app() -> FastAPI:
    app = FastAPI(title="Shopfloor")

    @app.middleware("http")
    async def bind_tenant(request: Request, call_next):
        tenant = request.headers.get(TENANT_HEADER)
        if not tenant:
            return JSONResponse({"detail": f"{TENANT_HEADER} header required"}, status_code=400)
        token = current_tenant.set(tenant)
        try:
            return await call_next(request)
        finally:
            current_tenant.reset(token)

    @app.exception_handler(UnknownTenantError)
    async def unknown_tenant(_: Request, error: UnknownTenantError):
        return JSONResponse({"detail": str(error)}, status_code=404)

    app.include_router(orders_router)
    return app


app = create_app()
