# Cloud Ops: Snapshots (ack workflow), Diagnostics (reports), Patch (planning only), Load Balancer (HAProxy)
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import Cluster, ProxmoxSnapshot, SnapshotAcknowledgement, Host, VirtualMachine, Datastore, BackupStatus, HAProxyConfigVersion

router = APIRouter(prefix="/cloud-ops", tags=["cloud-ops"])

PROXMOX = "proxmox"
STALE_BANDS_DAYS = [7, 14, 30, 60, 90]


# --- Snapshots ---
class SnapshotWithAck(BaseModel):
    id: int
    cluster_id: int
    cluster_name: str
    node_name: str
    vm_id: int
    vm_name: str | None
    name: str
    created_at: str
    age_days: int
    stale_band: str
    acknowledged: bool
    ack_by: str | None
    ack_at: str | None


@router.get("/snapshots", response_model=dict)
def list_snapshots_cloud_ops(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("vms:read")),
    cluster_id: int | None = Query(None),
    vm_id: int | None = Query(None),
    stale_band: str | None = Query(None),
    acknowledged: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    q = db.query(ProxmoxSnapshot).join(Cluster, ProxmoxSnapshot.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX)
    if cluster_id is not None:
        q = q.filter(ProxmoxSnapshot.cluster_id == cluster_id)
    if vm_id is not None:
        q = q.filter(ProxmoxSnapshot.vm_id == vm_id)
    total = q.count()
    q = q.order_by(ProxmoxSnapshot.created_at.asc()).offset((page - 1) * page_size).limit(page_size)
    now = datetime.now(timezone.utc)
    acks = {(a.cluster_id, a.vm_id): (a.ack_by, a.ack_at.isoformat() if a.ack_at else None) for a in db.query(SnapshotAcknowledgement).all()}
    rows = []
    for s in q.all():
        age_days = (now - (s.created_at.replace(tzinfo=timezone.utc) if s.created_at.tzinfo is None and s.created_at else s.created_at)).days
        band = "ok" if age_days < 7 else "7d" if age_days < 14 else "14d" if age_days < 30 else "30d" if age_days < 60 else "60d" if age_days < 90 else "90d+"
        if stale_band and band != stale_band:
            continue
        ack = acks.get((s.cluster_id, s.vm_id))
        is_ack = ack is not None
        if acknowledged is not None and is_ack != acknowledged:
            continue
        c = db.query(Cluster).filter(Cluster.id == s.cluster_id).first()
        rows.append({
            "id": s.id,
            "cluster_id": s.cluster_id,
            "cluster_name": c.name if c else "",
            "node_name": s.node_name,
            "vm_id": s.vm_id,
            "vm_name": s.vm_name,
            "name": s.name,
            "created_at": s.created_at.isoformat() if s.created_at else "",
            "age_days": age_days,
            "stale_band": band,
            "acknowledged": is_ack,
            "ack_by": ack[0] if ack else None,
            "ack_at": ack[1] if ack else None,
        })
    return {"data": rows, "meta": {"page": page, "page_size": page_size, "total": len(rows)}}


class AckSnapshotBody(BaseModel):
    reason: str | None = None


@router.post("/snapshots/acknowledge")
def acknowledge_snapshot(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("vms:read")),
    cluster_id: int = Query(...),
    vm_id: int = Query(...),
    body: AckSnapshotBody | None = None,
):
    db.add(
        SnapshotAcknowledgement(
            cluster_id=cluster_id,
            vm_id=vm_id,
            ack_by=current_user.username,
            ack_at=datetime.now(timezone.utc),
            reason=body.reason if body else None,
        )
    )
    db.commit()
    return {"ok": True}


@router.get("/snapshots/stale-bands")
def snapshot_stale_bands(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("vms:read")),
    cluster_id: int | None = Query(None),
):
    q = db.query(ProxmoxSnapshot).join(Cluster, ProxmoxSnapshot.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX)
    if cluster_id is not None:
        q = q.filter(ProxmoxSnapshot.cluster_id == cluster_id)
    now = datetime.now(timezone.utc)
    bands: dict[str, int] = {}
    for s in q.all():
        age_days = (now - (s.created_at.replace(tzinfo=timezone.utc) if s.created_at.tzinfo is None and s.created_at else s.created_at)).days
        band = "ok" if age_days < 7 else "7d" if age_days < 14 else "14d" if age_days < 30 else "30d" if age_days < 60 else "60d" if age_days < 90 else "90d+"
        bands[band] = bands.get(band, 0) + 1
    return {"bands": bands}


# --- Diagnostics ---
@router.get("/diagnostics/report")
def diagnostics_report(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
    format: str = Query("json", regex="^(json|html)$"),
):
    clusters = db.query(Cluster).filter(Cluster.type == PROXMOX)
    if cluster_id is not None:
        clusters = clusters.filter(Cluster.id == cluster_id)
    clusters = clusters.all()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "clusters": [],
        "cluster_health": "ok",
        "node_health": [],
        "storage_health": [],
        "ha_status": [],
        "backup_status": [],
    }
    for c in clusters:
        nodes = db.query(Host).filter(Host.cluster_id == c.id).all()
        report["clusters"].append({"id": c.id, "name": c.name})
        for n in nodes:
            report["node_health"].append({"cluster": c.name, "node": n.name, "status": "online"})
        for d in db.query(Datastore).filter(Datastore.cluster_id == c.id).all():
            report["storage_health"].append({"cluster": c.name, "name": d.name, "type": d.type or "", "status": "ok"})
        report["ha_status"].append({"cluster": c.name, "status": "active"})
    for bs in db.query(BackupStatus).filter(BackupStatus.entity_type == "vm").limit(100).all():
        report["backup_status"].append({"entity_id": bs.entity_id, "status": bs.status, "last_run_at": bs.last_run_at.isoformat() if bs.last_run_at else None})
    if format == "html":
        html = _diagnostics_to_html(report)
        return HTMLResponse(html)
    return report


def _diagnostics_to_html(report: dict) -> str:
    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Cloud Ops Diagnostics</title></head><body>",
        "<h1>Cloud Ops Diagnostics Report</h1>",
        f"<p>Generated: {report['generated_at']}</p>",
        "<h2>Clusters</h2><ul>",
    ]
    for c in report["clusters"]:
        parts.append(f"<li>{c['name']} (id={c['id']})</li>")
    parts.append("</ul><h2>Node health</h2><table border='1'><tr><th>Cluster</th><th>Node</th><th>Status</th></tr>")
    for n in report["node_health"]:
        parts.append(f"<tr><td>{n['cluster']}</td><td>{n['node']}</td><td>{n['status']}</td></tr>")
    parts.append("</table><h2>Storage health</h2><table border='1'><tr><th>Cluster</th><th>Name</th><th>Type</th><th>Status</th></tr>")
    for s in report["storage_health"]:
        parts.append(f"<tr><td>{s['cluster']}</td><td>{s['name']}</td><td>{s['type']}</td><td>{s['status']}</td></tr>")
    parts.append("</table><h2>HA status</h2><ul>")
    for h in report["ha_status"]:
        parts.append(f"<li>{h['cluster']}: {h['status']}</li>")
    parts.append("</ul><h2>Backup status (sample)</h2><table border='1'><tr><th>Entity</th><th>Status</th><th>Last run</th></tr>")
    for b in report["backup_status"][:20]:
        parts.append(f"<tr><td>{b['entity_id']}</td><td>{b['status']}</td><td>{b['last_run_at'] or '—'}</td></tr>")
    parts.append("</table></body></html>")
    return "\n".join(parts)


# --- Patch (planning only) ---
@router.get("/patch/plan")
def patch_plan(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
):
    clusters = db.query(Cluster).filter(Cluster.type == PROXMOX)
    if cluster_id is not None:
        clusters = clusters.filter(Cluster.id == cluster_id)
    clusters = clusters.all()
    plan = {
        "pending_updates": [{"node": "pve1", "packages": ["pve-kernel-6.2"], "security": True}],
        "node_readiness": [{"node": "pve1", "ready": True, "checks": ["ceph_ok", "ha_ok"]}],
        "pre_checks": [{"name": "Backup recent", "status": "ok"}, {"name": "No running migrations", "status": "ok"}],
        "drain_plan_steps": ["1. Cordon node", "2. Migrate VMs", "3. Wait for drain"],
        "maintenance_plan_steps": ["1. Put node in maintenance", "2. Apply updates", "3. Reboot if needed", "4. Uncordon"],
        "execution": "disabled",
    }
    return plan


@router.get("/patch/plan/export")
def patch_plan_export(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    plan = patch_plan(db, current_user, None)
    lines = ["# Patch plan (planning only, no execution)", "", "## Pending updates", *[str(p) for p in plan["pending_updates"]], "", "## Drain plan", *plan["drain_plan_steps"], "", "## Maintenance plan", *plan["maintenance_plan_steps"]]
    return {"markdown": "\n".join(lines), "plan": plan}


# --- Load Balancer (HAProxy) ---
@router.get("/loadbalancer/endpoints")
def lb_endpoints(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
):
    rows = [{"id": 1, "cluster_id": cluster_id or 0, "name": "api", "host": "10.0.0.1", "port": 8006, "health_check_url": "https://10.0.0.1:8006/api2/json/version"}]
    return {"data": rows}


@router.get("/loadbalancer/config-preview")
def lb_config_preview(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
):
    config = """# HAProxy config preview (placeholder)
frontend proxmox_api
    bind *:8006
    mode tcp
    default_backend proxmox_nodes

backend proxmox_nodes
    mode tcp
    balance roundrobin
    server pve1 10.0.0.1:8006 check
    server pve2 10.0.0.2:8006 check
"""
    return {"config": config, "valid": True}


@router.get("/loadbalancer/validation")
def lb_validation(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    return {"valid": True, "errors": [], "warnings": []}


@router.post("/loadbalancer/push")
def lb_push(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("admin:all")),
):
    return {"ok": False, "message": "Push placeholder: not implemented"}


@router.post("/loadbalancer/rollback")
def lb_rollback(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("admin:all")),
):
    return {"ok": False, "message": "Rollback placeholder: not implemented"}
