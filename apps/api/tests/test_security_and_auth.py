"""Smoke tests for LDAP stub, internal runner auth, and rate-limited routes."""
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_ldap_login_returns_501_when_not_configured():
    r = client.post("/api/v1/auth/ldap/login", json={"username": "x", "password": "y"})
    assert r.status_code == 501


def test_internal_script_manifest_requires_secret():
    r = client.get("/api/v1/internal/scripts/1/manifest")
    assert r.status_code == 401


def test_oidc_login_returns_501_when_not_configured():
    r = client.get("/api/v1/auth/oidc/login", follow_redirects=False)
    assert r.status_code == 501
