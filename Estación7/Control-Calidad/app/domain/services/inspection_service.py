"""Domain service for inspection business logic"""
from uuid import uuid4
from datetime import datetime
from loguru import logger

from app.domain.entities import Inspection, Comment, Photograph, InspectionTime
from app.repositories.inspection_repository import InspectionRepository


class InspectionService:
    """Domain service implementing inspection business rules"""

    def __init__(self, repo: InspectionRepository):
        self.repo = repo

    async def register_inspection(
        self,
        lote_id: str,
        analista_id: str,
        defect_id: str,
        comment_text: str,
        photo_path: str,
        photo_checksum: str,
        photo_size_kb: int,
        machine_id: str,
        check_in: datetime,
        check_out: datetime = None
    ) -> Inspection:
        """
        Register a new inspection following business rules.
        BR-001: Inspection must have mandatory fields (defect, comment, photo, machine)
        BR-002: Comments must be 10-500 characters
        BR-004: Photos max 500KB
        BR-006: Timestamps generated server-side, not client
        """
        # Validate mandatory fields
        if not all([lote_id, analista_id, defect_id, comment_text, photo_path, machine_id]):
            raise ValueError("Missing mandatory inspection fields")

        # Create value objects with validation
        comment = Comment(text=comment_text)
        photograph = Photograph(
            file_path=photo_path,
            checksum=photo_checksum,
            size_kb=photo_size_kb
        )
        inspection_time = InspectionTime(check_in=check_in, check_out=check_out)

        # Create inspection aggregate
        inspection = Inspection(
            inspection_id=uuid4(),
            lote_id=lote_id,
            analista_id=analista_id,
            defect_id=defect_id,
            comment=comment,
            photograph=photograph,
            machine_id=machine_id,
            inspection_time=inspection_time,
            created_at=datetime.now()
        )

        # Persist
        await self.repo.create(inspection)
        logger.info(
            "Inspection registered",
            inspection_id=str(inspection.inspection_id),
            lote_id=lote_id
        )
        return inspection

    async def mark_synced(self, inspection_id):
        """Mark inspection as successfully synced"""
        inspection = await self.repo.mark_synced(inspection_id)
        if inspection:
            logger.info("Inspection marked as synced", inspection_id=str(inspection_id))
        return inspection

    async def mark_sync_failed(self, inspection_id, error_message: str):
        """Mark inspection sync as failed"""
        inspection = await self.repo.mark_sync_failed(inspection_id, error_message)
        return inspection

    async def get_pending_sync(self):
        """Get all pending inspections for sync"""
        return await self.repo.get_pending_sync()

    async def validate_inspection(self, inspection: Inspection) -> bool:
        """Validate inspection business rules"""
        try:
            # Comment validation (already done in value object)
            _ = inspection.comment
            # Photo validation (already done in value object)
            _ = inspection.photograph
            # Time validation
            if inspection.inspection_time.elapsed_seconds < 0:
                return False
            return True
        except ValueError:
            return False
