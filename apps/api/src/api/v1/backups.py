from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import BackupStatus

router = APIRouter(prefix="/backups", tags=["backups"])


class BackupStatusResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    status: str
    last_run_at: str | None
    details: str | None
    class Config:
        from_attributes = True


@router.get("", response_model=list[BackupStatusResponse])
def list_backup_statuses(db: Session = Depends(get_db_session), current_user: User = Depends(require_permission("dashboard:read"))):
    rows = db.query(BackupStatus).order_by(BackupStatus.updated_at.desc()).limit(100).all()
    return [BackupStatusResponse(
        id=r.id, entity_type=r.entity_type, entity_id=r.entity_id, status=r.status,
        last_run_at=r.last_run_at.isoformat() if r.last_run_at else None, details=r.details,
    ) for r in rows]
