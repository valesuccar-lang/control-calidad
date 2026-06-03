"""Base repository interface for data access"""
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for all data access"""

    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: any) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        pass

    @abstractmethod
    async def update(self, entity_id: any, data: dict) -> Optional[T]:
        """Update an entity"""
        pass

    @abstractmethod
    async def delete(self, entity_id: any) -> bool:
        """Delete an entity (soft delete if applicable)"""
        pass

    @abstractmethod
    async def exists(self, entity_id: any) -> bool:
        """Check if entity exists"""
        pass
