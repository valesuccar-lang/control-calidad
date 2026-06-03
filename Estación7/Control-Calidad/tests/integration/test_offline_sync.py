"""Integration tests for offline sync functionality"""
import pytest
import pytest_asyncio
from app.config import settings


def test_exponential_backoff_delays():
    """Test exponential backoff delay calculation"""
    delays = settings.sync.backoff_delays
    assert len(delays) == settings.sync.max_retries
    assert delays[0] == 5  # Initial delay
    assert delays[1] == 10
    assert delays[2] == 30
    assert delays[3] == 60
    assert delays[4] == 60  # Capped at 60


def test_sync_configuration():
    """Test sync configuration values"""
    assert settings.sync.initial_delay_seconds == 5
    assert settings.sync.max_retries == 5
    total_delay = sum(settings.sync.backoff_delays)
    assert 60 <= total_delay <= 180  # Total retry window


@pytest.mark.asyncio
async def test_batch_sync_endpoint_structure():
    """Test batch sync endpoint accepts correct structure"""
    from app.schemas.inspection_schemas import SyncBatchRequest, CreateInspectionRequest

    # Valid batch request
    batch = SyncBatchRequest(
        inspections=[
            CreateInspectionRequest(
                lote_id="HDR-12847",
                defect_id="DEF_001",
                comment_text="Test comment with sufficient length",
                photo_path="/storage/photo.jpg",
                photo_checksum="a" * 64,
                photo_size_kb=250,
                machine_id="MACH_001"
            )
        ]
    )
    assert len(batch.inspections) == 1


@pytest.mark.asyncio
async def test_batch_sync_max_items():
    """Test batch sync max items validation"""
    from pydantic import ValidationError
    from app.schemas.inspection_schemas import SyncBatchRequest, CreateInspectionRequest

    inspection = CreateInspectionRequest(
        lote_id="HDR-12847",
        defect_id="DEF_001",
        comment_text="Test comment with sufficient length",
        photo_path="/storage/photo.jpg",
        photo_checksum="a" * 64,
        photo_size_kb=250,
        machine_id="MACH_001"
    )

    # This should fail - more than 100 items
    try:
        batch = SyncBatchRequest(
            inspections=[inspection] * 101
        )
        assert False, "Should have raised validation error"
    except ValidationError:
        pass  # Expected
