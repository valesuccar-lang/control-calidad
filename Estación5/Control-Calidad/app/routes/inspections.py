"""Inspection API routes"""
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from uuid import UUID

from app.database import get_db_session
from app.auth.dependencies import require_role
from app.repositories.inspection_repository import InspectionRepository
from app.domain.services.inspection_service import InspectionService
from app.schemas.inspection_schemas import (
    CreateInspectionRequest, InspectionResponse, SyncBatchRequest, SyncBatchResponse
)
from app.monitoring.audit_logger import audit_logger

router = APIRouter()


@router.post("", response_model=InspectionResponse, status_code=201)
async def create_inspection(
    request: CreateInspectionRequest,
    user: dict = Depends(require_role("ANALISTA")),
    session = Depends(get_db_session)
):
    """Create a new inspection (ANALISTA role required)"""
    try:
        async with session() as db:
            repo = InspectionRepository(db)
            service = InspectionService(repo)

            from datetime import datetime
            inspection = await service.register_inspection(
                lote_id=request.lote_id,
                analista_id=user.get("sub"),
                defect_id=request.defect_id,
                comment_text=request.comment_text,
                photo_path=request.photo_path,
                photo_checksum=request.photo_checksum,
                photo_size_kb=request.photo_size_kb,
                machine_id=request.machine_id,
                check_in=datetime.now()
            )

            audit_logger.log_inspection_created(
                user_id=user.get("sub"),
                inspection_id=str(inspection.inspection_id),
                lote_id=request.lote_id
            )

            await db.commit()

            return InspectionResponse(
                inspection_id=inspection.inspection_id,
                lote_id=inspection.lote_id,
                analista_id=inspection.analista_id,
                defect_id=inspection.defect_id,
                comment_text=inspection.comment.text,
                photo_path=inspection.photograph.file_path,
                photo_checksum=inspection.photograph.checksum,
                machine_id=inspection.machine_id,
                check_in=inspection.inspection_time.check_in,
                check_out=inspection.inspection_time.check_out,
                elapsed_seconds=inspection.inspection_time.elapsed_seconds,
                sync_status=inspection.sync_status.value,
                created_at=inspection.created_at
            )

    except ValueError as e:
        logger.error("Validation error creating inspection", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating inspection", error=str(e), exc_info=e)
        raise HTTPException(status_code=500, detail="Error creating inspection")


@router.post("/sync-batch", response_model=SyncBatchResponse, status_code=200)
async def sync_batch(
    request: SyncBatchRequest,
    user: dict = Depends(require_role("ANALISTA")),
    session = Depends(get_db_session)
):
    """Batch sync multiple pending inspections"""
    try:
        async with session() as db:
            synced = 0
            failed = 0
            details = []

            for inspection_req in request.inspections:
                try:
                    repo = InspectionRepository(db)
                    service = InspectionService(repo)

                    from datetime import datetime
                    inspection = await service.register_inspection(
                        lote_id=inspection_req.lote_id,
                        analista_id=user.get("sub"),
                        defect_id=inspection_req.defect_id,
                        comment_text=inspection_req.comment_text,
                        photo_path=inspection_req.photo_path,
                        photo_checksum=inspection_req.photo_checksum,
                        photo_size_kb=inspection_req.photo_size_kb,
                        machine_id=inspection_req.machine_id,
                        check_in=datetime.now()
                    )
                    synced += 1
                    details.append({"inspection_id": str(inspection.inspection_id), "status": "synced"})

                except Exception as e:
                    failed += 1
                    details.append({"error": str(e), "status": "failed"})

            await db.commit()

            return SyncBatchResponse(
                synced_count=synced,
                failed_count=failed,
                details=details
            )

    except Exception as e:
        logger.error("Error in batch sync", error=str(e))
        raise HTTPException(status_code=500, detail="Error in batch sync")


@router.get("", response_model=dict)
async def list_inspections(
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_role("ANALISTA", "JEFE_QA", "ADMIN")),
    session = Depends(get_db_session)
):
    """List inspections with pagination"""
    try:
        async with session() as db:
            repo = InspectionRepository(db)
            inspections = await repo.get_all(skip=skip, limit=limit)

            return {
                "total": len(inspections),
                "items": [
                    {
                        "inspection_id": str(i.inspection_id),
                        "lote_id": i.lote_id,
                        "analista_id": i.analista_id,
                        "defect_id": i.defect_id,
                        "comment_text": i.comment_text,
                        "photo_path": i.photo_path,
                        "machine_id": i.machine_id,
                        "check_in": i.check_in,
                        "sync_status": i.sync_status,
                        "created_at": i.created_at
                    }
                    for i in inspections
                ],
                "page": skip // limit,
                "page_size": limit
            }

    except Exception as e:
        logger.error("Error listing inspections", error=str(e))
        raise HTTPException(status_code=500, detail="Error listing inspections")


@router.get("/{inspection_id}", response_model=InspectionResponse)
async def get_inspection(
    inspection_id: UUID,
    user: dict = Depends(require_role("ANALISTA", "JEFE_QA", "ADMIN")),
    session = Depends(get_db_session)
):
    """Get a specific inspection by ID"""
    try:
        async with session() as db:
            repo = InspectionRepository(db)
            inspection = await repo.get_by_id(inspection_id)

            if not inspection:
                raise HTTPException(status_code=404, detail="Inspection not found")

            return InspectionResponse(
                inspection_id=inspection.inspection_id,
                lote_id=inspection.lote_id,
                analista_id=inspection.analista_id,
                defect_id=inspection.defect_id,
                comment_text=inspection.comment_text,
                photo_path=inspection.photo_path,
                photo_checksum=inspection.photo_checksum,
                machine_id=inspection.machine_id,
                check_in=inspection.check_in,
                check_out=inspection.check_out,
                elapsed_seconds=inspection.elapsed_seconds,
                sync_status=inspection.sync_status,
                created_at=inspection.created_at
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting inspection", error=str(e))
        raise HTTPException(status_code=500, detail="Error getting inspection")
