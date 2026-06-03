"""Pydantic schemas for approval requests/responses"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ApproveInspectionRequest(BaseModel):
    """Request model for approving an inspection"""
    inspection_id: UUID
    notes: Optional[str] = Field(None, max_length=500)


class RejectInspectionRequest(BaseModel):
    """Request model for rejecting an inspection"""
    inspection_id: UUID
    rejection_reason: str = Field(..., min_length=10, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)


class ApprovalResponse(BaseModel):
    """Response model for approval"""
    approval_id: UUID
    inspection_id: UUID
    jefe_qa_id: str
    decision: str
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    approved_at: datetime

    class Config:
        from_attributes = True


class PendingApprovalResponse(BaseModel):
    """Response for pending approvals list"""
    approval_id: UUID
    inspection_id: UUID
    lote_id: str
    defect_id: str
    comment_text: str
    photo_path: str
    analista_id: str
    check_in: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalListResponse(BaseModel):
    """Response for listing approvals"""
    total: int
    items: List[ApprovalResponse]
    page: int
    page_size: int
