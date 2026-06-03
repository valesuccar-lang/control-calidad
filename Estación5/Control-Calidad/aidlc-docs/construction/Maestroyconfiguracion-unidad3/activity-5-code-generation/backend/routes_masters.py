# backend/app/routes_masters.py
# FastAPI routes for master data CRUD operations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.security import get_current_user, require_role
from app.models import User
from app.schemas import (
    DefectCreate, DefectUpdate, DefectResponse, DefectListResponse,
    MachineCreate, MachineUpdate, MachineResponse, MachineListResponse,
    FabricCreate, FabricUpdate, FabricResponse, FabricListResponse,
    ArchiveRequest, ArchiveResponse, ErrorResponse, PaginationParams
)
from app.services import (
    MastersService, DuplicateError, ValidationError,
    ArchiveError, NotFoundError
)

router = APIRouter(prefix="/api/v1/masters", tags=["masters"])


# ==================== DEFECT ROUTES ====================

@router.get("/defects", response_model=DefectListResponse)
async def list_defects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List defects with pagination and optional search"""
    service = MastersService(db)

    skip = (page - 1) * page_size

    if search:
        items, total = service.defect_repo.search_by_name(search, skip, page_size)
    else:
        items, total = service.list_defects(skip, page_size, include_archived)

    has_more = (skip + page_size) < total

    return DefectListResponse(
        items=[DefectResponse.from_orm(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/defects/{defect_id}", response_model=DefectResponse)
async def get_defect(
    defect_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get defect detail"""
    service = MastersService(db)
    defect = service.get_defect(defect_id)

    if not defect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect '{defect_id}' not found"
        )

    return DefectResponse.from_orm(defect)


@router.post("/defects", response_model=DefectResponse, status_code=status.HTTP_201_CREATED)
async def create_defect(
    payload: DefectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new defect (ADMIN only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can create defects"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        defect = service.create_defect(payload, user_id=current_user.id, trace_id=trace_id)
        return DefectResponse.from_orm(defect)
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/defects/{defect_id}", response_model=DefectResponse)
async def update_defect(
    defect_id: str,
    payload: DefectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update defect (ADMIN only, includes version check for concurrency)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update defects"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        defect = service.update_defect(defect_id, payload, user_id=current_user.id, trace_id=trace_id)
        return DefectResponse.from_orm(defect)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        if "version" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/defects/{defect_id}/archive", response_model=ArchiveResponse)
async def archive_defect(
    defect_id: str,
    request: ArchiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive defect (soft delete, with validation)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can archive defects"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        service.archive_defect(defect_id, request.reason, user_id=current_user.id, trace_id=trace_id)
        return ArchiveResponse(success=True, message=f"Defect '{defect_id}' archived successfully")
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ArchiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== MACHINE ROUTES ====================

@router.get("/machines", response_model=MachineListResponse)
async def list_machines(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List machines with pagination"""
    service = MastersService(db)
    skip = (page - 1) * page_size

    if search:
        items, total = service.machine_repo.search_by_name(search, skip, page_size)
    else:
        items, total = service.list_machines(skip, page_size, include_archived)

    has_more = (skip + page_size) < total

    return MachineListResponse(
        items=[MachineResponse.from_orm(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/machines/{machine_id}", response_model=MachineResponse)
async def get_machine(
    machine_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get machine detail"""
    service = MastersService(db)
    machine = service.get_machine(machine_id)

    if not machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine '{machine_id}' not found"
        )

    return MachineResponse.from_orm(machine)


@router.post("/machines", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
async def create_machine(
    payload: MachineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new machine (ADMIN only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can create machines"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        machine = service.create_machine(payload, user_id=current_user.id, trace_id=trace_id)
        return MachineResponse.from_orm(machine)
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/machines/{machine_id}", response_model=MachineResponse)
async def update_machine(
    machine_id: str,
    payload: MachineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update machine (ADMIN only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update machines"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        machine = service.update_machine(machine_id, payload, user_id=current_user.id, trace_id=trace_id)
        return MachineResponse.from_orm(machine)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        if "version" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/machines/{machine_id}/archive", response_model=ArchiveResponse)
async def archive_machine(
    machine_id: str,
    request: ArchiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive machine (soft delete)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can archive machines"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        service.archive_machine(machine_id, request.reason, user_id=current_user.id, trace_id=trace_id)
        return ArchiveResponse(success=True, message=f"Machine '{machine_id}' archived successfully")
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ArchiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== FABRIC ROUTES ====================

@router.get("/fabrics", response_model=FabricListResponse)
async def list_fabrics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List fabrics with pagination"""
    service = MastersService(db)
    skip = (page - 1) * page_size

    if search:
        items, total = service.fabric_repo.search_by_name(search, skip, page_size)
    else:
        items, total = service.list_fabrics(skip, page_size, include_archived)

    has_more = (skip + page_size) < total

    return FabricListResponse(
        items=[FabricResponse.from_orm(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/fabrics/{fabric_id}", response_model=FabricResponse)
async def get_fabric(
    fabric_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get fabric detail"""
    service = MastersService(db)
    fabric = service.get_fabric(fabric_id)

    if not fabric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fabric '{fabric_id}' not found"
        )

    return FabricResponse.from_orm(fabric)


@router.post("/fabrics", response_model=FabricResponse, status_code=status.HTTP_201_CREATED)
async def create_fabric(
    payload: FabricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new fabric (ADMIN only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can create fabrics"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        fabric = service.create_fabric(payload, user_id=current_user.id, trace_id=trace_id)
        return FabricResponse.from_orm(fabric)
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/fabrics/{fabric_id}", response_model=FabricResponse)
async def update_fabric(
    fabric_id: str,
    payload: FabricUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update fabric (ADMIN only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can update fabrics"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        fabric = service.update_fabric(fabric_id, payload, user_id=current_user.id, trace_id=trace_id)
        return FabricResponse.from_orm(fabric)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        if "version" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/fabrics/{fabric_id}/archive", response_model=ArchiveResponse)
async def archive_fabric(
    fabric_id: str,
    request: ArchiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive fabric (soft delete)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can archive fabrics"
        )

    trace_id = str(uuid.uuid4())
    service = MastersService(db)

    try:
        service.archive_fabric(fabric_id, request.reason, user_id=current_user.id, trace_id=trace_id)
        return ArchiveResponse(success=True, message=f"Fabric '{fabric_id}' archived successfully")
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ArchiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
