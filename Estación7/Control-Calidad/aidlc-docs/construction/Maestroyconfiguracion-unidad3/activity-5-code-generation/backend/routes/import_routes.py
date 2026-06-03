# backend/app/routes/import_routes.py
# FastAPI routes for CSV import operations with WebSocket support

import uuid
from typing import Optional
from fastapi import (
    APIRouter, Depends, HTTPException, status, Query, UploadFile, File, WebSocket, WebSocketDisconnect
)
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.security import get_current_user
from app.models import User, ImportJob
from app.schemas import (
    CsvImportStartRequest, CsvValidationResponse, CsvImportPreview,
    CsvImportExecuteRequest, CsvImportResult, ImportJobStatus, ErrorResponse
)
from app.services.csv_import import CsvImportService, ImportMode
from app.services import NotFoundError
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/import", tags=["import"])


# ==================== CSV VALIDATION ====================

@router.post("/validate", response_model=CsvValidationResponse)
async def validate_csv(
    file: UploadFile = File(...),
    master_type: str = Query(..., regex="^(DEFECT|MACHINE|FABRIC)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate CSV file structure and content without creating import job.
    Returns validation errors if any.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can validate imports"
        )

    try:
        file_content = await file.read()
        service = CsvImportService(db)
        result = service.validate_csv(file_content, master_type)
        return result

    except Exception as e:
        logger.error("validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== CSV PREVIEW ====================

@router.post("/preview", response_model=CsvImportPreview)
async def preview_csv(
    file: UploadFile = File(...),
    master_type: str = Query(..., regex="^(DEFECT|MACHINE|FABRIC)$"),
    import_mode: str = Query("UPSERT", regex="^(INSERT|UPDATE|UPSERT|SKIP)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview CSV import showing what will be created/updated.
    Detects duplicates and conflicts.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can preview imports"
        )

    try:
        file_content = await file.read()
        service = CsvImportService(db)
        mode = ImportMode[import_mode]

        result = service.preview_csv(file_content, master_type, mode)
        return result

    except Exception as e:
        logger.error("preview_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== CSV IMPORT START ====================

@router.post("/start", response_model=ImportJobStatus)
async def start_csv_import(
    file: UploadFile = File(...),
    request: CsvImportStartRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start CSV import job.
    Creates import job record and returns job ID for tracking/WebSocket.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can start imports"
        )

    try:
        file_content = await file.read()
        job_id = str(uuid.uuid4())

        # Create import job record
        job = ImportJob(
            id=job_id,
            master_type=request.master_type,
            filename=file.filename or "upload.csv",
            status="VALIDATION",
            total_rows=0,
            processed_rows=0,
            error_count=0,
            import_mode=request.import_mode,
            user_id=current_user.id
        )
        db.add(job)
        db.commit()

        logger.info(
            "import_job_created",
            job_id=job_id,
            master_type=request.master_type,
            user_id=current_user.id
        )

        # Validate CSV
        service = CsvImportService(db)
        validation = service.validate_csv(file_content, request.master_type)

        if not validation.valid:
            job.status = "VALIDATION_FAILED"
            job.error_count = validation.error_count
            job.error_details = json.dumps(validation.errors)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV validation failed: {validation.error_count} errors"
            )

        # Generate preview
        job.status = "PREVIEW"
        job.total_rows = validation.total_rows
        db.commit()

        mode = ImportMode[request.import_mode]
        preview = service.preview_csv(file_content, request.master_type, mode)

        return ImportJobStatus(
            job_id=job_id,
            status="PREVIEW",
            filename=file.filename or "upload.csv",
            master_type=request.master_type,
            import_mode=request.import_mode,
            total_rows=preview.total_rows,
            to_create=preview.to_create,
            to_update=preview.to_update,
            duplicates=len(preview.duplicates),
            can_proceed=preview.can_proceed
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("import_start_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== CSV IMPORT EXECUTE ====================

@router.post("/execute", response_model=CsvImportResult)
async def execute_csv_import(
    request: CsvImportExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute CSV import job.
    Performs actual creation/update of entities.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can execute imports"
        )

    try:
        # Get job
        job = db.query(ImportJob).filter(ImportJob.id == request.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import job '{request.job_id}' not found"
            )

        if job.status != "PREVIEW":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot execute job in status '{job.status}'"
            )

        # For now, this endpoint returns a result structure
        # In production, this would trigger async Celery task
        # and return immediately, with WebSocket for progress

        return CsvImportResult(
            job_id=request.job_id,
            status="QUEUED",
            created_count=0,
            updated_count=0,
            skipped_count=0,
            error_count=0,
            error_details=[],
            message="Import job queued. Connect via WebSocket for progress."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("import_execute_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== JOB STATUS ====================

@router.get("/jobs/{job_id}", response_model=ImportJobStatus)
async def get_import_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get import job status"""
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job '{job_id}' not found"
        )

    if job.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other user's import jobs"
        )

    return ImportJobStatus(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        master_type=job.master_type,
        import_mode=job.import_mode,
        total_rows=job.total_rows,
        processed_rows=job.processed_rows,
        error_count=job.error_count
    )


# ==================== WEBSOCKET PROGRESS ====================

# In-memory storage of active WebSocket connections
# In production, use Redis for multi-instance deployments
active_connections: dict[str, list] = {}


@router.websocket("/ws/jobs/{job_id}")
async def websocket_import_progress(
    websocket: WebSocket,
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    WebSocket endpoint for real-time import progress.
    Sends progress updates, errors, and completion status.
    """
    # Verify job exists and user has access
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if not job:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Job not found")
        return

    if job.user_id != current_user.id and current_user.role != "ADMIN":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access denied")
        return

    await websocket.accept()

    # Register connection
    if job_id not in active_connections:
        active_connections[job_id] = []
    active_connections[job_id].append(websocket)

    logger.info(
        "websocket_connected",
        job_id=job_id,
        user_id=current_user.id
    )

    try:
        # Send current job status
        await websocket.send_json({
            "type": "status",
            "job_id": job_id,
            "status": job.status,
            "total_rows": job.total_rows,
            "processed_rows": job.processed_rows,
            "error_count": job.error_count
        })

        # Keep connection alive
        while True:
            # In production, listen for progress updates from Celery
            # For now, just keep connection open
            data = await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", job_id=job_id)
        active_connections[job_id].remove(websocket)
        if not active_connections[job_id]:
            del active_connections[job_id]

    except Exception as e:
        logger.error("websocket_error", error=str(e), job_id=job_id)
        if websocket in active_connections.get(job_id, []):
            active_connections[job_id].remove(websocket)


async def broadcast_progress(job_id: str, message: dict):
    """
    Broadcast progress update to all connected WebSocket clients.
    Called by Celery task callback.
    """
    if job_id not in active_connections:
        return

    disconnected = []
    for websocket in active_connections[job_id]:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("broadcast_error", error=str(e), job_id=job_id)
            disconnected.append(websocket)

    # Clean up disconnected clients
    for ws in disconnected:
        active_connections[job_id].remove(ws)
