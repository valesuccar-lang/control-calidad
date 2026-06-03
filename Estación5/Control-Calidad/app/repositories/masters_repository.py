"""Masters repository - data access for defects, machines, fabrics"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.orm import Defect, Machine, Fabric
from app.repositories.base import BaseRepository


class DefectRepository(BaseRepository[Defect]):
    """Repository for Defect master data"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Defect)

    async def create(self, defect: Defect) -> Defect:
        self.session.add(defect)
        await self.session.flush()
        logger.info("Defect created", defect_id=defect.defect_id)
        return defect

    async def get_by_id(self, defect_id: str) -> Optional[Defect]:
        stmt = select(Defect).where(Defect.defect_id == defect_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Defect]:
        stmt = select(Defect).offset(skip).limit(limit).order_by(Defect.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active(self) -> List[Defect]:
        """Get all active defects for dropdown"""
        stmt = select(Defect).where(Defect.status == "ACTIVE").order_by(Defect.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, defect_id: str, data: dict) -> Optional[Defect]:
        defect = await self.get_by_id(defect_id)
        if defect:
            for key, value in data.items():
                setattr(defect, key, value)
            await self.session.flush()
        return defect

    async def delete(self, defect_id: str) -> bool:
        raise NotImplementedError("Use soft delete by setting status to INACTIVE")

    async def exists(self, defect_id: str) -> bool:
        return await self.get_by_id(defect_id) is not None


class MachineRepository(BaseRepository[Machine]):
    """Repository for Machine master data"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Machine)

    async def create(self, machine: Machine) -> Machine:
        self.session.add(machine)
        await self.session.flush()
        logger.info("Machine created", machine_id=machine.machine_id)
        return machine

    async def get_by_id(self, machine_id: str) -> Optional[Machine]:
        stmt = select(Machine).where(Machine.machine_id == machine_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Machine]:
        stmt = select(Machine).offset(skip).limit(limit).order_by(Machine.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active(self) -> List[Machine]:
        """Get all active machines for dropdown"""
        stmt = select(Machine).where(Machine.status == "ACTIVE").order_by(Machine.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, machine_id: str, data: dict) -> Optional[Machine]:
        machine = await self.get_by_id(machine_id)
        if machine:
            for key, value in data.items():
                setattr(machine, key, value)
            await self.session.flush()
        return machine

    async def delete(self, machine_id: str) -> bool:
        raise NotImplementedError("Use soft delete by setting status to INACTIVE")

    async def exists(self, machine_id: str) -> bool:
        return await self.get_by_id(machine_id) is not None


class FabricRepository(BaseRepository[Fabric]):
    """Repository for Fabric master data"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Fabric)

    async def create(self, fabric: Fabric) -> Fabric:
        self.session.add(fabric)
        await self.session.flush()
        logger.info("Fabric created", fabric_id=fabric.fabric_id)
        return fabric

    async def get_by_id(self, fabric_id: str) -> Optional[Fabric]:
        stmt = select(Fabric).where(Fabric.fabric_id == fabric_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Fabric]:
        stmt = select(Fabric).offset(skip).limit(limit).order_by(Fabric.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active(self) -> List[Fabric]:
        """Get all active fabrics for dropdown"""
        stmt = select(Fabric).where(Fabric.status == "ACTIVE").order_by(Fabric.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, fabric_id: str, data: dict) -> Optional[Fabric]:
        fabric = await self.get_by_id(fabric_id)
        if fabric:
            for key, value in data.items():
                setattr(fabric, key, value)
            await self.session.flush()
        return fabric

    async def delete(self, fabric_id: str) -> bool:
        raise NotImplementedError("Use soft delete by setting status to INACTIVE")

    async def exists(self, fabric_id: str) -> bool:
        return await self.get_by_id(fabric_id) is not None
