import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.core.dependencies import get_current_user_token, TokenData, require_role

logger = logging.getLogger("notification_service")

router = APIRouter()


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_current_user_token),
):
    request_id = getattr(request.state, "request_id", "unknown")

    notification = Notification(**payload.model_dump())
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    logger.info(
        "request_id=%s action=create_notification notification_id=%s profile_id=%s type=%s",
        request_id, notification.id, notification.profile_id, notification.type,
    )
    return notification


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(require_role("admin")),
):
    result = await db.execute(select(Notification))
    return result.scalars().all()


@router.get("/profile/{profile_id}", response_model=list[NotificationResponse])
async def get_notifications_by_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(require_role("admin", "member")),
):
    result = await db.execute(
        select(Notification).where(Notification.profile_id == profile_id)
    )
    return result.scalars().all()
