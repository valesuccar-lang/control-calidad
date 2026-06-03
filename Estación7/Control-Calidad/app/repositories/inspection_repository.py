"""Inspection repository - data access for inspections"""
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from loguru import logger

from app.models.orm import Inspection, SyncStatus
from app.repositories.base import BaseRepository


class InspectionRepository(BaseRepository[Inspection]):
    """Repository for Inspection aggregate"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Inspection)

    async def create(self, inspection: Inspection) -> Inspection:
        """Create new inspection"""
        self.session.add(inspection)
        await self.session.flush()
        logger.info("Inspection created", inspection_id=str(inspection.inspection_id))
        return inspection

    async def get_by_id(self, inspection_id: UUID) -> Optional[Inspection]:
        """Get inspection by ID"""
        stmt = select(Inspection).where(Inspection.inspection_id == inspection_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Inspection]:
        """Get all inspections with pagination"""
        stmt = (
            select(Inspection)
            .offset(skip)
            .limit(limit)
            .order_by(Inspection.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_lote_id(self, lote_id: str) -> List[Inspection]:
        """Get all inspections for a lote"""
        stmt = (
            select(Inspection)
            .where(Inspection.lote_id == lote_id)
            .order_by(Inspection.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_sync(self) -> List[Inspection]:
        """Get all inspections pending synchronization"""
        stmt = select(Inspection).where(
            Inspection.sync_status == SyncStatus.PENDING
        ).order_by(Inspection.created_at.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_analista(self, analista_id: str, skip: int = 0, limit: int = 100) -> List[Inspection]:
        """Get inspections by analista"""
        stmt = (
            select(Inspection)
            .where(Inspection.analista_id == analista_id)
            .offset(skip)
            .limit(limit)
            .order_by(Inspection.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, inspection_id: UUID, data: dict) -> Optional[Inspection]:
        """Update inspection"""
        inspection = await self.get_by_id(inspection_id)
        if inspection:
            for key, value in data.items():
                setattr(inspection, key, value)
            await self.session.flush()
            logger.info("Inspection updated", inspection_id=str(inspection_id))
        return inspection

    async def mark_synced(self, inspection_id: UUID) -> Optional[Inspection]:
        """Mark inspection as synced"""
        return await self.update(inspection_id, {
            "sync_status": SyncStatus.SYNCED,
            "sync_attempts": 0
        })

    async def mark_sync_failed(self, inspection_id: UUID, error: str) -> Optional[Inspection]:
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
