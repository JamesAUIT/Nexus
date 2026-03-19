from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.api.deps import get_db_session, get_current_user
from src.core.security import verify_password, create_access_token
from src.core.audit_middleware import log_audit, get_client_ip
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
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
