"""Audit log repository - persist audit events to database"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import json

from app.models.orm import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog persistence"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLog)

    async def create(self, audit_log: AuditLog) -> AuditLog:
        """Create audit log entry"""
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log

    async def log_event(
        self,
        user_id: Optional[str],
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        status: str = "SUCCESS",
        error_message: str = None
    ) -> AuditLog:
        """Log an event with details"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details or {}),
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        return await self.create(audit_log)

    async def get_by_id(self, audit_id: UUID) -> Optional[AuditLog]:
        """Get audit log by ID"""
        stmt = select(AuditLog).where(AuditLog.id == audit_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get all audit logs with pagination"""
        stmt = (
            select(AuditLog)
            .offset(skip)
            .limit(limit)
            .order_by(AuditLog.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a user"""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(AuditLog.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for an entity"""
        stmt = (
            select(AuditLog)
            .where((AuditLog.entity_type == entity_type) & (AuditLog.entity_id == entity_id))
            .offset(skip)
            .limit(limit)
            .order_by(AuditLog.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_action(self, action: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get audit logs by action type"""
        stmt = (
            select(AuditLog)
            .where(AuditLog.action == action)
            .offset(skip)
            .limit(limit)
            .order_by(AuditLog.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, audit_id: UUID, data: dict) -> Optional[AuditLog]:
        """Update is not supported for immutable audit logs"""
        raise NotImplementedError("Audit logs are immutable")

    async def delete(self, audit_id: UUID) -> bool:
        """Delete is not supported for audit logs"""
        raise NotImplementedError("Audit logs cannot be deleted")

    async def exists(self, audit_id: UUID) -> bool:
        """Check if audit log exists"""
        return await self.get_by_id(audit_id) is not None
