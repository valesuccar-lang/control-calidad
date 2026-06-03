"""Authentication routes - login and token refresh"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from loguru import logger
from datetime import timedelta

from app.auth.security import security_service
from app.auth.dependencies import get_current_user
from app.config import settings

router = APIRouter(tags=["authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    roles: list


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse, status_code=200)
async def login(request: LoginRequest):
    """POST /auth/login → JWT access + refresh tokens"""
    DEMO_USERS = {
        "analista@example.com": ("password", "analista_001", ["ANALISTA"]),
        "jefe@example.com": ("password", "jefe_001", ["JEFE_QA"]),
        "admin@example.com": ("password", "admin_001", ["ADMIN"]),
        "gerente@example.com": ("password", "gerente_001", ["GERENTE"]),
    }
    user = DEMO_USERS.get(request.email)
    if not user or user[0] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id, roles = user[1], user[2]
    access_token = security_service.create_access_token(data={"sub": user_id, "roles": roles})
    refresh_token = security_service.create_refresh_token(data={"sub": user_id})

    logger.info("User login successful", user_id=user_id)
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        roles=roles,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest):
    """POST /auth/refresh → nuevo access token"""
    payload = security_service.verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    roles = payload.get("roles", ["ANALISTA"])
    access_token = security_service.create_access_token(data={"sub": user_id, "roles": roles})
    return RefreshResponse(access_token=access_token)


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user_id": user.get("sub"), "roles": user.get("roles", [])}
