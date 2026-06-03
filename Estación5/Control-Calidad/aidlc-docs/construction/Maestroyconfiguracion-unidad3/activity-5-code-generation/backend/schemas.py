# backend/app/schemas.py
# Pydantic schemas for request/response validation

from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator


class ProcessEnum(str, Enum):
    TEÑIDO = "TEÑIDO"
    ESTAMPADO = "ESTAMPADO"
    ACABADO = "ACABADO"
    OTRA = "OTRA"


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ImportModeEnum(str, Enum):
    SKIP_DUPLICATES = "skip_duplicates"
    UPSERT = "upsert"


# ==================== DEFECT SCHEMAS ====================

class DefectBase(BaseModel):
    """Base schema for Defect (shared fields)"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    typical_process: ProcessEnum = ProcessEnum.OTRA
    typical_machine_id: Optional[str] = Field(None, max_length=100)

    @validator('name')
    def validate_name(cls, v):
        """Validate name format: alphanumeric + space/-/_"""
        if not all(c.isalnum() or c in ' -_' for c in v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, hyphens, or underscores')
        return v.strip()


class DefectCreate(DefectBase):
    """Schema for creating a defect"""
    pass


class DefectUpdate(BaseModel):
    """Schema for updating a defect (includes version for optimistic locking)"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    typical_process: Optional[ProcessEnum] = None
    typical_machine_id: Optional[str] = Field(None, max_length=100)
    version: int = Field(..., description="Current version for optimistic locking")

    @validator('name')
    def validate_name(cls, v):
        if v and not all(c.isalnum() or c in ' -_' for c in v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, hyphens, or underscores')
        return v.strip() if v else v


class DefectResponse(DefectBase):
    """Schema for defect response"""
    id: str
    status: StatusEnum
    is_system: bool
    version: int
    created_by: str
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    typical_machine_name: Optional[str] = None

    class Config:
        from_attributes = True


class DefectListResponse(BaseModel):
    """Schema for list of defects with pagination"""
    items: List[DefectResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ==================== MACHINE SCHEMAS ====================

class MachineBase(BaseModel):
    """Base schema for Machine"""
    name: str = Field(..., min_length=3, max_length=100)
    process: ProcessEnum
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    installation_date: Optional[date] = None

    @validator('name')
    def validate_name(cls, v):
        if not all(c.isalnum() or c in ' -_' for c in v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, hyphens, or underscores')
        return v.strip()

    @validator('installation_date')
    def validate_installation_date(cls, v):
        if v and v > date.today():
            raise ValueError('Installation date cannot be in the future')
        return v


class MachineCreate(MachineBase):
    """Schema for creating a machine"""
    pass


class MachineUpdate(BaseModel):
    """Schema for updating a machine"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    process: Optional[ProcessEnum] = None
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    installation_date: Optional[date] = None
    version: int = Field(..., description="Current version for optimistic locking")

    @validator('name')
    def validate_name(cls, v):
        if v and not all(c.isalnum() or c in ' -_' for c in v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, hyphens, or underscores')
        return v.strip() if v else v


class MachineResponse(MachineBase):
    """Schema for machine response"""
    id: str
    status: StatusEnum
    is_system: bool
    version: int
    created_by: str
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MachineListResponse(BaseModel):
    """Schema for list of machines with pagination"""
    items: List[MachineResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ==================== FABRIC SCHEMAS ====================

class FabricBase(BaseModel):
    """Base schema for Fabric"""
    name: str = Field(..., min_length=3, max_length=100)
    composition: str = Field(..., min_length=3, max_length=200)
    width_cm: Decimal = Field(..., decimal_places=2, ge=10, le=300)
    weight_gsm: Decimal = Field(..., decimal_places=2, ge=50, le=1000)

    @validator('name')
    def validate_name(cls, v):
        if not all(c.isalnum() or c in ' -_' for c in v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, hyphens, or underscores')
        return v.strip()

    @validator('composition')
    def validate_composition(cls, v):
        """Validate composition format: e.g., 'Cotton 50%, Polyester 50%'"""
        if not v or '%' not in v:
            raise ValueError("Composition must include percentage (e.g., 'Cotton 50%, Polyester 50%')")
        return v


class FabricCreate(FabricBase):
    """Schema for creating a fabric"""
    pass


class FabricUpdate(BaseModel):
    """Schema for updating a fabric"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    composition: Optional[str] = Field(None, min_length=3, max_length=200)
    width_cm: Optional[Decimal] = Field(None, decimal_places=2, ge=10, le=300)
    weight_gsm: Optional[Decimal] = Field(None, decimal_places=2, ge=50, le=1000)
    version: int = Field(..., description="Current version for optimistic locking")


class FabricResponse(FabricBase):
    """Schema for fabric response"""
    id: str
    status: StatusEnum
    is_system: bool
    version: int
    created_by: str
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FabricListResponse(BaseModel):
    """Schema for list of fabrics with pagination"""
    items: List[FabricResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ==================== ARCHIVE SCHEMAS ====================

class ArchiveRequest(BaseModel):
    """Schema for archiving a master"""
    reason: Optional[str] = Field(None, max_length=500)


class ArchiveResponse(BaseModel):
    """Schema for archive response"""
    success: bool
    message: str
    error: Optional[str] = None


# ==================== CSV IMPORT SCHEMAS ====================

class CsvImportStartRequest(BaseModel):
    """Schema for starting CSV import (Step 1)"""
    master_type: str = Field(..., description="'defect', 'machine', or 'fabric'")
    file_path: str = Field(..., description="Path to uploaded CSV file")


class CsvValidationResponse(BaseModel):
    """Schema for CSV validation result (Step 2)"""
    valid: bool
    file_name: str
    file_size_bytes: int
    row_count: int
    estimated_duration_seconds: float
    errors: Optional[List[str]] = None


class CsvPreviewRow(BaseModel):
    """Single row in CSV preview"""
    row_number: int
    values: dict
    action: str  # 'new', 'duplicate', 'update'


class CsvImportPreview(BaseModel):
    """CSV import preview for review (Step 3)"""
    master_type: str
    total_rows: int
    new_count: int
    duplicate_count: int
    update_count: int
    preview_rows: List[CsvPreviewRow] = Field(default=[], description="First 10 rows")


class CsvImportExecuteRequest(BaseModel):
    """Schema for executing CSV import (Step 4)"""
    import_mode: ImportModeEnum
    skip_validation: bool = False


class CsvImportError(BaseModel):
    """Single CSV row error"""
    row_number: int
    column: str
    value: str
    error: str


class CsvImportResult(BaseModel):
    """Result of CSV import (Step 5)"""
    success: bool
    status: str  # 'COMPLETED', 'VALIDATION_FAILED', 'FAILED'
    job_id: str
    master_type: str
    filename: str
    total_rows: int
    processed_rows: int
    error_count: int
    duration_seconds: Optional[float] = None
    errors: Optional[List[CsvImportError]] = None
    message: str


class ImportJobStatus(BaseModel):
    """Current status of an import job"""
    id: str
    master_type: str
    status: str
    total_rows: int
    processed_rows: int
    error_count: int
    percentage_complete: float
    estimated_seconds_remaining: Optional[float]


# ==================== AUDIT TRAIL SCHEMAS ====================

class AuditLogEntry(BaseModel):
    """Schema for audit log entry"""
    id: int
    entity_type: str
    entity_id: str
    operation: str
    old_values: Optional[str]
    new_values: Optional[str]
    user_id: str
    timestamp: datetime
    trace_id: Optional[str]

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Schema for audit log list"""
    items: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


# ==================== ERROR SCHEMAS ====================

class ErrorResponse(BaseModel):
    """Schema for error response"""
    error: str
    detail: str
    status_code: int
    trace_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Schema for validation error response"""
    error: str = "Validation Error"
    errors: List[dict]  # List of {field: str, message: str}
    trace_id: Optional[str] = None


# ==================== PAGINATION SCHEMAS ====================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort: Optional[str] = None  # e.g., 'name', '-created_at'
    search: Optional[str] = None  # Search term


# ==================== BULK OPERATIONS SCHEMAS ====================

class BulkArchiveRequest(BaseModel):
    """Schema for bulk archiving masters"""
    ids: List[str] = Field(..., min_items=1, max_items=100)
    reason: Optional[str] = Field(None, max_length=500)


class BulkArchiveResponse(BaseModel):
    """Response for bulk archive operation"""
    success_count: int
    failure_count: int
    failures: Optional[List[dict]] = None  # {id: str, error: str}
