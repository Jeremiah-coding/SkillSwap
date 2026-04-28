import logging

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user

logger = logging.getLogger("identity_profile_service")

router = APIRouter()


class TOTPSetupResponse(BaseModel):
    totp_secret: str
    totp_uri: str


class TOTPVerifyRequest(BaseModel):
    code: str


class TOTPDisableRequest(BaseModel):
    code: str


@router.post("/setup", response_model=TOTPSetupResponse)
async def setup_mfa(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", "unknown")
    if current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP already enabled")

    secret = pyotp.random_base32()
    current_user.totp_secret = secret
    await db.commit()

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="SkillSwap")
    logger.info("request_id=%s action=mfa_setup user_id=%s", request_id, current_user.id)
    return TOTPSetupResponse(totp_secret=secret, totp_uri=uri)


@router.post("/verify")
async def verify_mfa(
    payload: TOTPVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", "unknown")
    if not current_user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP not set up")

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    current_user.totp_enabled = True
    await db.commit()
    logger.info("request_id=%s action=mfa_verified user_id=%s", request_id, current_user.id)
    return {"message": "TOTP enabled successfully"}


@router.post("/disable")
async def disable_mfa(
    payload: TOTPDisableRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", "unknown")
    if not current_user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP not enabled")

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    current_user.totp_enabled = False
    current_user.totp_secret = None
    await db.commit()
    logger.info("request_id=%s action=mfa_disabled user_id=%s", request_id, current_user.id)
    return {"message": "TOTP disabled successfully"}
