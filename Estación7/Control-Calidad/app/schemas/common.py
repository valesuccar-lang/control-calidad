"""Common Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class ErrorResponse(BaseModel):
    """Error response model"""
    status_code: int
    detail: str
    error_type: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response"""
    status_code: int = 200
    message: str
    data: Optional[Any] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    environment: str
    database: str
    error: Optional[str] = None


class ConfigResponse(BaseModel):
    """Frontend configuration response"""
    environment: str
    api_url: str
    photo_max_size_kb: int
    retry_delays: list
    sync_enabled: bool
    features: dict

    class Config:
        from_attributes = True
