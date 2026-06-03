"""Pydantic schemas for inspection requests/responses"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CreateInspectionRequest(BaseModel):
    """Request model for creating an inspection"""
    lote_id: str = Field(..., min_length=1, max_length=50)
    defect_id: str = Field(..., min_length=1, max_length=50)
    comment_text: str = Field(..., min_length=10, max_length=500)
    photo_path: str = Field(..., max_length=500)
    photo_checksum: str = Field(..., min_length=64, max_length=64)
    photo_size_kb: int = Field(..., gt=0, le=500)
    machine_id: str = Field(..., min_length=1, max_length=50)


class InspectionResponse(BaseModel):
    """Response model for inspection"""
    inspection_id: UUID
    lote_id: str
    analista_id: str
    defect_id: str
    comment_text: str
    photo_path: str
    photo_checksum: str
    machine_id: str
    check_in: datetime
    check_out: Optional[datetime] = None
    elapsed_seconds: int
    sync_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SyncBatchRequest(BaseModel):
    """Request model for batch sync of multiple inspections"""
    inspections: List[CreateInspectionRequest] = Field(..., min_items=1, max_items=100)


class SyncBatchResponse(BaseModel):
    """Response model for batch sync"""
    synced_count: int
    failed_count: int
    details: List[dict]


class InspectionListResponse(BaseModel):
    """Response for listing inspections"""
    total: int
    items: List[InspectionResponse]
    page: int
    page_size: int
