from secrets import compare_digest

from fastapi import Header, HTTPException, status

from app.core.config import ConfigurationError, settings


def verify_admin_token(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")
) -> None:
    try:
        settings.validate()
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if not x_admin_token or not compare_digest(x_admin_token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
