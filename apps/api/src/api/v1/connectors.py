# Connector health status, data freshness, sync status indicators; create with encrypted config
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.deps import get_db_session
from src.core.audit_middleware import get_client_ip, log_audit
from src.core.encryption import encrypt_connector_config
from src.core.rbac import require_permission
from src.connectors.registry import get_connector
from src.models.user import User
from src.models import Connector, SyncJob
from src.schemas.connector import ConnectorCreateRequest, ConnectorResponse

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _derive_base_url(connector_type: str, d: dict) -> str | None:
    u = d.get("url")
    if isinstance(u, str) and u.strip():
        return u.rstrip("/")
    h = d.get("host")
    if isinstance(h, str) and h.strip():
        if connector_type == "vsphere":
            return f"https://{h.strip()}"
        if connector_type == "vyos":
            port = d.get("port", 22)
            return f"ssh://{h.strip()}:{port}"
    return None


@router.get("/types", response_model=list[dict])
def list_connector_types(
    current_user: User = Depends(require_permission("connectors:read")),
):
    """Supported connector `type` values for create forms."""
    return [
        {"type": "netbox", "label": "NetBox", "config_hint": '{"url": "https://netbox.example.com", "token": "…", "verify_ssl": true}'},
        {"type": "proxmox", "label": "Proxmox VE", "config_hint": '{"url": "https://pve:8006", "user": "root@pam", "password": "…", "verify_ssl": false}'},
        {"type": "vsphere", "label": "VMware vSphere", "config_hint": '{"host": "vcenter.example.com", "user": "…", "password": "…", "verify_ssl": true}'},
        {"type": "vyos", "label": "VyOS", "config_hint": '{"host": "router.example.com", "user": "…", "password": "…", "port": 22}'},
        {"type": "ad", "label": "Active Directory (LDAP)", "config_hint": '{"url": "ldaps://dc.example.com", "bind_dn": "…", "bind_password": "…", "base_dn": "DC=example,DC=com"}'},
    ]


@router.post("", response_model=ConnectorResponse)
def create_connector(
    body: ConnectorCreateRequest,
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("connectors:write")),
):
    impl = get_connector(body.type.strip().lower())
    if not impl:
        raise HTTPException(status_code=400, detail=f"Unknown connector type: {body.type}")

    try:
        cfg_model = impl.get_config_model()
        validated = cfg_model.model_validate(body.config_plain)
        plain_dict = validated.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid config: {e}") from e

    base_url = body.base_url
    if not base_url:
        base_url = _derive_base_url(impl.connector_type, plain_dict)

    enc = encrypt_connector_config(json.dumps(plain_dict, ensure_ascii=False))
    row = Connector(
        type=impl.connector_type,
        name=body.name.strip(),
        base_url=base_url,
        encrypted_config=enc,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    if body.create_sync_job:
        db.add(SyncJob(connector_id=row.id, schedule_cron=body.schedule_cron))
        db.commit()

    log_audit(
        db,
        current_user.id,
        "connector_create",
        "connector",
        str(row.id),
        details=f"type={row.type} name={row.name}",
        ip=get_client_ip(request),
    )
    return row


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
