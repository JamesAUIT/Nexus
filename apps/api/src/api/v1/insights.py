# Insights engine: rule-based recommendations
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import VirtualMachine, ProxmoxSnapshot, BackupStatus, Datastore, TLSCertificate, IDracInventory, StorageVolume

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=dict)
def list_insights(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    rule: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    now = datetime.now(timezone.utc)
    insights = []

    # Oversized VMs — heuristic: any VM with tag or name hint (extend when vCPU/RAM on model)
    if not rule or rule == "oversized_vms":
        for vm in db.query(VirtualMachine).limit(limit).all():
            if vm.tags and ("large" in vm.tags.lower() or "xl" in vm.tags.lower()):
                insights.append({"rule": "oversized_vms", "entity_type": "vm", "entity_id": str(vm.id), "title": "Review VM sizing (tag hint)", "detail": vm.name, "severity": "low"})

    # Stale snapshots
    if not rule or rule == "stale_snapshots":
        cutoff = now - timedelta(days=30)
        for s in db.query(ProxmoxSnapshot).filter(ProxmoxSnapshot.created_at < cutoff).limit(limit).all():
            insights.append({"rule": "stale_snapshots", "entity_type": "vm", "entity_id": str(s.vm_id), "title": "Stale snapshot", "detail": f"{s.vm_name or s.vm_id} / {s.name}", "severity": "medium"})

    # Missing backups
    if not rule or rule == "missing_backups":
        vms = db.query(VirtualMachine).all()
        for vm in vms[:limit]:
            eid = str(vm.external_id) if vm.external_id else f"vm-{vm.id}"
            if not db.query(BackupStatus).filter(BackupStatus.entity_type == "vm", BackupStatus.entity_id == eid).first():
                insights.append({"rule": "missing_backups", "entity_type": "vm", "entity_id": str(vm.id), "title": "No backup", "detail": vm.name, "severity": "high"})

    # High storage — flag datastores with many volumes (capacity model is partial)
    if not rule or rule == "high_storage":
        for d in db.query(Datastore).limit(10).all():
            nvol = db.query(StorageVolume).filter(StorageVolume.datastore_id == d.id).count()
            if nvol >= 5:
                insights.append({"rule": "high_storage", "entity_type": "datastore", "entity_id": str(d.id), "title": "Many volumes on datastore", "detail": f"{d.name} ({nvol} volumes)", "severity": "low"})

    # Firmware outdated
    if not rule or rule == "firmware_outdated":
        for inv in db.query(IDracInventory).filter(IDracInventory.compliance_status == "outdated").limit(limit).all():
            insights.append({"rule": "firmware_outdated", "entity_type": "host", "entity_id": str(inv.host_id or inv.id), "title": "Firmware outdated", "detail": inv.idrac_version or "", "severity": "medium"})

    # Expiring certificates
    if not rule or rule == "expiring_certificates":
        for c in db.query(TLSCertificate).filter(TLSCertificate.severity.in_(["critical", "high", "medium"])).limit(limit).all():
            insights.append({"rule": "expiring_certificates", "entity_type": "certificate", "entity_id": str(c.id), "title": "Certificate expiring", "detail": f"{c.hostname}:{c.port}", "severity": c.severity})

    return {"data": insights[:limit]}
