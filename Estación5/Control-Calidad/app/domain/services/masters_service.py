"""Domain service for masters data business logic"""
from loguru import logger
from typing import List

from app.models.orm import Defect, Machine, Fabric
from app.repositories.masters_repository import DefectRepository, MachineRepository, FabricRepository


class MastersService:
    """Domain service for managing master data (defects, machines, fabrics)"""

    def __init__(
        self,
        defect_repo: DefectRepository,
        machine_repo: MachineRepository,
        fabric_repo: FabricRepository
    ):
        self.defect_repo = defect_repo
        self.machine_repo = machine_repo
        self.fabric_repo = fabric_repo

    # ==================== DEFECTS ====================
    async def create_defect(self, defect_id: str, name: str, category: str, severity: str = "MEDIUM"):
        """Create a defect type"""
        # BR-010: ID uniqueness
        existing = await self.defect_repo.get_by_id(defect_id)
        if existing:
            raise ValueError(f"Defect already exists: {defect_id}")

        defect = Defect(
            defect_id=defect_id,
            name=name,
            category=category,
            severity=severity,
            status="ACTIVE"
        )
        await self.defect_repo.create(defect)
        logger.info("Defect created", defect_id=defect_id)
        return defect

    async def get_active_defects(self) -> List[Defect]:
        """Get all active defects for dropdown"""
        return await self.defect_repo.get_active()

    async def bulk_import_defects(self, defects: List[dict]):
        """
        Bulk import defects with idempotency.
        BR-012: Import idempotency - skip duplicates
        """
        created_count = 0
        skipped_count = 0

        for item in defects:
            defect_id = item.get("defect_id")
            existing = await self.defect_repo.get_by_id(defect_id)

            if existing:
                skipped_count += 1
                logger.info("Defect already exists, skipping", defect_id=defect_id)
                continue

            await self.create_defect(
                defect_id=defect_id,
                name=item.get("name"),
                category=item.get("category"),
                severity=item.get("severity", "MEDIUM")
            )
            created_count += 1

        logger.info("Defects bulk imported", created=created_count, skipped=skipped_count)
        return {"created": created_count, "skipped": skipped_count}

    # ==================== MACHINES ====================
    async def create_machine(self, machine_id: str, name: str, model: str = None):
        """Create a machine"""
        existing = await self.machine_repo.get_by_id(machine_id)
        if existing:
            raise ValueError(f"Machine already exists: {machine_id}")

        machine = Machine(
            machine_id=machine_id,
            name=name,
            model=model,
            status="ACTIVE"
        )
        await self.machine_repo.create(machine)
        logger.info("Machine created", machine_id=machine_id)
        return machine

    async def get_active_machines(self) -> List[Machine]:
        """Get all active machines for dropdown"""
        return await self.machine_repo.get_active()

    async def bulk_import_machines(self, machines: List[dict]):
        """Bulk import machines with idempotency"""
        created_count = 0
        skipped_count = 0

        for item in machines:
            machine_id = item.get("machine_id")
            existing = await self.machine_repo.get_by_id(machine_id)

            if existing:
                skipped_count += 1
                logger.info("Machine already exists, skipping", machine_id=machine_id)
                continue

            await self.create_machine(
                machine_id=machine_id,
                name=item.get("name"),
                model=item.get("model")
            )
            created_count += 1

        logger.info("Machines bulk imported", created=created_count, skipped=skipped_count)
        return {"created": created_count, "skipped": skipped_count}

    # ==================== FABRICS ====================
    async def create_fabric(self, fabric_id: str, name: str, description: str = None):
        """Create a fabric type"""
        existing = await self.fabric_repo.get_by_id(fabric_id)
        if existing:
            raise ValueError(f"Fabric already exists: {fabric_id}")

        fabric = Fabric(
            fabric_id=fabric_id,
            name=name,
            description=description,
            status="ACTIVE"
        )
        await self.fabric_repo.create(fabric)
        logger.info("Fabric created", fabric_id=fabric_id)
        return fabric

    async def get_active_fabrics(self) -> List[Fabric]:
        """Get all active fabrics for dropdown"""
        return await self.fabric_repo.get_active()

    async def bulk_import_fabrics(self, fabrics: List[dict]):
        """Bulk import fabrics with idempotency"""
        created_count = 0
        skipped_count = 0

        for item in fabrics:
            fabric_id = item.get("fabric_id")
            existing = await self.fabric_repo.get_by_id(fabric_id)

            if existing:
                skipped_count += 1
                logger.info("Fabric already exists, skipping", fabric_id=fabric_id)
                continue

            await self.create_fabric(
                fabric_id=fabric_id,
                name=item.get("name"),
                description=item.get("description")
            )
            created_count += 1

        logger.info("Fabrics bulk imported", created=created_count, skipped=skipped_count)
        return {"created": created_count, "skipped": skipped_count}
