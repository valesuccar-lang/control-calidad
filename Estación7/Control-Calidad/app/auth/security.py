"""JWT security and password handling"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from loguru import logger

from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityService:
    """JWT and password security service"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                hours=settings.jwt.access_token_expire_hours
            )

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt.secret_key,
            algorithm=settings.jwt.algorithm
        )
        logger.info("Access token created", user_id=data.get("sub"))
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=settings.jwt.refresh_token_expire_days
        )
        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt.secret_key,
            algorithm=settings.jwt.algorithm
        )
        logger.info("Refresh token created", user_id=data.get("sub"))
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.jwt.secret_key,
                algorithms=[settings.jwt.algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning("Token decode failed", error=str(e))
            return None

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """Verify token is valid and of correct type"""
        payload = SecurityService.decode_token(token)
        if not payload:
            return None

        if payload.get("type") != token_type:
            logger.warning("Token type mismatch", expected=token_type, got=payload.get("type"))
            return None

        return payload


security_service = SecurityService()
