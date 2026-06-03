"""Shared pytest fixtures for all test suites"""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.routes import auth, inspections, approvals, masters


@pytest.fixture
def app_no_db():
    """FastAPI app with auth routes only — no DB dependency"""
    application = FastAPI()
    application.include_router(auth.router, prefix="/auth")
    return application


@pytest.fixture
async def async_client(app_no_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_no_db), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def analista_token(app_no_db):
    from fastapi.testclient import TestClient
    client = TestClient(app_no_db)
    resp = client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
    return resp.json()["access_token"]


@pytest.fixture
def jefe_qa_token(app_no_db):
    from fastapi.testclient import TestClient
    client = TestClient(app_no_db)
    resp = client.post("/auth/login", json={"email": "jefe@example.com", "password": "password"})
    return resp.json()["access_token"]


@pytest.fixture
def admin_token(app_no_db):
    from fastapi.testclient import TestClient
    client = TestClient(app_no_db)
    resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "password"})
    return resp.json()["access_token"]
