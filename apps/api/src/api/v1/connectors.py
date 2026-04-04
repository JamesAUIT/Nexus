# Connector health status, data freshness, sync status indicators
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import Connector, SyncJob

router = APIRouter(prefix="/connectors", tags=["connectors"])


class ConnectorHealthResponse(BaseModel):
    id: int
    type: str
    name: str
    base_url: str | None
    status: str  # healthy, unhealthy, unknown
    last_ok_at: datetime | None
    last_error: str | None
    data_freshness_minutes: int | None  # minutes since last successful sync
    sync_status: str | None  # last sync job status
    sync_last_run_at: datetime | None

    class Config:
        from_attributes = True


@router.get("/health", response_model=list[ConnectorHealthResponse])
def list_connector_health(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("connectors:read")),
):
    """Connector health status and data freshness from last successful sync."""
    connectors = db.query(Connector).order_by(Connector.name).all()
    out = []
    for c in connectors:
        sync_job = db.query(SyncJob).filter(SyncJob.connector_id == c.id).order_by(SyncJob.id.desc()).first()
        sync_status = sync_job.last_status if sync_job else None
        sync_last_run_at = sync_job.last_run_at if sync_job else None
        data_freshness_minutes = None
        if c.last_ok_at:
            delta = (datetime.now(c.last_ok_at.tzinfo) if c.last_ok_at.tzinfo else datetime.utcnow()) - c.last_ok_at
            data_freshness_minutes = int(delta.total_seconds() / 60)
        status = "healthy" if c.last_error is None and c.last_ok_at else ("unhealthy" if c.last_error else "unknown")
        if c.last_ok_at and not c.last_error:
            status = "healthy"
        elif c.last_error:
            status = "unhealthy"
        out.append(ConnectorHealthResponse(
            id=c.id,
            type=c.type,
            name=c.name,
            base_url=c.base_url,
            status=status,
            last_ok_at=c.last_ok_at,
            last_error=c.last_error,
            data_freshness_minutes=data_freshness_minutes,
            sync_status=sync_status,
            sync_last_run_at=sync_last_run_at,
        ))
    return out
