"""Integration tests for Auth API — RBAC and JWT flows"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the router directly — no DB needed for auth tests
from app.routes.auth import router
from app.config import settings

app = FastAPI()
app.include_router(router, prefix="/auth")
client = TestClient(app)


class TestLogin:
    def test_analista_login_returns_tokens(self):
        resp = client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["roles"] == ["ANALISTA"]

    def test_jefe_qa_login(self):
        resp = client.post("/auth/login", json={"email": "jefe@example.com", "password": "password"})
        assert resp.status_code == 200
        assert resp.json()["roles"] == ["JEFE_QA"]

    def test_admin_login(self):
        resp = client.post("/auth/login", json={"email": "admin@example.com", "password": "password"})
        assert resp.status_code == 200
        assert resp.json()["roles"] == ["ADMIN"]

    def test_gerente_login(self):
        resp = client.post("/auth/login", json={"email": "gerente@example.com", "password": "password"})
        assert resp.status_code == 200
        assert resp.json()["roles"] == ["GERENTE"]

    def test_wrong_password_returns_401(self):
        resp = client.post("/auth/login", json={"email": "analista@example.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_unknown_user_returns_401(self):
        resp = client.post("/auth/login", json={"email": "unknown@example.com", "password": "password"})
        assert resp.status_code == 401

    def test_invalid_email_format_returns_422(self):
        resp = client.post("/auth/login", json={"email": "not-an-email", "password": "password"})
        assert resp.status_code == 422


class TestRefresh:
    def _get_refresh_token(self):
        resp = client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
        return resp.json()["refresh_token"]

    def test_valid_refresh_returns_new_access_token(self):
        refresh = self._get_refresh_token()
        resp = client.post("/auth/refresh", json={"refresh_token": refresh})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_invalid_refresh_token_returns_401(self):
        resp = client.post("/auth/refresh", json={"refresh_token": "invalid.token.here"})
        assert resp.status_code == 401

    def test_access_token_as_refresh_returns_401(self):
        login = client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
        access = login.json()["access_token"]
        resp = client.post("/auth/refresh", json={"refresh_token": access})
        assert resp.status_code == 401


class TestMe:
    def test_authenticated_user_gets_info(self):
        login = client.post("/auth/login", json={"email": "analista@example.com", "password": "password"})
        token = login.json()["access_token"]
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "analista_001"

    def test_no_token_returns_403(self):
        resp = client.get("/auth/me")
        assert resp.status_code in (401, 403)

    def test_expired_token_returns_401(self):
        from jose import jwt
        from datetime import datetime, timedelta
        expired_payload = {"sub": "user", "roles": ["ANALISTA"], "type": "access",
                           "exp": datetime.utcnow() - timedelta(hours=1)}
        expired_token = jwt.encode(expired_payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401
