import uuid
import logging
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
import httpx
from pydantic import BaseModel
from cropnet.services.api.app.core.config import settings

logger = logging.getLogger(__name__)


def _resolve_is_admin(email: str, user_id: uuid.UUID) -> bool:
    """Determine whether the authenticated user has Government Schemes admin rights."""
    normalized_email = (email or "").strip().lower()
    admin_emails = {e.strip().lower() for e in settings.ADMIN_EMAILS if e and e.strip()}
    admin_ids = {u.strip().lower() for u in settings.ADMIN_USER_IDS if u and u.strip()}
    return normalized_email in admin_emails or str(user_id).lower() in admin_ids


class CurrentUser(BaseModel):
    user_id: uuid.UUID
    email: str
    is_authenticated: bool = True
    is_admin: bool = False


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_dev_user_id: Optional[str] = Header(None)
) -> CurrentUser:
    """
    Authenticate request and return current user.
    - If Authorization: Bearer <token> is provided, verifies against Supabase Auth.
    - In development mode (ENVIRONMENT=development), allows X-Dev-User-Id for automated testing and local isolation.
    - Strictly blocks dev header bypass in production.
    """
    # 1. Bearer Token Verification via Supabase
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
            try:
                auth_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        auth_url,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "apikey": settings.SUPABASE_ANON_KEY
                        }
                    )
                    if resp.status_code == 200:
                        user_data = resp.json()
                        user_id = uuid.UUID(user_data["id"])
                        email = user_data.get("email", "")
                        return CurrentUser(
                            user_id=user_id,
                            email=email,
                            is_authenticated=True,
                            is_admin=_resolve_is_admin(email, user_id)
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired Supabase authentication token"
                        )
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Supabase token verification error: %s", e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Authentication service error: {str(e)}"
                )

    # 2. Local Development Opt-In Auth Bypass Gate
    is_production = (
        settings.ENVIRONMENT.lower() in ("production", "prod")
        or getattr(settings, "PRODUCTION", False)
    )

    if not is_production and getattr(settings, "ALLOW_DEV_AUTH_BYPASS", False):
        if x_dev_user_id:
            try:
                user_uuid = uuid.UUID(x_dev_user_id)
                # Local development user is treated as admin so the admin UI can be
                # exercised without a live Supabase project configuration.
                return CurrentUser(
                    user_id=user_uuid,
                    email=settings.DEV_USER_EMAIL,
                    is_authenticated=True,
                    is_admin=True
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid UUID format in X-Dev-User-Id"
                )

    # 3. Fail-Closed Authentication Rejection (Never silently impersonate DEV_USER_ID)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid authentication credentials: Missing Authorization Bearer token",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Dependency gate restricting an endpoint to Government Schemes administrators."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required for this operation."
        )
    return current_user
