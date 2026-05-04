import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionStatusUpdate, SessionResponse
from app.core.dependencies import get_current_user_token, TokenData, require_role
from app.clients import validate_profile, send_notification

logger = logging.getLogger("session_service")

router = APIRouter()

VALID_STATUSES = {"pending", "approved", "rejected", "cancelled"}


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_current_user_token),
):
    request_id = getattr(request.state, "request_id", "unknown")

    # Validate both profiles exist in Identity Service before persisting
    await validate_profile(str(payload.requester_profile_id), request_id)
    await validate_profile(str(payload.mentor_profile_id), request_id)

    session = Session(**payload.model_dump())
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info(
        "request_id=%s action=create_session session_id=%s requester=%s mentor=%s",
        request_id, session.id, session.requester_profile_id, session.mentor_profile_id,
    )

    # Notify both parties (non-blocking — failure is logged, not raised)
    await send_notification(
        profile_id=str(session.requester_profile_id),
        message=f"Your session request for '{session.requested_skill}' has been submitted.",
        notif_type="session_created",
        request_id=request_id,
    )
    await send_notification(
        profile_id=str(session.mentor_profile_id),
        message=f"You have a new session request for '{session.requested_skill}'.",
        notif_type="session_request_received",
        request_id=request_id,
    )

    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(require_role("admin")),
):
    query = select(Session)
    if status_filter:
        query = query.where(Session.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(get_current_user_token),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.patch("/{session_id}/status", response_model=SessionResponse)
async def update_session_status(
    session_id: uuid.UUID,
    payload: SessionStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token_data: TokenData = Depends(require_role("admin")),
):
    request_id = getattr(request.state, "request_id", "unknown")

    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {VALID_STATUSES}",
        )

    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    old_status = session.status
    session.status = payload.status
    await db.commit()
    await db.refresh(session)
    logger.info(
        "request_id=%s action=update_session_status session_id=%s old_status=%s new_status=%s",
        request_id, session.id, old_status, session.status,
    )

    # Notify requester when status changes
    status_messages = {
        "approved": f"Your session request for '{session.requested_skill}' has been approved.",
        "rejected": f"Your session request for '{session.requested_skill}' has been rejected.",
        "cancelled": f"Your session for '{session.requested_skill}' has been cancelled.",
    }
    if session.status in status_messages:
        await send_notification(
            profile_id=str(session.requester_profile_id),
            message=status_messages[session.status],
            notif_type=f"session_{session.status}",
            request_id=request_id,
        )

    return session
