"""Unit tests for MastersService business logic"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class FakeRepo:
    """Generic in-memory fake repository"""

    def __init__(self):
        self._store = {}

    async def get_by_id(self, id_):
        return self._store.get(id_)

    async def create(self, obj):
        key = getattr(obj, list(vars(obj).keys())[0])  # first attr as key
        self._store[key] = obj
        return obj

    async def get_active(self):
        return [v for v in self._store.values() if getattr(v, "status", "ACTIVE") == "ACTIVE"]


# We test the domain service directly using fake repos (no DB)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.domain.services.masters_service import MastersService


class SimpleFakeRepo:
    def __init__(self):
        self._data = {}

    async def get_by_id(self, id_):
        return self._data.get(id_)

    async def create(self, obj):
        first_key = next(k for k in vars(obj) if "id" in k)
        self._data[getattr(obj, first_key)] = obj
        return obj

    async def get_active(self):
        return list(self._data.values())


def make_service():
    defect_repo = SimpleFakeRepo()
    machine_repo = SimpleFakeRepo()
    fabric_repo = SimpleFakeRepo()
    return MastersService(defect_repo, machine_repo, fabric_repo), defect_repo, machine_repo, fabric_repo


class TestDefectService:
    @pytest.mark.asyncio
    async def test_create_defect_success(self):
        svc, drepo, *_ = make_service()
        d = await svc.create_defect("D-001", "Rasgadura", "STRUCTURAL", "HIGH")
        assert d.defect_id == "D-001"
        assert d.severity == "HIGH"

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self):
        svc, *_ = make_service()
        await svc.create_defect("D-001", "Rasgadura", "STRUCTURAL")
        with pytest.raises(ValueError, match="already exists"):
            await svc.create_defect("D-001", "Rasgadura", "STRUCTURAL")

    @pytest.mark.asyncio
    async def test_bulk_import_idempotent(self):
        svc, *_ = make_service()
        defects = [
            {"defect_id": "D-001", "name": "Rasgadura", "category": "STRUCTURAL"},
            {"defect_id": "D-002", "name": "Mancha", "category": "APPEARANCE"},
        ]
        result = await svc.bulk_import_defects(defects)
        assert result["created"] == 2
        assert result["skipped"] == 0

        result2 = await svc.bulk_import_defects(defects)
        assert result2["created"] == 0
        assert result2["skipped"] == 2


class TestMachineService:
    @pytest.mark.asyncio
    async def test_create_machine_success(self):
        svc, _, mrepo, _ = make_service()
        m = await svc.create_machine("M-001", "Tejedora A", "Model X")
        assert m.machine_id == "M-001"

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self):
        svc, *_ = make_service()
        await svc.create_machine("M-001", "Tejedora A")
        with pytest.raises(ValueError, match="already exists"):
            await svc.create_machine("M-001", "Tejedora B")

    @pytest.mark.asyncio
    async def test_bulk_import_machines(self):
        svc, *_ = make_service()
        result = await svc.bulk_import_machines([
            {"machine_id": "M-001", "name": "Tejedora A", "model": "TX100"},
            {"machine_id": "M-002", "name": "Tejedora B", "model": "TX200"},
        ])
        assert result["created"] == 2


class TestFabricService:
    @pytest.mark.asyncio
    async def test_create_fabric_success(self):
        svc, *_ = make_service()
        f = await svc.create_fabric("F-001", "Algodón", "100% natural")
        assert f.fabric_id == "F-001"

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self):
        svc, *_ = make_service()
        await svc.create_fabric("F-001", "Algodón")
        with pytest.raises(ValueError, match="already exists"):
            await svc.create_fabric("F-001", "Seda")

    @pytest.mark.asyncio
    async def test_bulk_import_fabrics(self):
        svc, *_ = make_service()
        result = await svc.bulk_import_fabrics([
            {"fabric_id": "F-001", "name": "Algodón", "description": "Natural"},
            {"fabric_id": "F-002", "name": "Poliéster", "description": "Sintético"},
        ])
        assert result["created"] == 2
        result2 = await svc.bulk_import_fabrics([{"fabric_id": "F-001", "name": "Algodón"}])
        assert result2["skipped"] == 1
