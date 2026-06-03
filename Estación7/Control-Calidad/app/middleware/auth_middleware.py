"""Authentication middleware for request validation"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from loguru import logger

from app.monitoring.audit_logger import audit_logger


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and extract auth info"""

    async def dispatch(self, request: Request, call_next):
        """Log incoming request and response"""
        start_time = time.time()

        # Extract auth info
        auth_header = request.headers.get("Authorization", "")
        user_id = None

        if auth_header.startswith("Bearer "):
            from app.auth.security import security_service
            token = auth_header.replace("Bearer ", "")
            payload = security_service.decode_token(token)
            if payload:
                user_id = payload.get("sub")

        # Get IP address
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log request
        audit_logger.log_api_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            ip_address=ip_address
        )

        # Add custom headers
        response.headers["X-Process-Time"] = str(duration_ms)
        response.headers["X-User-ID"] = user_id or "anonymous"

        return response
