from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db_session, get_current_user
from src.config import settings
from src.core.limiter import limiter
from src.core.security import verify_password, create_access_token
from src.core.audit_middleware import log_audit, get_client_ip
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse, Token
from src.api.auth.oidc import router as oidc_router
from src.api.auth.ldap import router as ldap_router

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(oidc_router)
router.include_router(ldap_router)


@router.get("/public-options")
def auth_public_options():
    """Safe flags for the login UI (no authentication required)."""
    return {
        "oidc_enabled": bool(settings.oidc_issuer_url and settings.oidc_client_id),
        "ldap_enabled": bool(
            settings.ldap_url
            and settings.ldap_base_dn
            and settings.ldap_bind_dn
            and settings.ldap_bind_password
        ),
    }


@router.post("/login", response_model=Token)
@limiter.limit(settings.auth_login_rate_limit)
def login(
    request: Request,
    body: UserCreate,
    db: Session = Depends(get_db_session),
):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not user.is_local or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if user.disabled_at:
        raise HTTPException(status_code=403, detail="Account disabled")
    log_audit(db, user.id, "login", "auth", None, "login_success", get_client_ip(request))
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
