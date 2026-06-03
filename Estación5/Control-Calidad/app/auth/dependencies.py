"""FastAPI dependency injection for authentication"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials as HTTPAuthCredentials
from typing import Optional, List
from loguru import logger

from app.auth.security import security_service

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> dict:
    """
    Extract and validate JWT token from Authorization header.
    Returns user payload with sub, roles, etc.
    """
    token = credentials.credentials

    payload = security_service.verify_token(token, token_type="access")
    if not payload:
        logger.warning("Invalid token attempted", token_preview=token[:20])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    logger.debug("User authenticated", user_id=user_id)
    return payload


async def get_current_user_optional(
    credentials: Optional[HTTPAuthCredentials] = Depends(security) if False else None
) -> Optional[dict]:
    """Optional authentication - returns user if valid token, None otherwise"""
    if not credentials:
        return None

    return await get_current_user(credentials)


def require_role(*allowed_roles: str):
    """Dependency to enforce role-based access control"""
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_roles = user.get("roles", [])

        if not any(role in user_roles for role in allowed_roles):
            logger.warning(
                "Unauthorized role access attempted",
                user_id=user.get("sub"),
                required=list(allowed_roles),
                user_roles=user_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User must have one of roles: {', '.join(allowed_roles)}"
            )

        return user

    return role_checker


def get_user_id(user: dict = Depends(get_current_user)) -> str:
    """Extract user ID from current user"""
    return user.get("sub")


def get_user_roles(user: dict = Depends(get_current_user)) -> List[str]:
    """Extract roles from current user"""
    return user.get("roles", [])
