"""Approval repository - data access for approvals"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from loguru import logger

from app.models.orm import Approval, ApprovalStatus
from app.repositories.base import BaseRepository


class ApprovalRepository(BaseRepository[Approval]):
    """Repository for Approval aggregate"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Approval)

    async def create(self, approval: Approval) -> Approval:
        """Create new approval"""
        self.session.add(approval)
        await self.session.flush()
        logger.info("Approval created", approval_id=str(approval.approval_id))
        return approval

    async def get_by_id(self, approval_id: UUID) -> Optional[Approval]:
        """Get approval by ID"""
        stmt = select(Approval).where(Approval.approval_id == approval_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_inspection_id(self, inspection_id: UUID) -> Optional[Approval]:
        """Get approval for an inspection"""
        stmt = select(Approval).where(Approval.inspection_id == inspection_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Approval]:
        """Get all approvals with pagination"""
        stmt = (
            select(Approval)
            .offset(skip)
            .limit(limit)
            .order_by(Approval.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending(self) -> List[Approval]:
        """Get pending approvals"""
        stmt = (
            select(Approval)
            .where(Approval.decision == ApprovalStatus.APPROVED)
            .order_by(Approval.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_jefe_qa(self, jefe_qa_id: str, skip: int = 0, limit: int = 100) -> List[Approval]:
        """Get approvals by jefe QA"""
        stmt = (
            select(Approval)
            .where(Approval.jefe_qa_id == jefe_qa_id)
            .offset(skip)
            .limit(limit)
            .order_by(Approval.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, approval_id: UUID, data: dict) -> Optional[Approval]:
        """Update approval"""
        approval = await self.get_by_id(approval_id)
        if approval:
            for key, value in data.items():
                setattr(approval, key, value)
            await self.session.flush()
            logger.info("Approval updated", approval_id=str(approval_id))
        return approval

    async def delete(self, approval_id: UUID) -> bool:
        """Delete approval (not implemented - immutable)"""
        raise NotImplementedError("Approvals are immutable and cannot be deleted")

    async def exists(self, approval_id: UUID) -> bool:
        """Check if approval exists"""
        return await self.get_by_id(approval_id) is not None
