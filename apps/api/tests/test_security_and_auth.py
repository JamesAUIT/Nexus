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


def test_auth_public_options():
    r = client.get("/api/v1/auth/public-options")
    assert r.status_code == 200
    data = r.json()
    assert "oidc_enabled" in data
    assert "ldap_enabled" in data


def test_platform_settings_requires_auth():
    r = client.get("/api/v1/platform/settings")
    assert r.status_code == 401


def test_create_connector_requires_auth():
    r = client.post(
        "/api/v1/connectors",
        json={
            "type": "netbox",
            "name": "Test",
            "config_plain": {"url": "https://x.example.com", "token": "t", "verify_ssl": True},
        },
    )
    assert r.status_code == 401
