# Saved Queries: reusable filtered views for common operational queries
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import SavedQuery

router = APIRouter(prefix="/saved-queries", tags=["saved-queries"])


class SavedQueryResponse(BaseModel):
    id: int
    name: str
    query_json: str | None

    class Config:
        from_attributes = True


class SavedQueryCreate(BaseModel):
    name: str
    query_json: str | None = None


@router.get("", response_model=list[SavedQueryResponse])
def list_saved_queries(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    return db.query(SavedQuery).filter(SavedQuery.user_id == current_user.id).order_by(SavedQuery.name).all()


@router.post("", response_model=SavedQueryResponse)
def create_saved_query(
  body: SavedQueryCreate,
  db: Session = Depends(get_db_session),
  current_user: User = Depends(require_permission("dashboard:read")),
):
    sq = SavedQuery(user_id=current_user.id, name=body.name, query_json=body.query_json)
    db.add(sq)
    db.commit()
    db.refresh(sq)
    return sq


@router.get("/{query_id}", response_model=SavedQueryResponse)
def get_saved_query(
  query_id: int,
  db: Session = Depends(get_db_session),
  current_user: User = Depends(require_permission("dashboard:read")),
):
    r = db.query(SavedQuery).filter(SavedQuery.id == query_id, SavedQuery.user_id == current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Saved query not found")
    return r


@router.delete("/{query_id}")
def delete_saved_query(
  query_id: int,
  db: Session = Depends(get_db_session),
  current_user: User = Depends(require_permission("dashboard:read")),
):
    r = db.query(SavedQuery).filter(SavedQuery.id == query_id, SavedQuery.user_id == current_user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Saved query not found")
    db.delete(r)
    db.commit()
    return {"status": "ok"}
