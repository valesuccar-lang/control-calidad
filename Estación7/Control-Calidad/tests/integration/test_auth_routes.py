"""Integration tests for authentication routes"""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_login_success():
    """Test successful login"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "analista@example.com",
                "password": "password"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "invalid@example.com",
                "password": "wrong_password"
            }
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token():
    """Test token refresh"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First login
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "analista@example.com",
                "password": "password"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        refresh_response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.json()


@pytest.mark.asyncio
async def test_get_current_user():
    """Test getting current user info"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login first
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "analista@example.com",
                "password": "password"
            }
        )
        access_token = login_response.json()["access_token"]

        # Get user info
        user_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert user_response.status_code == 200
        data = user_response.json()
        assert "user_id" in data
        assert "roles" in data
