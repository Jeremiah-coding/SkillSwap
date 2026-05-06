"""
HTTP clients for calling other microservices.
All calls include timeout handling and request ID propagation.
"""
import logging
from typing import Optional

import httpx
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger("session_service")


async def validate_profile(
    profile_id: str,
    request_id: str,
) -> dict:
    """
    Validate that a profile exists in the Identity Service.
    
    Args:
        profile_id: UUID of the profile to validate
        request_id: Request ID for distributed tracing
        
    Returns:
        Profile data if valid
        
    Raises:
        HTTPException: If profile not found or Identity Service is unavailable
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.IDENTITY_SERVICE_URL}/internal/profiles/{profile_id}",
                headers={
                    "X-Request-ID": request_id,
                    "X-Internal-Secret": settings.SECRET_KEY,
                },
                timeout=settings.HTTP_TIMEOUT,
            )
            
            if response.status_code == 404:
                logger.warning(
                    "request_id=%s profile_validation_failed profile_id=%s status=%d",
                    request_id,
                    profile_id,
                    response.status_code,
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Profile {profile_id} not found",
                )
            
            response.raise_for_status()
            logger.info(
                "request_id=%s profile_validation_success profile_id=%s",
                request_id,
                profile_id,
            )
            return response.json()
            
        except httpx.TimeoutException:
            logger.error(
                "request_id=%s profile_validation_timeout profile_id=%s timeout_seconds=%s",
                request_id,
                profile_id,
                settings.HTTP_TIMEOUT,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Identity Service is unavailable",
            )
        except httpx.RequestError as e:
            logger.error(
                "request_id=%s profile_validation_error profile_id=%s error=%s",
                request_id,
                profile_id,
                str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Identity Service is unavailable",
            )


async def create_notification(
    profile_id: str,
    message: str,
    notification_type: str,
    request_id: str,
) -> Optional[dict]:
    """
    Create a notification in the Notification Service.
    
    Args:
        profile_id: UUID of the profile to notify
        message: Notification message
        notification_type: Type of notification (e.g., session_created, session_approved)
        request_id: Request ID for distributed tracing
        
    Returns:
        Notification data if created, None if Notification Service fails
        
    Note:
        If notification creation fails, logs the error but does not raise.
        Session has already been saved, so we don't want to fail the request.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notifications",
                json={
                    "profile_id": profile_id,
                    "message": message,
                    "type": notification_type,
                },
                headers={
                    "X-Request-ID": request_id,
                    "Authorization": f"Bearer {settings.SECRET_KEY}",
                },
                timeout=settings.HTTP_TIMEOUT,
            )
            
            response.raise_for_status()
            logger.info(
                "request_id=%s notification_created notification_type=%s profile_id=%s",
                request_id,
                notification_type,
                profile_id,
            )
            return response.json()
            
        except httpx.TimeoutException:
            logger.error(
                "request_id=%s notification_creation_timeout profile_id=%s timeout_seconds=%s",
                request_id,
                profile_id,
                settings.HTTP_TIMEOUT,
            )
            # Don't raise – session already saved
            return None
            
        except httpx.RequestError as e:
            logger.error(
                "request_id=%s notification_creation_failed profile_id=%s error=%s",
                request_id,
                profile_id,
                str(e),
            )
            # Don't raise – session already saved
            return None
