# Useful Links: categories, site-specific, role-based visibility, object-level related links
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission, get_user_permissions
from src.models.user import User
from src.models import UsefulLink

router = APIRouter(prefix="/useful-links", tags=["useful-links"])


class UsefulLinkResponse(BaseModel):
    id: int
    name: str
    url: str
    category: str | None
    site_id: int | None
    related_entity_type: str | None
    related_entity_id: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=list[UsefulLinkResponse])
def list_useful_links(
    category: str | None = Query(None),
    site_id: int | None = Query(None),
    related_entity_type: str | None = Query(None),
    related_entity_id: str | None = Query(None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    perms = get_user_permissions(current_user)
    q = db.query(UsefulLink).order_by(UsefulLink.category, UsefulLink.name)
    if category:
        q = q.filter(UsefulLink.category == category)
    if site_id is not None:
        q = q.filter((UsefulLink.site_id == site_id) | (UsefulLink.site_id.is_(None)))
    if related_entity_type:
        q = q.filter(UsefulLink.related_entity_type == related_entity_type)
    if related_entity_id:
        q = q.filter(UsefulLink.related_entity_id == related_entity_id)
    rows = q.all()
    out = []
    for r in rows:
        if r.required_permission and r.required_permission not in perms and "admin:all" not in perms:
            continue
        out.append(UsefulLinkResponse(
            id=r.id, name=r.name, url=r.url, category=r.category,
            site_id=r.site_id, related_entity_type=r.related_entity_type, related_entity_id=r.related_entity_id,
        ))
    return out
