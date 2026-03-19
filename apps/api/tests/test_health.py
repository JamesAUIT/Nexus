"""Basic health and smoke tests for Cloud Nexus API."""
import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health():
    """Health endpoint returns ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_docs_available():
    """API docs are served."""
    r = client.get("/docs")
    assert r.status_code == 200


def test_openapi_schema():
    """OpenAPI schema is exposed."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert "openapi" in data
    assert "paths" in data


def test_api_v1_prefix():
    """v1 paths exist in schema."""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    assert any(p.startswith("/api/v1") for p in paths)
