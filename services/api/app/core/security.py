import uuid
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel
from cropnet.services.api.app.core.config import settings


class CurrentUser(BaseModel):
    user_id: uuid.UUID
    email: str
    is_authenticated: bool = True


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_dev_user_id: Optional[str] = Header(None)
) -> CurrentUser:
    """
    Authenticate request and return current user.
    In development mode without external auth, allows test user headers.
    In production mode, strictly validates authorization bearer tokens.
    """
    if settings.SUPABASE_AUTH_ENABLED:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = authorization.split("Bearer ")[1].strip()
        # Decode and verify Supabase JWT
        # For greenfield initialization, if JWT secret is configured, verify here
        if not settings.SUPABASE_JWT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase JWT secret not configured on backend"
            )
        # Placeholder for external JWT verification
        # Return authenticated user
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="External Supabase Auth provider configuration in progress"
        )

    # Safe Local Development Mode (strictly blocked in production)
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Development auth bypass is strictly disabled in production environment"
        )

    # Allow custom dev user ID for testing multi-user isolation
    user_id_str = x_dev_user_id or settings.DEV_USER_ID
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID in X-Dev-User-Id header"
        )

    return CurrentUser(
        user_id=user_uuid,
        email=settings.DEV_USER_EMAIL,
        is_authenticated=True
    )
