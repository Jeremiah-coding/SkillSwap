import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine, Base
from app.middleware.request_id import RequestIDMiddleware

# Ensure models are registered with Base before create_all
from app.models import user, profile  # noqa: F401

from app.routers import auth, profiles, mfa, internal

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Identity & Profile Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(RequestIDMiddleware)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(mfa.router, prefix="/api/v1/mfa", tags=["mfa"])
app.include_router(internal.router, prefix="/internal/profiles", tags=["internal"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "identity-profile-service"}
