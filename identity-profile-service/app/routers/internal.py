"""
Internal endpoints for service-to-service communication.
These endpoints do not require JWT authentication but validate a shared secret.
"""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileResponse
from app.config import settings

logger = logging.getLogger("identity_profile_service")

router = APIRouter()


def verify_internal_secret(x_internal_secret: str = Header(None)) -> None:
    """Verify that the request includes the correct internal shared secret."""
    if not x_internal_secret or x_internal_secret != settings.SECRET_KEY:
        logger.warning("Internal endpoint access attempt with invalid secret")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal secret",
        )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile_internal(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_internal_secret),
):
    """
    Internal endpoint for service-to-service profile validation.
    Requires X-Internal-Secret header with the shared SECRET_KEY.
    Used by Session Service to validate profile existence before creating sessions.
    """
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile
