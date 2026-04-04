# User favourites and recent objects
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import UserFavourite, RecentObject

router = APIRouter(prefix="/favourites", tags=["favourites"])


@router.get("")
def list_favourites(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    q = db.query(UserFavourite).filter(UserFavourite.user_id == current_user.id).order_by(UserFavourite.created_at.desc())
    rows = [{"id": f.id, "entity_type": f.entity_type, "entity_id": f.entity_id} for f in q.all()]
    return {"data": rows}


@router.post("")
def add_favourite(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    entity_type: str = Query(...),
    entity_id: str = Query(...),
):
    existing = db.query(UserFavourite).filter(UserFavourite.user_id == current_user.id, UserFavourite.entity_type == entity_type, UserFavourite.entity_id == entity_id).first()
    if existing:
        return {"ok": True, "id": existing.id}
    f = UserFavourite(user_id=current_user.id, entity_type=entity_type, entity_id=entity_id, created_at=datetime.now(timezone.utc))
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"ok": True, "id": f.id}


@router.delete("")
def remove_favourite(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    entity_type: str = Query(...),
    entity_id: str = Query(...),
):
    db.query(UserFavourite).filter(UserFavourite.user_id == current_user.id, UserFavourite.entity_type == entity_type, UserFavourite.entity_id == entity_id).delete()
    db.commit()
    return {"ok": True}


router_recent = APIRouter(prefix="/recent", tags=["recent"])


@router_recent.get("")
def list_recent(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    limit: int = Query(20, ge=1, le=50),
):
    q = db.query(RecentObject).filter(RecentObject.user_id == current_user.id).order_by(RecentObject.last_viewed_at.desc()).limit(limit)
    rows = [{"entity_type": r.entity_type, "entity_id": r.entity_id, "display_name": r.display_name, "last_viewed_at": r.last_viewed_at.isoformat() if r.last_viewed_at else ""} for r in q.all()]
    return {"data": rows}


@router_recent.post("")
def record_view(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    display_name: str = Query(""),
):
    now = datetime.now(timezone.utc)
    existing = db.query(RecentObject).filter(RecentObject.user_id == current_user.id, RecentObject.entity_type == entity_type, RecentObject.entity_id == entity_id).first()
    if existing:
        existing.last_viewed_at = now
        existing.display_name = display_name or existing.display_name
        db.commit()
        return {"ok": True}
    # Keep only last 100 per user
    count = db.query(RecentObject).filter(RecentObject.user_id == current_user.id).count()
    if count >= 100:
        to_del = db.query(RecentObject).filter(RecentObject.user_id == current_user.id).order_by(RecentObject.last_viewed_at.asc()).limit(1).first()
        if to_del:
            db.delete(to_del)
    r = RecentObject(user_id=current_user.id, entity_type=entity_type, entity_id=entity_id, display_name=display_name or None, last_viewed_at=now)
    db.add(r)
    db.commit()
    return {"ok": True}
