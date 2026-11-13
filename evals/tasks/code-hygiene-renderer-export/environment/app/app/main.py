from fastapi import FastAPI

from app.reports.routes import router as reports_router

app = FastAPI(title="Reports")
app.include_router(reports_router)
