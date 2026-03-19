# Change detection: ChangeEvent list and history by entity
from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import ChangeEvent

router = APIRouter(prefix="/change-events", tags=["change-events"])


class ChangeEventResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    change_type: str
    field_name: str | None
    old_value: str | None
    new_value: str | None
    changed_at: str
    changed_by: str | None
    source: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=dict)
def list_change_events(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("audit:read")),
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = db.query(ChangeEvent).order_by(ChangeEvent.changed_at.desc())
    if entity_type:
        q = q.filter(ChangeEvent.entity_type == entity_type)
    if entity_id:
        q = q.filter(ChangeEvent.entity_id == entity_id)
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = []
    for e in q.all():
        rows.append(ChangeEventResponse(
            id=e.id,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            change_type=e.change_type,
            field_name=e.field_name,
            old_value=e.old_value,
            new_value=e.new_value,
            changed_at=e.changed_at.isoformat() if e.changed_at else "",
            changed_by=e.changed_by,
            source=e.source,
        ))
    return {"data": rows, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.get("/timeline")
def timeline_for_entity(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("audit:read")),
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
):
    q = db.query(ChangeEvent).filter(ChangeEvent.entity_type == entity_type, ChangeEvent.entity_id == entity_id).order_by(ChangeEvent.changed_at.desc()).limit(limit)
    rows = [{"id": e.id, "change_type": e.change_type, "field_name": e.field_name, "old_value": e.old_value, "new_value": e.new_value, "changed_at": e.changed_at.isoformat() if e.changed_at else "", "changed_by": e.changed_by} for e in q.all()]
    return {"data": rows}
