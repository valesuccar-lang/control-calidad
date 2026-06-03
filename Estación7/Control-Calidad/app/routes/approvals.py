"""Approval API routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from uuid import UUID

from app.database import get_db_session
from app.auth.dependencies import require_role, get_user_id
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.inspection_repository import InspectionRepository
from app.domain.services.approval_service import ApprovalService
from app.schemas.approval_schemas import (
    ApproveInspectionRequest, RejectInspectionRequest, ApprovalResponse
)
from app.monitoring.audit_logger import audit_logger

router = APIRouter()


@router.post("/approve", response_model=ApprovalResponse, status_code=201)
async def approve_inspection(
    request: ApproveInspectionRequest,
    user: dict = Depends(require_role("JEFE_QA")),
    session = Depends(get_db_session)
):
    """Approve an inspection (JEFE_QA role required)"""
    try:
        async with session() as db:
            approval_repo = ApprovalRepository(db)
            inspection_repo = InspectionRepository(db)
            service = ApprovalService(approval_repo, inspection_repo)

            approval = await service.approve_inspection(
                inspection_id=request.inspection_id,
                jefe_qa_id=user.get("sub"),
                notes=request.notes
            )

            audit_logger.log_inspection_approved(
                user_id=user.get("sub"),
                approval_id=str(approval.approval_id),
                inspection_id=str(request.inspection_id),
                decision="APPROVED"
            )

            await db.commit()

            return ApprovalResponse(
                approval_id=approval.approval_id,
                inspection_id=approval.inspection_id,
                jefe_qa_id=approval.jefe_qa_id,
                decision=approval.decision,
                rejection_reason=approval.rejection_reason,
                notes=approval.notes,
                approved_at=approval.approved_at
            )

    except ValueError as e:
        logger.warning("Validation error approving inspection", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error approving inspection", error=str(e), exc_info=e)
        raise HTTPException(status_code=500, detail="Error approving inspection")


@router.post("/reject", response_model=ApprovalResponse, status_code=201)
async def reject_inspection(
    request: RejectInspectionRequest,
    user: dict = Depends(require_role("JEFE_QA")),
    session = Depends(get_db_session)
):
    """Reject an inspection with reason (JEFE_QA role required)"""
    try:
        async with session() as db:
            approval_repo = ApprovalRepository(db)
            inspection_repo = InspectionRepository(db)
            service = ApprovalService(approval_repo, inspection_repo)

            approval = await service.reject_inspection(
                inspection_id=request.inspection_id,
                jefe_qa_id=user.get("sub"),
                rejection_reason=request.rejection_reason,
                notes=request.notes
            )

            audit_logger.log_inspection_approved(
                user_id=user.get("sub"),
                approval_id=str(approval.approval_id),
                inspection_id=str(request.inspection_id),
                decision="REJECTED"
            )

            await db.commit()

            return ApprovalResponse(
                approval_id=approval.approval_id,
                inspection_id=approval.inspection_id,
                jefe_qa_id=approval.jefe_qa_id,
                decision=approval.decision,
                rejection_reason=approval.rejection_reason,
                notes=approval.notes,
                approved_at=approval.approved_at
            )

    except ValueError as e:
        logger.warning("Validation error rejecting inspection", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error rejecting inspection", error=str(e), exc_info=e)
        raise HTTPException(status_code=500, detail="Error rejecting inspection")


@router.get("/pending", response_model=dict)
async def get_pending_approvals(
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(require_role("JEFE_QA", "GERENTE")),
    session = Depends(get_db_session)
):
    """Get pending approvals for jefe QA"""
    try:
        async with session() as db:
            repo = ApprovalRepository(db)
            approvals = await repo.get_by_jefe_qa(user.get("sub"), skip=skip, limit=limit)

            return {
                "total": len(approvals),
                "items": [
                    {
                        "approval_id": str(a.approval_id),
                        "inspection_id": str(a.inspection_id),
                        "decision": a.decision,
                        "rejection_reason": a.rejection_reason,
                        "approved_at": a.approved_at,
                        "created_at": a.created_at
                    }
                    for a in approvals
                ],
                "page": skip // limit,
                "page_size": limit
            }

    except Exception as e:
        logger.error("Error getting pending approvals", error=str(e))
        raise HTTPException(status_code=500, detail="Error getting pending approvals")
