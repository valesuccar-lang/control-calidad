"""Authentication routes - login and token refresh"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from loguru import logger

from app.auth.security import security_service
from app.auth.dependencies import get_current_user
from app.monitoring.audit_logger import audit_logger

router = APIRouter(tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    roles: list


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Token refresh response"""
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(request: LoginRequest):
    """
    User login endpoint.
    Returns JWT access and refresh tokens.
    """
    # TODO: Validate credentials against user database
    # This is a placeholder - in production, query users table and verify password

    # For now, accept demo credentials
    if request.email == "analista@example.com" and request.password == "password":
        user_id = "analista_001"
        roles = ["ANALISTA"]
    elif request.email == "jefe@example.com" and request.password == "password":
        user_id = "jefe_001"
        roles = ["JEFE_QA"]
    elif request.email == "admin@example.com" and request.password == "password":
        user_id = "admin_001"
        roles = ["ADMIN"]
    elif request.email == "gerente@example.com" and request.password == "password":
        user_id = "gerente_001"
        roles = ["GERENTE"]
    else:
        audit_logger.log_auth_failure(
            email=request.email,
            reason="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create tokens
    access_token = security_service.create_access_token(
        data={"sub": user_id, "roles": roles}
    )
    refresh_token = security_service.create_refresh_token(
        data={"sub": user_id}
    )

    audit_logger.log_user_login(user_id, request.email)

    logger.info("User login successful", user_id=user_id, email=request.email)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        roles=roles
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh expired access token using refresh token.
    """
    payload = security_service.verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")

    # TODO: Get user roles from database
    roles = ["ANALISTA"]  # Placeholder

    access_token = security_service.create_access_token(
        data={"sub": user_id, "roles": roles}
    )

    logger.info("Token refreshed", user_id=user_id)

    return RefreshResponse(access_token=access_token)


@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "user_id": user.get("sub"),
        "roles": user.get("roles", [])
    }
