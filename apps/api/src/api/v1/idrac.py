# iDRAC/Redfish firmware and hardware health (scaffolding)
from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session
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
    username: str | None = Query(None, description="iDRAC/Redfish user"),
    password: str | None = Query(None, description="iDRAC/Redfish password"),
):
    import httpx
    from datetime import datetime, timezone

    host = db.query(Host).filter(Host.id == host_id).first()
    if not host:
        return {"ok": False, "error": "Host not found"}
    base = host.ip_address or host.name
    if not base.startswith("http"):
        target = f"https://{base}"
    else:
        target = base
    now = datetime.now(timezone.utc)
    bios_ver = None
    idrac_ver = None
    err = None
    if username and password:
        try:
            sys_url = f"{target.rstrip('/')}/redfish/v1/Systems/System.Embedded.1"
            with httpx.Client(verify=False, timeout=30.0) as client:
                r = client.get(sys_url, auth=(username, password))
                r.raise_for_status()
                data = r.json()
                bios_ver = (data.get("BiosVersion") or data.get("Bios", {}).get("Version") if isinstance(data.get("Bios"), dict) else None)
                if isinstance(bios_ver, dict):
                    bios_ver = bios_ver.get("Version")
                mgr_url = f"{target.rstrip('/')}/redfish/v1/Managers/iDRAC.Embedded.1"
                r2 = client.get(mgr_url, auth=(username, password))
                if r2.status_code == 200:
                    m = r2.json()
                    idrac_ver = m.get("FirmwareVersion") or m.get("ManagerFirmwareVersion")
        except Exception as e:
            err = str(e)[:1024]
    inv = db.query(IDracInventory).filter(IDracInventory.host_id == host_id).first()
    if not inv:
        inv = IDracInventory(
            host_id=host_id,
            target_url=target,
            bios_version=bios_ver or "unknown",
            idrac_version=idrac_ver or "unknown",
            compliance_status="unknown",
            last_scan_at=now,
            scan_error=err,
        )
        db.add(inv)
    else:
        inv.target_url = target
        if bios_ver:
            inv.bios_version = bios_ver
        if idrac_ver:
            inv.idrac_version = idrac_ver
        inv.last_scan_at = now
        inv.scan_error = err
    db.commit()
    db.refresh(inv)
    return {"ok": err is None, "id": inv.id, "error": err}
