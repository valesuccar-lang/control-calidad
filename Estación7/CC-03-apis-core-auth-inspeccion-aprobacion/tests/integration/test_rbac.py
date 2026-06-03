"""RBAC tests — role enforcement across endpoints"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends

from app.auth.dependencies import require_role

app = FastAPI()


@app.get("/only-analista")
async def only_analista(user: dict = Depends(require_role("ANALISTA"))):
    return {"ok": True}


@app.get("/only-jefe-qa")
async def only_jefe_qa(user: dict = Depends(require_role("JEFE_QA"))):
    return {"ok": True}


@app.get("/multi-role")
async def multi_role(user: dict = Depends(require_role("ANALISTA", "JEFE_QA", "ADMIN"))):
    return {"ok": True}


client = TestClient(app)

from app.routes.auth import router as auth_router

auth_app = FastAPI()
auth_app.include_router(auth_router, prefix="/auth")
auth_client = TestClient(auth_app)


def _token(email: str) -> str:
    resp = auth_client.post("/auth/login", json={"email": email, "password": "password"})
    return resp.json()["access_token"]


class TestRBAC:
    def test_analista_can_access_analista_route(self):
        token = _token("analista@example.com")
        resp = client.get("/only-analista", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_jefe_qa_cannot_access_analista_route(self):
        token = _token("jefe@example.com")
        resp = client.get("/only-analista", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_analista_cannot_access_jefe_qa_route(self):
        token = _token("analista@example.com")
        resp = client.get("/only-jefe-qa", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_admin_can_access_multi_role_route(self):
        token = _token("admin@example.com")
        resp = client.get("/multi-role", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_unauthenticated_returns_403(self):
        resp = client.get("/only-analista")
        assert resp.status_code in (401, 403)
