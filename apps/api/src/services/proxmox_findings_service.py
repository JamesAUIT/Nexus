"""Proxmox-specific findings: no backup, stale snapshot, guest agent missing, ballooning disabled, etc."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.models import (
    Cluster,
    Host,
    VirtualMachine,
    Datastore,
    BackupStatus,
    ProxmoxSnapshot,
    ProxmoxFinding,
    ProxmoxTask,
)

# Finding type slugs
NO_BACKUP = "no_backup"
STALE_SNAPSHOT = "stale_snapshot"
GUEST_AGENT_MISSING = "guest_agent_missing"
BALLOONING_DISABLED = "ballooning_disabled"
LOCAL_STORAGE_ONLY = "local_storage_only"
FAILED_TASKS = "failed_tasks"
STALE_BACKUPS = "stale_backups"


def run_findings_for_cluster(db: Session, cluster_id: int) -> int:
    """Compute and upsert Proxmox findings for a cluster. Returns count of findings written."""
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id, Cluster.type == "proxmox").first()
    if not cluster:
        return 0

    now = datetime.now(timezone.utc)
    stale_snapshot_days = 30
    stale_backup_days = 7
    count = 0

    # Clear existing findings for this cluster so we don't duplicate
    db.query(ProxmoxFinding).filter(ProxmoxFinding.cluster_id == cluster_id).delete()

    # No backup: VMs with no backup status or status not ok
    vms = db.query(VirtualMachine).filter(VirtualMachine.cluster_id == cluster_id).all()
    for vm in vms:
        entity_id = str(vm.external_id) if vm.external_id else f"vm-{vm.id}"
        backup = (
            db.query(BackupStatus)
            .filter(
                BackupStatus.entity_type == "vm",
                BackupStatus.entity_id == entity_id,
            )
            .first()
        )
        if not backup or backup.status != "ok":
            db.add(
                ProxmoxFinding(
                    cluster_id=cluster_id,
                    entity_type="vm",
                    entity_id=entity_id,
                    finding_type=NO_BACKUP,
                    title="No backup",
                    detail=vm.name,
                    severity="high",
                    created_at=now,
                )
            )
            count += 1

    # Stale snapshot: snapshots older than N days
    cutoff = now - timedelta(days=stale_snapshot_days)
    for snap in (
        db.query(ProxmoxSnapshot)
        .filter(ProxmoxSnapshot.cluster_id == cluster_id, ProxmoxSnapshot.created_at < cutoff)
        .all()
    ):
        db.add(
            ProxmoxFinding(
                cluster_id=cluster_id,
                entity_type="vm",
                entity_id=str(snap.vm_id),
                finding_type=STALE_SNAPSHOT,
                title="Stale snapshot",
                detail=f"{snap.vm_name or snap.vm_id} / {snap.name}",
                severity="medium",
                created_at=now,
            )
        )
        count += 1

    # Guest agent missing / ballooning disabled: placeholders when we have no per-VM data from Proxmox API
    if vms:
        db.add(
            ProxmoxFinding(
                cluster_id=cluster_id,
                entity_type="cluster",
                entity_id=str(cluster_id),
                finding_type=GUEST_AGENT_MISSING,
                title="Guest agent missing (sample)",
                detail="Check VMs for QEMU guest agent",
                severity="low",
                created_at=now,
            )
        )
        count += 1
        db.add(
            ProxmoxFinding(
                cluster_id=cluster_id,
                entity_type="cluster",
                entity_id=str(cluster_id),
                finding_type=BALLOONING_DISABLED,
                title="Ballooning disabled (sample)",
                detail="Check memory balloon on VMs",
                severity="low",
                created_at=now,
            )
        )
        count += 1

    # Local storage only: nodes (hosts) that only have local datastores
    for host in db.query(Host).filter(Host.cluster_id == cluster_id).all():
        datastores = db.query(Datastore).filter(Datastore.host_id == host.id).all()
        if datastores and all(d.type in ("local", "directory", None) for d in datastores):
            db.add(
                ProxmoxFinding(
                    cluster_id=cluster_id,
                    entity_type="node",
                    entity_id=str(host.external_id) if host.external_id else f"node-{host.id}",
                    finding_type=LOCAL_STORAGE_ONLY,
                    title="Local storage only",
                    detail=host.name,
                    severity="medium",
                    created_at=now,
                )
            )
            count += 1

    # Failed tasks
    for task in (
        db.query(ProxmoxTask)
        .filter(ProxmoxTask.cluster_id == cluster_id, ProxmoxTask.status == "failed")
        .all()
    ):
        db.add(
            ProxmoxFinding(
                cluster_id=cluster_id,
                entity_type="task",
                entity_id=task.upid or f"task-{task.id}",
                finding_type=FAILED_TASKS,
                title="Failed task",
                detail=task.details or task.type or "",
                severity="high",
                created_at=now,
            )
        )
        count += 1

    # Stale backups: backup status older than N days
    cutoff_backup = now - timedelta(days=stale_backup_days)
    for bs in (
        db.query(BackupStatus)
        .filter(
            BackupStatus.entity_type == "vm",
            BackupStatus.last_run_at.isnot(None),
            BackupStatus.last_run_at < cutoff_backup,
        )
        .all()
    ):
        db.add(
            ProxmoxFinding(
                cluster_id=cluster_id,
                entity_type="vm",
                entity_id=bs.entity_id,
                finding_type=STALE_BACKUPS,
                title="Stale backup",
                detail=bs.details or bs.entity_id,
                severity="medium",
                created_at=now,
            )
        )
        count += 1

    db.commit()
    return count
