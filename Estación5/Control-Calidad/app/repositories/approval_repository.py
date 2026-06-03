"""Approval repository - data access for approvals"""
from typing import List, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from loguru import logger

from app.models.orm import Approval as ApprovalORM, ApprovalStatus
from app.repositories.base import BaseRepository

import app.domain.entities as domain


class ApprovalRepository(BaseRepository[ApprovalORM]):
    """Repository for Approval aggregate"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ApprovalORM)

    def _to_orm(self, entity: domain.Approval) -> ApprovalORM:
        """Convert domain entity to ORM model."""
        return ApprovalORM(
            approval_id=entity.approval_id,
            inspection_id=entity.inspection_id,
            jefe_qa_id=entity.jefe_qa_id,
            decision=ApprovalStatus(entity.decision),
            rejection_reason=entity.rejection_reason,
            notes=entity.notes,
            approved_at=entity.approved_at,
        )

    async def create(self, approval: Union[domain.Approval, ApprovalORM]) -> ApprovalORM:
        """Create new approval (accepts domain entity or ORM model)."""
        if isinstance(approval, domain.Approval):
            orm_obj = self._to_orm(approval)
        else:
            orm_obj = approval
        self.session.add(orm_obj)
        await self.session.flush()
        logger.info("Approval created", approval_id=str(orm_obj.approval_id))
        return orm_obj

    async def get_by_id(self, approval_id: UUID) -> Optional[ApprovalORM]:
        """Get approval by ID"""
        stmt = select(ApprovalORM).where(ApprovalORM.approval_id == approval_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_inspection_id(self, inspection_id: UUID) -> Optional[ApprovalORM]:
        """Get approval for an inspection"""
        stmt = select(ApprovalORM).where(ApprovalORM.inspection_id == inspection_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ApprovalORM]:
        """Get all approvals with pagination"""
        stmt = (
            select(ApprovalORM)
            .offset(skip)
            .limit(limit)
            .order_by(ApprovalORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending(self) -> List[ApprovalORM]:
        """Get pending approvals"""
        stmt = (
            select(ApprovalORM)
            .where(ApprovalORM.decision == ApprovalStatus.APPROVED)
            .order_by(ApprovalORM.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_jefe_qa(self, jefe_qa_id: str, skip: int = 0, limit: int = 100) -> List[ApprovalORM]:
        """Get approvals by jefe QA"""
        stmt = (
            select(ApprovalORM)
            .where(ApprovalORM.jefe_qa_id == jefe_qa_id)
            .offset(skip)
            .limit(limit)
            .order_by(ApprovalORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, approval_id: UUID, data: dict) -> Optional[ApprovalORM]:
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
