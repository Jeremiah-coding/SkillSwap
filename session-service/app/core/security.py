from datetime import datetime, timezone, timedelta
from typing import Any

from jose import jwt

from app.config import settings


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def create_service_token() -> str:
    """Generate a short-lived service JWT for internal inter-service calls."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "session-service",
        "role": "member",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
