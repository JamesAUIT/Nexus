# iDRAC/Redfish firmware and hardware health (scaffolding)
from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import IDracInventory, Host

router = APIRouter(prefix="/idrac", tags=["idrac"])


class IDracResponse(BaseModel):
    id: int
    host_id: int | None
    target_url: str | None
    bios_version: str | None
    idrac_version: str | None
    compliance_status: str | None
    last_scan_at: str
    scan_error: str | None

    class Config:
        from_attributes = True


@router.get("/inventory", response_model=dict)
def list_inventory(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("hosts:read")),
    host_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = db.query(IDracInventory).order_by(IDracInventory.last_scan_at.desc())
    if host_id is not None:
        q = q.filter(IDracInventory.host_id == host_id)
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = []
    for r in q.all():
        rows.append(IDracResponse(
            id=r.id,
            host_id=r.host_id,
            target_url=r.target_url,
            bios_version=r.bios_version,
            idrac_version=r.idrac_version,
            compliance_status=r.compliance_status,
            last_scan_at=r.last_scan_at.isoformat() if r.last_scan_at else "",
            scan_error=r.scan_error,
        ))
    return {"data": rows, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("/scan")
def run_scan(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("hosts:read")),
    host_id: int = Query(...),
):
    from datetime import datetime, timezone
    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        return {"ok": False, "error": "Host not found"}
    # Placeholder: would call Redfish API; store stub result
    now = datetime.now(timezone.utc)
    inv = db.query(IDracInventory).filter(IDracInventory.host_id == host_id).first()
    if inv:
        inv.bios_version = inv.bios_version or "2.0.0"
        inv.idrac_version = inv.idrac_version or "5.0.0"
        inv.compliance_status = "unknown"
        inv.last_scan_at = now
        inv.scan_error = None
        db.commit()
        db.refresh(inv)
        return {"ok": True, "id": inv.id}
    inv = IDracInventory(host_id=host_id, target_url=f"https://{host.ip_address or host.name}", bios_version="2.0.0", idrac_version="5.0.0", compliance_status="unknown", last_scan_at=now)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return {"ok": True, "id": inv.id}
