import uuid
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileResponse

logger = logging.getLogger("identity_profile_service")

router = APIRouter()


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def internal_get_profile(
    profile_id: uuid.UUID,
    request: Request,
    x_internal_service_secret: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", "unknown")

    if x_internal_service_secret != settings.INTERNAL_SERVICE_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal service secret")

    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    logger.info("request_id=%s action=internal_get_profile profile_id=%s", request_id, profile_id)
    return profile
