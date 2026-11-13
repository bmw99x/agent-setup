from fastapi import FastAPI

from app.articles.routes import router

app = FastAPI(title="Newsroom")
app.include_router(router)
