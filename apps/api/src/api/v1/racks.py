from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import Rack
from src.schemas.rack import RackResponse

router = APIRouter(prefix="/racks", tags=["racks"])


@router.get("", response_model=list[RackResponse])
def list_racks(db: Session = Depends(get_db_session), current_user: User = Depends(require_permission("sites:read"))):
    return db.query(Rack).order_by(Rack.site_id, Rack.name).all()
