"""Verify OpenAPI schema is accessible and has required endpoints"""
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.routes import auth


def make_app():
    app = FastAPI(title="Control Calidad API", version="1.0.0", docs_url="/docs", openapi_url="/openapi.json")
    app.include_router(auth.router, prefix="/auth")

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    return app


client = TestClient(make_app())


class TestOpenAPI:
    def test_openapi_json_accessible(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "Control Calidad API"

    def test_docs_endpoint_accessible(self):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_auth_login_in_schema(self):
        schema = client.get("/openapi.json").json()
        paths = schema["paths"]
        assert "/auth/login" in paths

    def test_auth_refresh_in_schema(self):
        schema = client.get("/openapi.json").json()
        assert "/auth/refresh" in schema["paths"]
