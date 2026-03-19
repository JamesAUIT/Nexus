# Runbooks: markdown content, categories, tags, related systems, related links
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import Runbook

router = APIRouter(prefix="/runbooks", tags=["runbooks"])


class RunbookResponse(BaseModel):
    id: int
    name: str
    content: str | None
    category: str | None
    tags: str | None
    related_systems: str | None
    related_links: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=list[RunbookResponse])
def list_runbooks(
    category: str | None = Query(None),
    tag: str | None = Query(None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("runbooks:read")),
):
    q = db.query(Runbook).order_by(Runbook.category, Runbook.name)
    if category:
        q = q.filter(Runbook.category == category)
    if tag:
        q = q.filter(Runbook.tags.ilike(f"%{tag}%"))
    return q.all()


@router.get("/{runbook_id}", response_model=RunbookResponse)
def get_runbook(
  runbook_id: int,
  db: Session = Depends(get_db_session),
  current_user: User = Depends(require_permission("runbooks:read")),
):
    r = db.query(Runbook).filter(Runbook.id == runbook_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return r
