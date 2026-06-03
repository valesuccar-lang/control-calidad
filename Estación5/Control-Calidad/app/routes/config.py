"""Configuration and system info endpoints"""
from fastapi import APIRouter, Depends
from loguru import logger

from app.auth.dependencies import get_current_user_optional
from app.settings import app_settings
from app.schemas.common import ConfigResponse

router = APIRouter()


@router.get("/config", response_model=ConfigResponse)
async def get_config(user: dict = Depends(get_current_user_optional)):
    """Get frontend configuration"""
    try:
        config = ConfigResponse(
            environment=app_settings.config.environment,
            api_url="http://localhost:8000" if app_settings.config.is_development else "https://api.example.com",
            photo_max_size_kb=app_settings.config.photo_storage.max_size_kb,
            retry_delays=app_settings.get_backoff_delays(),
            sync_enabled=True,
            features={
                "offline_first": True,
                "photo_validation": True,
                "audit_logging": True,
                "rbac": True
            }
        )
        logger.info("Config retrieved", user_id=user.get("sub") if user else None)
        return config

    except Exception as e:
        logger.error("Error getting config", error=str(e))
        raise
