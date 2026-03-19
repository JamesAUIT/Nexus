from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import Datastore, StorageVolume

router = APIRouter(prefix="/storage", tags=["storage"])


class DatastoreResponse(BaseModel):
    id: int
    name: str
    type: str | None
    cluster_id: int | None
    host_id: int | None
    external_id: str | None
    class Config:
        from_attributes = True


class StorageVolumeResponse(BaseModel):
    id: int
    datastore_id: int
    name: str
    capacity_bytes: int | None
    external_id: str | None
    class Config:
        from_attributes = True


@router.get("/datastores", response_model=list[DatastoreResponse])
def list_datastores(db: Session = Depends(get_db_session), current_user: User = Depends(require_permission("dashboard:read"))):
    return db.query(Datastore).order_by(Datastore.name).all()


@router.get("/volumes", response_model=list[StorageVolumeResponse])
def list_volumes(db: Session = Depends(get_db_session), current_user: User = Depends(require_permission("dashboard:read"))):
    return db.query(StorageVolume).order_by(StorageVolume.datastore_id, StorageVolume.name).all()
