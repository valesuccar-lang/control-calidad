"""Integration tests for inspection API routes"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime

from app.main import app


@pytest.mark.asyncio
async def test_create_inspection_unauthorized():
    """Test creating inspection without authentication"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/inspections",
            json={
                "lote_id": "HDR-12847",
                "defect_id": "DEF_001",
                "comment_text": "Test comment with more chars",
                "photo_path": "/storage/photo.jpg",
                "photo_checksum": "a" * 64,
                "photo_size_kb": 250,
                "machine_id": "MACH_001"
            }
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_inspection_invalid_comment():
    """Test that short comments are rejected"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": "Bearer test_token"}
        response = await client.post(
            "/api/inspections",
            json={
                "lote_id": "HDR-12847",
                "defect_id": "DEF_001",
                "comment_text": "short",  # Invalid
                "photo_path": "/storage/photo.jpg",
                "photo_checksum": "a" * 64,
                "photo_size_kb": 250,
                "machine_id": "MACH_001"
            },
            headers=headers
        )
        assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_list_inspections():
    """Test listing inspections"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": "Bearer test_token"}
        response = await client.get(
            "/api/inspections",
            headers=headers
        )
        assert response.status_code in (200, 401)


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
