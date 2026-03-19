from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import Host
from src.schemas.host import HostResponse

router = APIRouter(prefix="/hosts", tags=["hosts"])


@router.get("", response_model=list[HostResponse])
def list_hosts(db: Session = Depends(get_db_session), current_user: User = Depends(require_permission("hosts:read"))):
    return db.query(Host).order_by(Host.name).all()
