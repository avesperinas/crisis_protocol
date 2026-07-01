from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth as auth_router
from src.api import games as games_router
from src.api import messages as messages_router
from src.api import pacts as pacts_router
from src.api import scenarios as scenarios_router
from src.api import social as social_router
from src.api import turns as turns_router
from src.api import ws as ws_router
from src.config import settings
from src.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


app = FastAPI(title="Crisis Protocol API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(scenarios_router.router)
app.include_router(games_router.router)
app.include_router(turns_router.router)
app.include_router(pacts_router.router)
app.include_router(messages_router.router)
app.include_router(social_router.router)
app.include_router(ws_router.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
