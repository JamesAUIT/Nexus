# OIDC redirect + callback (authlib-style token exchange via httpx)
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from src.config import settings

router = APIRouter(prefix="/oidc", tags=["auth-oidc"])


@router.get("/login")
def oidc_login():
    if not settings.oidc_client_id or not settings.oidc_issuer_url:
        raise HTTPException(status_code=501, detail="OIDC not configured")
    base = settings.oidc_issuer_url.rstrip("/")
    redirect = settings.oidc_redirect_uri or "http://localhost:8000/api/v1/auth/oidc/callback"
    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "redirect_uri": redirect,
        "scope": "openid email profile",
    }
    url = f"{base}/oauth2/authorize?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/callback")
def oidc_callback(code: str = Query(...), error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=error)
    if not settings.oidc_client_secret or not settings.oidc_issuer_url:
        raise HTTPException(status_code=501, detail="OIDC not configured")
    base = settings.oidc_issuer_url.rstrip("/")
    redirect = settings.oidc_redirect_uri or "http://localhost:8000/api/v1/auth/oidc/callback"
    token_url = f"{base}/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect,
        "client_id": settings.oidc_client_id,
        "client_secret": settings.oidc_client_secret,
    }
    r = httpx.post(token_url, data=data, timeout=30.0)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=r.text[:500])
    tok = r.json()
    return {
        "message": "OIDC token received; map id_token claims to local User and issue JWT in a full deployment",
        "token_type": tok.get("token_type"),
        "expires_in": tok.get("expires_in"),
    }
