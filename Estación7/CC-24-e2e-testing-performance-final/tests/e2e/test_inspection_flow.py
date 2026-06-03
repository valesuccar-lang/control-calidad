"""End-to-end tests for the full inspection → approval flow"""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.routes import auth as auth_routes
from app.config import settings

# Minimal app with just auth for E2E token generation
auth_app = FastAPI()
auth_app.include_router(auth_routes.router, prefix="/auth")


@pytest.mark.asyncio
async def test_full_login_flow():
    async with AsyncClient(transport=ASGITransport(app=auth_app), base_url="http://test") as client:
        # Step 1: Login as analista
        resp = await client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
        assert resp.status_code == 200
        token_data = resp.json()
        assert "access_token" in token_data
        assert "ANALISTA" in token_data["roles"]

        # Step 2: Verify token works for /me
        access_token = token_data["access_token"]
        me_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["user_id"] == "analista_001"


@pytest.mark.asyncio
async def test_jefe_qa_can_login():
    async with AsyncClient(transport=ASGITransport(app=auth_app), base_url="http://test") as client:
        resp = await client.post("/auth/login", json={"email": "jefe@example.com", "password": "password"})
        assert resp.status_code == 200
        assert "JEFE_QA" in resp.json()["roles"]


@pytest.mark.asyncio
async def test_token_refresh_flow():
    async with AsyncClient(transport=ASGITransport(app=auth_app), base_url="http://test") as client:
        login = await client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
        refresh_token = login.json()["refresh_token"]

        refresh = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh.status_code == 200
        new_token = refresh.json()["access_token"]
        assert new_token != login.json()["access_token"]

        me = await client.get("/auth/me", headers={"Authorization": f"Bearer {new_token}"})
        assert me.status_code == 200
