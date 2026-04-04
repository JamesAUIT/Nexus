# Audit log: list events (auth, sync, privileged)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    resource_type: str
    resource_id: str | None
    details: str | None
    ip: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("audit:read")),
):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    rows = q.limit(limit).all()
    return [AuditLogResponse(
        id=r.id,
        user_id=r.user_id,
        action=r.action,
        resource_type=r.resource_type,
        resource_id=r.resource_id,
        details=r.details,
        ip=r.ip,
        created_at=r.created_at.isoformat() if r.created_at else "",
    ) for r in rows]
