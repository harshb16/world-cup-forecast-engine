"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.env import load_local_env

load_local_env()

from app.api.routes import router
from app.core.config import API_TITLE
from app.services.runtime_store import init_runtime_store

LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_runtime_store()
    yield


app = FastAPI(title=API_TITLE, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_FRONTEND_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-WCO-Admin-Key"],
)
app.include_router(router)
