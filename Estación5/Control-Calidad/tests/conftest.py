"""Pytest configuration and fixtures"""
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from app.models.base import Base
from app.models.orm import User, Fabric, Lote, Machine, Defect

_DATABASE_URL = os.environ.get("DATABASE_URL", "")
_USE_POSTGRES = _DATABASE_URL.startswith("postgresql+asyncpg://")


@pytest_asyncio.fixture
async def test_db():
    """Create test database — uses postgres from env if available, else SQLite."""
    if _USE_POSTGRES:
        engine = create_async_engine(_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        yield factory
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
    else:
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=pool.StaticPool,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        yield factory
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db):
    """Get test database session with required FK prerequisites seeded."""
    async with test_db() as session:
        # Seed master data required by FK constraints
        session.add(Fabric(fabric_id="FABRIC_001", name="Cotton"))
        session.add(Lote(lote_id="HDR-12847", fabric_id="FABRIC_001", quantity=100))
        session.add(User(
            id="analista_001", email="analista@test.com", full_name="Test Analista",
            hashed_password="x", roles=["ANALISTA"]
        ))
        session.add(User(
            id="jefe_qa_001", email="jefe@test.com", full_name="Test Jefe QA",
            hashed_password="x", roles=["JEFE_QA"]
        ))
        session.add(Defect(defect_id="DEFECT_001", name="Tear", category="Physical"))
        session.add(Machine(machine_id="MACHINE_001", name="Machine 1"))
        try:
            await session.commit()
        except Exception:
            await session.rollback()
        yield session


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "id": "test_user_001",
        "email": "test@example.com",
        "full_name": "Test User",
        "hashed_password": "hashed_password",
        "roles": ["ANALISTA"],
        "status": "ACTIVE"
    }


@pytest.fixture
def test_inspection_data():
    """Test inspection data"""
    return {
        "lote_id": "HDR-12847",
        "analista_id": "analista_001",
        "defect_id": "DEFECT_001",
        "comment_text": "This is a test comment",
        "photo_path": "/storage/photos/2026/05/28/inspection_001.jpg",
        "photo_checksum": "a" * 64,
        "photo_size_kb": 250,
        "machine_id": "MACHINE_001"
    }


@pytest.fixture
def test_approval_data():
    """Test approval data"""
    return {
        "jefe_qa_id": "jefe_qa_001",
        "decision": "APPROVED",
        "rejection_reason": None,
        "notes": "Looks good"
    }
