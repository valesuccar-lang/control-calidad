"""Pydantic schemas for masters data"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DefectResponse(BaseModel):
    """Response model for defect"""
    defect_id: str
    name: str
    category: str
    severity: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MachineResponse(BaseModel):
    """Response model for machine"""
    machine_id: str
    name: str
    model: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FabricResponse(BaseModel):
    """Response model for fabric"""
    fabric_id: str
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BulkImportDefectsRequest(BaseModel):
    """Request model for bulk importing defects"""
    defects: List[dict] = Field(..., min_items=1, max_items=500)


class BulkImportMachinesRequest(BaseModel):
    """Request model for bulk importing machines"""
    machines: List[dict] = Field(..., min_items=1, max_items=500)


class BulkImportFabricsRequest(BaseModel):
    """Request model for bulk importing fabrics"""
    fabrics: List[dict] = Field(..., min_items=1, max_items=500)


class BulkImportResponse(BaseModel):
    """Response model for bulk import"""
    created: int
    skipped: int
    total: int


class MastersListResponse(BaseModel):
    """Generic response for masters list"""
    total: int
    items: List[dict]
    page: int
    page_size: int
