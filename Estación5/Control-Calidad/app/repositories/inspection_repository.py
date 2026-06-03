"""Inspection repository - data access for inspections"""
from typing import List, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from loguru import logger

from app.models.orm import Inspection as InspectionORM, SyncStatus
from app.repositories.base import BaseRepository

import app.domain.entities as domain


class InspectionRepository(BaseRepository[InspectionORM]):
    """Repository for Inspection aggregate"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, InspectionORM)

    def _to_orm(self, entity: domain.Inspection) -> InspectionORM:
        """Convert domain entity to ORM model."""
        return InspectionORM(
            inspection_id=entity.inspection_id,
            lote_id=entity.lote_id,
            analista_id=entity.analista_id,
            defect_id=entity.defect_id,
            comment_text=entity.comment.text,
            photo_path=entity.photograph.file_path,
            photo_checksum=entity.photograph.checksum,
            machine_id=entity.machine_id,
            check_in=entity.inspection_time.check_in,
            check_out=entity.inspection_time.check_out,
            elapsed_seconds=entity.inspection_time.elapsed_seconds,
            sync_status=SyncStatus(entity.sync_status.value),
            created_at=entity.created_at,
        )

    async def create(self, inspection: Union[domain.Inspection, InspectionORM]) -> InspectionORM:
        """Create new inspection (accepts domain entity or ORM model)."""
        if isinstance(inspection, domain.Inspection):
            orm_obj = self._to_orm(inspection)
        else:
            orm_obj = inspection
        self.session.add(orm_obj)
        await self.session.flush()
        logger.info("Inspection created", inspection_id=str(orm_obj.inspection_id))
        return orm_obj

    async def get_by_id(self, inspection_id: UUID) -> Optional[InspectionORM]:
        """Get inspection by ID"""
        stmt = select(InspectionORM).where(InspectionORM.inspection_id == inspection_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[InspectionORM]:
        """Get all inspections with pagination"""
        stmt = (
            select(InspectionORM)
            .offset(skip)
            .limit(limit)
            .order_by(InspectionORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_lote_id(self, lote_id: str) -> List[InspectionORM]:
        """Get all inspections for a lote"""
        stmt = (
            select(InspectionORM)
            .where(InspectionORM.lote_id == lote_id)
            .order_by(InspectionORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_sync(self) -> List[InspectionORM]:
        """Get all inspections pending synchronization"""
        stmt = select(InspectionORM).where(
            InspectionORM.sync_status == SyncStatus.PENDING
        ).order_by(InspectionORM.created_at.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_analista(self, analista_id: str, skip: int = 0, limit: int = 100) -> List[InspectionORM]:
        """Get inspections by analista"""
        stmt = (
            select(InspectionORM)
            .where(InspectionORM.analista_id == analista_id)
            .offset(skip)
            .limit(limit)
            .order_by(InspectionORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, inspection_id: UUID, data: dict) -> Optional[InspectionORM]:
        """Update inspection"""
        inspection = await self.get_by_id(inspection_id)
        if inspection:
            for key, value in data.items():
                setattr(inspection, key, value)
            await self.session.flush()
            logger.info("Inspection updated", inspection_id=str(inspection_id))
        return inspection

    async def mark_synced(self, inspection_id: UUID) -> Optional[InspectionORM]:
        """Mark inspection as synced"""
        return await self.update(inspection_id, {
            "sync_status": SyncStatus.SYNCED,
            "sync_attempts": 0
        })

    async def mark_sync_failed(self, inspection_id: UUID, error: str) -> Optional[InspectionORM]:
        """Mark inspection sync as failed"""
        inspection = await self.get_by_id(inspection_id)
        if inspection:
            inspection.sync_status = SyncStatus.SYNC_FAILED
            inspection.sync_attempts = (inspection.sync_attempts or 0) + 1
            inspection.last_sync_error = error
            await self.session.flush()
            logger.warning(
                "Inspection sync failed",
                inspection_id=str(inspection_id),
                attempts=inspection.sync_attempts,
                error=error
            )
        return inspection

    async def delete(self, inspection_id: UUID) -> bool:
        """Delete inspection (not implemented - immutable)"""
        raise NotImplementedError("Inspections are immutable and cannot be deleted")

    async def exists(self, inspection_id: UUID) -> bool:
        """Check if inspection exists"""
        return await self.get_by_id(inspection_id) is not None
