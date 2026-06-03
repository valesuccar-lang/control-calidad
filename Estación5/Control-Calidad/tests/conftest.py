"""Pytest configuration and fixtures"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool

from app.models.base import Base
from app.models.orm import User, Lote, Inspection, Approval, Defect, Machine, Fabric, AuditLog


@pytest_asyncio.fixture
async def test_db():
    """Create in-memory test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    yield async_session_factory

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db):
    """Get test database session"""
    async with test_db() as session:
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
