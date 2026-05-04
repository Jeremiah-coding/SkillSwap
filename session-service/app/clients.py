import logging
import httpx
from fastapi import HTTPException, status
from app.config import settings
from app.core.security import create_service_token

logger = logging.getLogger("session_service")


async def validate_profile(profile_id: str, request_id: str) -> None:
    """Call Identity Service internal endpoint to confirm a profile exists."""
    url = f"{settings.IDENTITY_SERVICE_URL}/internal/profiles/{profile_id}"
    headers = {
        "X-Request-ID": request_id,
        "X-Internal-Service-Secret": settings.INTERNAL_SERVICE_SECRET,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code == 404:
            logger.warning(
                "request_id=%s action=validate_profile profile_id=%s status=not_found",
                request_id, profile_id,
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Profile {profile_id} not found",
            )
        if resp.status_code != 200:
            logger.error(
                "request_id=%s action=validate_profile profile_id=%s status=upstream_error code=%s",
                request_id, profile_id, resp.status_code,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Identity service returned an unexpected error",
            )

        logger.info(
            "request_id=%s action=validate_profile profile_id=%s status=ok",
            request_id, profile_id,
        )

    except httpx.TimeoutException:
        logger.error(
            "request_id=%s action=validate_profile profile_id=%s status=timeout",
            request_id, profile_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity service timed out",
        )
    except httpx.RequestError as exc:
        logger.error(
            "request_id=%s action=validate_profile profile_id=%s status=unreachable error=%s",
            request_id, profile_id, str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity service unreachable",
        )


async def send_notification(
    profile_id: str,
    message: str,
    notif_type: str,
    request_id: str,
) -> None:
    """Call Notification Service to create a notification. Failures are logged but do not propagate."""
    url = f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notifications"
    token = create_service_token()
    headers = {"Authorization": f"Bearer {token}", "X-Request-ID": request_id}
    payload = {"profile_id": str(profile_id), "message": message, "type": notif_type}

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code not in (200, 201):
            logger.warning(
                "request_id=%s action=send_notification profile_id=%s type=%s status=unexpected_response code=%s",
                request_id, profile_id, notif_type, resp.status_code,
            )
        else:
            logger.info(
                "request_id=%s action=send_notification profile_id=%s type=%s status=ok",
                request_id, profile_id, notif_type,
            )

    except httpx.TimeoutException:
        logger.warning(
            "request_id=%s action=send_notification profile_id=%s type=%s status=timeout",
            request_id, profile_id, notif_type,
        )
    except httpx.RequestError as exc:
        logger.warning(
            "request_id=%s action=send_notification profile_id=%s type=%s status=unreachable error=%s",
            request_id, profile_id, notif_type, str(exc),
        )
