import uuid
import logging
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
import httpx
from pydantic import BaseModel
from cropnet.services.api.app.core.config import settings

logger = logging.getLogger(__name__)


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
                        return CurrentUser(
                            user_id=uuid.UUID(user_data["id"]),
                            email=user_data.get("email", ""),
                            is_authenticated=True
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

    # 2. Development Mode Fallback with X-Dev-User-Id
    if settings.ENVIRONMENT == "development":
        user_id_str = x_dev_user_id or settings.DEV_USER_ID
        try:
            user_uuid = uuid.UUID(user_id_str)
            return CurrentUser(
                user_id=user_uuid,
                email=settings.DEV_USER_EMAIL,
                is_authenticated=True
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format in X-Dev-User-Id"
            )

    # 3. Production Protection
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Authorization Bearer token",
        headers={"WWW-Authenticate": "Bearer"}
    )
