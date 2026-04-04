# LDAP login: service bind + search + user bind; issues JWT if user exists in DB.
from __future__ import annotations

import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from ldap3 import ALL, Connection, Server
from ldap3.utils.conv import escape_filter_chars
from sqlalchemy.orm import Session

from src.api.deps import get_db_session
from src.config import settings
from src.core.audit_middleware import get_client_ip, log_audit
from src.core.limiter import limiter
from src.core.security import create_access_token
from src.models.user import User
from src.schemas.user import Token, UserCreate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth-ldap"])


def _ldap_connection() -> tuple[Server, str]:
    if not settings.ldap_url:
        raise HTTPException(status_code=501, detail="LDAP not configured")
    parsed = urlparse(settings.ldap_url if "://" in settings.ldap_url else f"ldap://{settings.ldap_url}")
    host = parsed.hostname or settings.ldap_url.replace("ldap://", "").replace("ldaps://", "").split(":")[0]
    port = parsed.port or (636 if parsed.scheme == "ldaps" else 389)
    use_ssl = parsed.scheme == "ldaps"
    server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL)
    return server, host


@router.post("/ldap/login", response_model=Token)
@limiter.limit(settings.auth_login_rate_limit)
def ldap_login(
    request: Request,
    body: UserCreate,
    db: Session = Depends(get_db_session),
):
    if not settings.ldap_url or not settings.ldap_base_dn:
        raise HTTPException(status_code=501, detail="LDAP not configured")
    if not settings.ldap_bind_dn or not settings.ldap_bind_password:
        raise HTTPException(status_code=501, detail="LDAP service bind not configured")

    user_row = db.query(User).filter(User.username == body.username).first()
    if not user_row:
        raise HTTPException(status_code=403, detail="User not provisioned in Nexus")
    if user_row.disabled_at:
        raise HTTPException(status_code=403, detail="Account disabled")

    server, _host = _ldap_connection()
    safe = escape_filter_chars(body.username)
    try:
        filt = settings.ldap_user_search_filter.format(username=safe)
    except KeyError as e:
        raise HTTPException(status_code=500, detail="Invalid LDAP_USER_SEARCH_FILTER (use {username})") from e

    try:
        conn = Connection(server, user=settings.ldap_bind_dn, password=settings.ldap_bind_password, auto_bind=True)
    except Exception as e:
        logger.warning("LDAP service bind failed: %s", e)
        raise HTTPException(status_code=503, detail="LDAP unavailable") from e

    try:
        ok = conn.search(settings.ldap_base_dn, filt, attributes=["dn"])
        if not ok or not conn.entries:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        user_dn = str(conn.entries[0].entry_dn)
    finally:
        conn.unbind()

    try:
        user_conn = Connection(server, user=user_dn, password=body.password, auto_bind=True)
        user_conn.unbind()
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    log_audit(db, user_row.id, "login", "auth", None, "ldap_login_success", get_client_ip(request))
    token = create_access_token(user_row.id)
    return Token(access_token=token)
