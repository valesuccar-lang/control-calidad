"""
Inspection Routes — FastAPI
/inspections/* endpoints for inspection CRUD and sync
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import base64
import os

# Imports from app
from .models import Inspection, Lote, User, InspectionStatusEnum, Fabric, Defect, Machine
from .database import get_db
from .routes_auth import verify_token

router = APIRouter(prefix="/inspections", tags=["inspections"])

PHOTO_DIR = os.getenv("PHOTO_DIR", "/data/photos")


# ============================================================================
# SCHEMAS
# ============================================================================

class PhotoMetadata(BaseModel):
    laplacian: float
    brightness: float
    contrast: float
    quality: str


class PhotoData(BaseModel):
    id: str
    base64: str
    metadata: PhotoMetadata


class InspectionCreate(BaseModel):
    lote_id: str
    defect_type_id: str
    machine_culpable_id: Optional[str] = None
    comment: str = Field(..., min_length=10, max_length=500)
    photos: List[PhotoData]


class InspectionResponse(BaseModel):
    id: str
    lote_id: str
    status: str
    check_in: str
    synced: bool

    class Config:
        from_attributes = True


class InspectionDetailResponse(BaseModel):
    id: str
    lote_id: str
    fabric_name: str
    analista_id: str
    analista_name: str
    defect_type_id: str
    defect_type_name: str
    machine_culpable_id: Optional[str]
    machine_name: Optional[str]
    comment: str
    photo_path: Optional[str]
    status: str
    check_in: str
    check_out: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class PendingApprovalResponse(BaseModel):
    id: str
    lote_id: str
    fabric_name: str
    analista_name: str
    defect_type_name: str
    machine_name: Optional[str]
    comment: str
    photo_url: Optional[str]
    created_at: str


class InspectionSyncRequest(BaseModel):
    inspection: InspectionCreate
    photos: List[PhotoData]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_photo(photo_base64: str, inspection_id: str) -> str:
    """Save base64 photo to filesystem"""
    try:
        # Remove data:image/jpeg;base64, prefix if present
        if "," in photo_base64:
            photo_base64 = photo_base64.split(",")[1]

        photo_bytes = base64.b64decode(photo_base64)
        filename = f"{inspection_id}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(PHOTO_DIR, filename)

        os.makedirs(PHOTO_DIR, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(photo_bytes)

        return filename
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save photo: {str(e)}")


def get_current_user(authorization: Optional[str] = None, db: Session = None) -> User:
    """Extract and verify user from JWT token"""
    if not authorization or not db:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except (ValueError, IndexError):
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = verify_token(token)
    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ============================================================================
# ROUTES
# ============================================================================

@router.post("/", response_model=InspectionResponse, status_code=201)
async def create_inspection(
    request: InspectionCreate,
    authorization: str = None,
    db: Session = Depends(get_db),
):
    """
    Create new inspection
    POST /inspections
    Returns: inspection ID and status
    """
    # Verify user
    user = get_current_user(authorization, db)

    # Verify lote exists
    lote = db.query(Lote).filter(Lote.id == request.lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote not found")

    # Verify defect type exists
    defect = db.query(Defect).filter(Defect.id == request.defect_type_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect type not found")

    # Create inspection
    inspection = Inspection(
        lote_id=request.lote_id,
        analista_id=user.id,
        defect_type_id=request.defect_type_id,
        machine_culpable_id=request.machine_culpable_id,
        comment=request.comment,
        status=InspectionStatusEnum.REGISTERED,
        synced=True,
    )

    # Save photos
    if request.photos:
        photo_filename = save_photo(request.photos[0].base64, str(inspection.id))
        inspection.photo_path = photo_filename

    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    return {
        "id": str(inspection.id),
        "lote_id": inspection.lote_id,
        "status": inspection.status.value,
        "check_in": inspection.check_in.isoformat(),
        "synced": inspection.synced,
    }


@router.get("/pending-approval", response_model=List[PendingApprovalResponse])
async def get_pending_approvals(
    limit: int = 20,
    offset: int = 0,
    authorization: str = None,
    db: Session = Depends(get_db),
):
    """
    Get inspections pending approval (no approval yet)
    GET /inspections/pending-approval?limit=20&offset=0
    """
    # Verify user (optional for this endpoint)
    if authorization:
        user = get_current_user(authorization, db)

    # Query inspections without approvals
    inspections = (
        db.query(Inspection)
        .filter(Inspection.approval.is_(None))  # No approval record
        .order_by(Inspection.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []
    for insp in inspections:
        fabric = db.query(Fabric).filter(Fabric.id == insp.lote.fabric_id).first()
        defect = db.query(Defect).filter(Defect.id == insp.defect_type_id).first()
        machine = (
            db.query(Machine).filter(Machine.id == insp.machine_culpable_id).first()
            if insp.machine_culpable_id
            else None
        )

        result.append({
            "id": str(insp.id),
            "lote_id": insp.lote_id,
            "fabric_name": fabric.name if fabric else "Unknown",
            "analista_name": insp.analista.full_name,
            "defect_type_name": defect.name if defect else "Unknown",
            "machine_name": machine.name if machine else None,
            "comment": insp.comment,
            "photo_url": f"/static/{insp.photo_path}" if insp.photo_path else None,
            "created_at": insp.created_at.isoformat(),
        })

    return result


@router.get("/{inspection_id}", response_model=InspectionDetailResponse)
async def get_inspection(
    inspection_id: str,
    authorization: str = None,
    db: Session = Depends(get_db),
):
    """Get single inspection with full details"""
    user = get_current_user(authorization, db)

    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")

    fabric = db.query(Fabric).filter(Fabric.id == inspection.lote.fabric_id).first()
    defect = db.query(Defect).filter(Defect.id == inspection.defect_type_id).first()
    machine = (
        db.query(Machine).filter(Machine.id == inspection.machine_culpable_id).first()
        if inspection.machine_culpable_id
        else None
    )

    return {
        "id": str(inspection.id),
        "lote_id": inspection.lote_id,
        "fabric_name": fabric.name if fabric else "Unknown",
        "analista_id": str(inspection.analista_id),
        "analista_name": inspection.analista.full_name,
        "defect_type_id": inspection.defect_type_id,
        "defect_type_name": defect.name if defect else "Unknown",
        "machine_culpable_id": inspection.machine_culpable_id,
        "machine_name": machine.name if machine else None,
        "comment": inspection.comment,
        "photo_path": inspection.photo_path,
        "status": inspection.status.value,
        "check_in": inspection.check_in.isoformat(),
        "check_out": inspection.check_out.isoformat() if inspection.check_out else None,
        "created_at": inspection.created_at.isoformat(),
    }


@router.post("/sync", response_model=dict)
async def sync_offline_inspections(
    request: InspectionSyncRequest,
    authorization: str = None,
    db: Session = Depends(get_db),
):
    """
    Sync offline-captured inspections
    POST /inspections/sync
    Receives: { inspection, photos }
    Returns: sync status
    """
    user = get_current_user(authorization, db)

    try:
        # Check if inspection already exists
        existing = db.query(Inspection).filter(
            Inspection.lote_id == request.inspection.lote_id
        ).first()

        # Verify lote
        lote = db.query(Lote).filter(Lote.id == request.inspection.lote_id).first()
        if not lote:
            raise Exception("Lote not found")

        # Create new inspection
        inspection = Inspection(
            id=uuid.uuid4(),
            lote_id=request.inspection.lote_id,
            analista_id=user.id,
            defect_type_id=request.inspection.defect_type_id,
            machine_culpable_id=request.inspection.machine_culpable_id,
            comment=request.inspection.comment,
            status=InspectionStatusEnum.REGISTERED,
            synced=True,
        )

        # Save photos
        if request.photos:
            photo_filename = save_photo(request.photos[0].base64, str(inspection.id))
            inspection.photo_path = photo_filename

        db.add(inspection)
        db.commit()
        db.refresh(inspection)

        return {
            "inspection_id": str(inspection.id),
            "synced": True,
        }

    except Exception as e:
        db.rollback()
        return {
            "inspection_id": None,
            "synced": False,
            "error": str(e),
        }
