from fastapi import FastAPI

from app.refunds.routes import router as refunds_router

app = FastAPI(title="Payments API")
app.include_router(refunds_router)
