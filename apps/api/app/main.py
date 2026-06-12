"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import API_TITLE

app = FastAPI(title=API_TITLE)
app.include_router(router)
