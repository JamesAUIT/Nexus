# Dashboard widgets: connector health, certs, firmware, snapshots, backups, changes, sync failures
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import Connector, SyncJob, SyncJobRun, TLSCertificate, IDracInventory, ProxmoxSnapshot, BackupStatus, VirtualMachine, ChangeEvent

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/widgets")
def get_widgets(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    now = datetime.now(timezone.utc)

    # Connector health & data freshness
    connectors = db.query(Connector).all()
    conn_summary = [{"id": c.id, "name": c.name, "status": "healthy" if c.last_ok_at and not c.last_error else "unhealthy", "last_ok_at": c.last_ok_at.isoformat() if c.last_ok_at else None} for c in connectors]

    # Expiring certificates
    cert_critical = db.query(TLSCertificate).filter(TLSCertificate.severity == "critical").count()
    cert_high = db.query(TLSCertificate).filter(TLSCertificate.severity == "high").count()
    cert_expiring = list(db.query(TLSCertificate).filter(TLSCertificate.severity.in_(["critical", "high"])).order_by(TLSCertificate.not_after.asc()).limit(5))

    # Outdated firmware (compliance_status)
    firmware_outdated = db.query(IDracInventory).filter(IDracInventory.compliance_status == "outdated").count()

    # Stale snapshots (older than 30d)
    cutoff_snap = now - timedelta(days=30)
    stale_snapshots = db.query(ProxmoxSnapshot).filter(ProxmoxSnapshot.created_at < cutoff_snap).count()

    # Missing backups (VMs without backup status)
    vms = db.query(VirtualMachine).count()
    backed_count = db.query(BackupStatus).filter(BackupStatus.entity_type == "vm").count()
    missing_backups = max(0, vms - backed_count)

    # Recent changes (last 24h)
    cutoff_changes = now - timedelta(hours=24)
    recent_changes = db.query(ChangeEvent).filter(ChangeEvent.changed_at >= cutoff_changes).count()

    # Recent sync failures
    recent_failures = db.query(SyncJobRun).filter(SyncJobRun.status == "failed", SyncJobRun.started_at >= now - timedelta(days=7)).count()

    return {
        "connector_health": conn_summary,
        "expiring_certificates": {"critical": cert_critical, "high": cert_high, "list": [{"hostname": c.hostname, "port": c.port, "severity": c.severity, "days_until_expiry": c.days_until_expiry} for c in cert_expiring]},
        "outdated_firmware_count": firmware_outdated,
        "stale_snapshots_count": stale_snapshots,
        "missing_backups_count": missing_backups,
        "recent_changes_count": recent_changes,
        "recent_sync_failures_count": recent_failures,
    }
