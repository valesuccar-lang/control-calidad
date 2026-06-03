"""Domain service for approval business logic"""
from uuid import uuid4
from datetime import datetime
from loguru import logger

from app.domain.entities import Approval
from app.repositories.approval_repository import ApprovalRepository
from app.repositories.inspection_repository import InspectionRepository


class ApprovalService:
    """Domain service implementing approval business rules"""

    def __init__(self, approval_repo: ApprovalRepository, inspection_repo: InspectionRepository):
        self.approval_repo = approval_repo
        self.inspection_repo = inspection_repo

    async def approve_inspection(
        self,
        inspection_id,
        jefe_qa_id: str,
        notes: str = None
    ) -> Approval:
        """
        Approve an inspection.
        BR-007: One approval per inspection
        BR-008: Approval is immutable
        """
        # Check if already approved (BR-007)
        existing = await self.approval_repo.get_by_inspection_id(inspection_id)
        if existing:
            raise ValueError(f"Inspection already approved: {inspection_id}")

        # Verify inspection exists
        inspection = await self.inspection_repo.get_by_id(inspection_id)
        if not inspection:
            raise ValueError(f"Inspection not found: {inspection_id}")

        # Create approval
        approval = Approval(
            approval_id=uuid4(),
            inspection_id=inspection_id,
            jefe_qa_id=jefe_qa_id,
            decision="APPROVED",
            notes=notes,
            approved_at=datetime.now()
        )

        approval.validate()
        await self.approval_repo.create(approval)
        logger.info(
            "Inspection approved",
            approval_id=str(approval.approval_id),
            inspection_id=str(inspection_id)
        )
        return approval

    async def reject_inspection(
        self,
        inspection_id,
        jefe_qa_id: str,
        rejection_reason: str,
        notes: str = None
    ) -> Approval:
        """
        Reject an inspection.
        BR-007: One approval per inspection
        BR-009: Rejection requires reason
        BR-008: Approval is immutable
        """
        # Check if already approved
        existing = await self.approval_repo.get_by_inspection_id(inspection_id)
        if existing:
            raise ValueError(f"Inspection already approved: {inspection_id}")

        # Verify inspection exists
        inspection = await self.inspection_repo.get_by_id(inspection_id)
        if not inspection:
            raise ValueError(f"Inspection not found: {inspection_id}")

        # Validate rejection reason (BR-009)
        if not rejection_reason or len(rejection_reason) < 10:
            raise ValueError("Rejection reason must be at least 10 characters")

        # Create approval with rejection
        approval = Approval(
            approval_id=uuid4(),
            inspection_id=inspection_id,
            jefe_qa_id=jefe_qa_id,
            decision="REJECTED",
            rejection_reason=rejection_reason,
            notes=notes,
            approved_at=datetime.now()
        )

        approval.validate()
        await self.approval_repo.create(approval)
        logger.info(
            "Inspection rejected",
            approval_id=str(approval.approval_id),
            inspection_id=str(inspection_id)
        )
        return approval

    async def get_pending_approvals(self, jefe_qa_id: str = None):
        """Get pending approvals for jefe QA"""
        if jefe_qa_id:
            return await self.approval_repo.get_by_jefe_qa(jefe_qa_id)
        return await self.approval_repo.get_pending()
