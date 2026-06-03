"""
Auth Routes — FastAPI
/auth/* endpoints for authentication and token management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
import bcrypt
import os

# Imports from app
from .models import User, RoleEnum
from .database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-prod")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8
REFRESH_TOKEN_EXPIRE_DAYS = 30


# ============================================================================
# SCHEMAS (Pydantic)
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


# ============================================================================
# UTILITIES
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: str, email: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token (long-lived)"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================================
# ROUTES
# ============================================================================

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint
    Returns: access_token, refresh_token, and user info
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    # Create tokens
    access_token = create_access_token(str(user.id), user.email, user.role.value)
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
        },
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token
    Returns: new access_token and refresh_token
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Get user from DB
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create new tokens
    new_access_token = create_access_token(str(user.id), user.email, user.role.value)
    new_refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,
    }


@router.post("/logout")
async def logout():
    """
    Logout endpoint
    Note: In stateless JWT, logout is typically done on frontend by clearing tokens
    This can be extended to blacklist tokens if needed
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    authorization: str = None,
    db: Session = Depends(get_db)
):
    """
    Get current user info
    Requires: Authorization: Bearer {token}
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Extract token from "Bearer {token}"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    # Verify token
    payload = verify_token(token)
    user_id = payload.get("sub")

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
