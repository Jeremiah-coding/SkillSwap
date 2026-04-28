import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine, Base
from app.middleware.request_id import RequestIDMiddleware
from app.models import notification  # noqa: F401
from app.routers import notifications

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


app = FastAPI(title="Notification Service", version="1.0.0", lifespan=lifespan)

app.add_middleware(RequestIDMiddleware)

app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "notification-service"}
