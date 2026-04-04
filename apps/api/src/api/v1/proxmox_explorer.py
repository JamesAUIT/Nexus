# Proxmox Explorer API: nodes, VMs, storage, snapshots, backups, networks, containers, disks, tasks, replication, HA
from io import BytesIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.core.cache import cache_get, cache_set
from src.models.user import User
from src.models import (
    Cluster,
    Host,
    VirtualMachine,
    Datastore,
    BackupStatus,
    ProxmoxSnapshot,
    ProxmoxFinding,
    ProxmoxTask,
    ProxmoxEntity,
)
from src.services.proxmox_findings_service import run_findings_for_cluster

router = APIRouter(prefix="/proxmox-explorer", tags=["proxmox-explorer"])

PROXMOX_CLUSTER_TYPE = "proxmox"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
CACHE_PREFIX = "proxmox_explorer"
CACHE_TTL = 120


# --- Response models ---
class PaginatedMeta(BaseModel):
    page: int
    page_size: int
    total: int


class NodeRow(BaseModel):
    id: int
    cluster_id: int
    cluster_name: str | None
    name: str
    type: str
    external_id: str | None
    ip_address: str | None

    class Config:
        from_attributes = True


class VMRow(BaseModel):
    id: int
    cluster_id: int
    cluster_name: str | None
    host_id: int | None
    node_name: str | None
    name: str
    power_state: str | None
    external_id: str | None
    ip_address: str | None

    class Config:
        from_attributes = True


class StorageRow(BaseModel):
    id: int
    cluster_id: int | None
    cluster_name: str | None
    host_id: int | None
    node_name: str | None
    name: str
    type: str | None
    external_id: str | None

    class Config:
        from_attributes = True


class SnapshotRow(BaseModel):
    id: int
    cluster_id: int
    node_name: str
    vm_id: int
    vm_name: str | None
    name: str
    created_at: str
    size_bytes: int | None

    class Config:
        from_attributes = True


class BackupRow(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    status: str
    last_run_at: str | None
    details: str | None

    class Config:
        from_attributes = True


class FindingRow(BaseModel):
    id: int
    cluster_id: int
    entity_type: str
    entity_id: str
    finding_type: str
    title: str
    detail: str | None
    severity: str

    class Config:
        from_attributes = True


class TaskRow(BaseModel):
    id: int
    cluster_id: int
    node_name: str
    type: str | None
    status: str
    start_time: str | None
    end_time: str | None
    user: str | None

    class Config:
        from_attributes = True


def _proxmox_cluster_ids(db: Session) -> list[int]:
    return [c.id for c in db.query(Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE).all()]


def _clusters_list(db: Session) -> list[dict]:
    return [
        {"id": c.id, "name": c.name, "type": c.type}
        for c in db.query(Cluster).filter(Cluster.type == PROXMOX_CLUSTER_TYPE).order_by(Cluster.name).all()
    ]


@router.get("/clusters")
def list_clusters(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    return _clusters_list(db)


@router.get("/nodes")
def list_nodes(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("hosts:read")),
    cluster_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    use_cache: bool = Query(True),
):
    cache_key = f"{CACHE_PREFIX}:nodes:{cluster_id}:{search}:{page}:{page_size}" if use_cache else None
    if cache_key:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    q = db.query(Host).join(Cluster, Host.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE)
    if cluster_id is not None:
        q = q.filter(Host.cluster_id == cluster_id)
    if search:
        q = q.filter(or_(Host.name.ilike(f"%{search}%"), Host.external_id.ilike(f"%{search}%") if Host.external_id else False))
    total = q.count()
    q = q.order_by(Host.name).offset((page - 1) * page_size).limit(page_size)
    rows = []
    for h in q.all():
        c = db.query(Cluster).filter(Cluster.id == h.cluster_id).first()
        rows.append(
            NodeRow(
                id=h.id,
                cluster_id=h.cluster_id or 0,
                cluster_name=c.name if c else None,
                name=h.name,
                type=h.type,
                external_id=h.external_id,
                ip_address=getattr(h, "ip_address", None),
            )
        )
    out = {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}
    if cache_key:
        cache_set(cache_key, out, CACHE_TTL)
    return out


def _node_name(db: Session, host_id: int | None) -> str | None:
    if not host_id:
        return None
    h = db.query(Host).filter(Host.id == host_id).first()
    return h.name if h else None


@router.get("/vms")
def list_vms(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("vms:read")),
    cluster_id: int | None = Query(None),
    node_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    use_cache: bool = Query(True),
):
    cache_key = f"{CACHE_PREFIX}:vms:{cluster_id}:{node_id}:{search}:{page}:{page_size}" if use_cache else None
    if cache_key:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    q = db.query(VirtualMachine).join(Cluster, VirtualMachine.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE)
    if cluster_id is not None:
        q = q.filter(VirtualMachine.cluster_id == cluster_id)
    if node_id is not None:
        q = q.filter(VirtualMachine.host_id == node_id)
    if search:
        q = q.filter(
            or_(
                VirtualMachine.name.ilike(f"%{search}%"),
                (VirtualMachine.external_id.isnot(None) & VirtualMachine.external_id.ilike(f"%{search}%")),
                (VirtualMachine.ip_address.isnot(None) & VirtualMachine.ip_address.ilike(f"%{search}%")),
            )
        )
    total = q.count()
    q = q.order_by(VirtualMachine.name).offset((page - 1) * page_size).limit(page_size)
    rows = []
    for v in q.all():
        c = db.query(Cluster).filter(Cluster.id == v.cluster_id).first()
        rows.append(
            VMRow(
                id=v.id,
                cluster_id=v.cluster_id or 0,
                cluster_name=c.name if c else None,
                host_id=v.host_id,
                node_name=_node_name(db, v.host_id),
                name=v.name,
                power_state=v.power_state,
                external_id=v.external_id,
                ip_address=getattr(v, "ip_address", None),
            )
        )
    out = {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}
    if cache_key:
        cache_set(cache_key, out, CACHE_TTL)
    return out


@router.get("/storage")
def list_storage(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    ids = _proxmox_cluster_ids(db)
    if not ids:
        return {"data": [], "meta": PaginatedMeta(page=page, page_size=page_size, total=0)}
    q = db.query(Datastore).filter(Datastore.cluster_id.in_(ids))
    if cluster_id is not None:
        q = q.filter(Datastore.cluster_id == cluster_id)
    if search:
        q = q.filter(Datastore.name.ilike(f"%{search}%"))
    total = q.count()
    q = q.order_by(Datastore.name).offset((page - 1) * page_size).limit(page_size)
    rows = []
    for d in q.all():
        c = db.query(Cluster).filter(Cluster.id == d.cluster_id).first()
        rows.append(
            StorageRow(
                id=d.id,
                cluster_id=d.cluster_id,
                cluster_name=c.name if c else None,
                host_id=d.host_id,
                node_name=_node_name(db, d.host_id),
                name=d.name,
                type=d.type,
                external_id=d.external_id,
            )
        )
    return {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}


@router.get("/snapshots")
def list_snapshots(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("vms:read")),
    cluster_id: int | None = Query(None),
    vm_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    q = db.query(ProxmoxSnapshot).join(Cluster, ProxmoxSnapshot.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE)
    if cluster_id is not None:
        q = q.filter(ProxmoxSnapshot.cluster_id == cluster_id)
    if vm_id is not None:
        q = q.filter(ProxmoxSnapshot.vm_id == vm_id)
    total = q.count()
    q = q.order_by(ProxmoxSnapshot.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = []
    for s in q.all():
        rows.append(
            SnapshotRow(
                id=s.id,
                cluster_id=s.cluster_id,
                node_name=s.node_name,
                vm_id=s.vm_id,
                vm_name=s.vm_name,
                name=s.name,
                created_at=s.created_at.isoformat() if s.created_at else "",
                size_bytes=s.size_bytes,
            )
        )
    return {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}


@router.get("/backups")
def list_backups(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    q = db.query(BackupStatus).filter(BackupStatus.entity_type == "vm")
    if status:
        q = q.filter(BackupStatus.status == status)
    total = q.count()
    q = q.order_by(BackupStatus.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = [
        BackupRow(
            id=b.id,
            entity_type=b.entity_type,
            entity_id=b.entity_id,
            status=b.status,
            last_run_at=b.last_run_at.isoformat() if b.last_run_at else None,
            details=b.details,
        )
        for b in q.all()
    ]
    return {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}


@router.get("/networks")
def list_networks(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    q = db.query(ProxmoxEntity).filter(ProxmoxEntity.kind == "network")
    if cluster_id is not None:
        q = q.filter(ProxmoxEntity.cluster_id == cluster_id)
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = [{"id": e.id, "cluster_id": e.cluster_id, "external_id": e.external_id, "data": e.data} for e in q.all()]
    if total == 0:
        rows = [{"id": 0, "cluster_id": cluster_id or 0, "external_id": "vmbr0", "data": "{\"name\":\"vmbr0\",\"bridge\":\"vmbr0\"}"}]
        total = 1
    return {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}


@router.get("/containers")
def list_containers(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    q = db.query(ProxmoxEntity).filter(ProxmoxEntity.kind == "container")
    if cluster_id is not None:
        q = q.filter(ProxmoxEntity.cluster_id == cluster_id)
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = [{"id": e.id, "cluster_id": e.cluster_id, "external_id": e.external_id, "data": e.data} for e in q.all()]
    if total == 0:
        rows = [{"id": 0, "cluster_id": cluster_id or 0, "external_id": "100", "data": "{\"name\":\"lxc-demo\",\"status\":\"stopped\"}"}]
        total = 1
    return {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}


@router.get("/disks")
def list_disks(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    q = db.query(ProxmoxEntity).filter(ProxmoxEntity.kind == "disk")
    if cluster_id is not None:
        q = q.filter(ProxmoxEntity.cluster_id == cluster_id)
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = [{"id": e.id, "cluster_id": e.cluster_id, "external_id": e.external_id, "data": e.data} for e in q.all()]
    if total == 0:
        rows = [{"id": 0, "cluster_id": cluster_id or 0, "external_id": "scsi0", "data": "{\"vm_id\":\"100\",\"size\":\"32G\"}"}]
        total = 1
    return {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}


@router.get("/tasks")
def list_tasks(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    q = db.query(ProxmoxTask).join(Cluster, ProxmoxTask.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE)
    if cluster_id is not None:
        q = q.filter(ProxmoxTask.cluster_id == cluster_id)
    if status:
        q = q.filter(ProxmoxTask.status == status)
    total = q.count()
    q = q.order_by(ProxmoxTask.start_time.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    rows = [
        TaskRow(
            id=t.id,
            cluster_id=t.cluster_id,
            node_name=t.node_name,
            type=t.type,
            status=t.status,
            start_time=t.start_time.isoformat() if t.start_time else None,
            end_time=t.end_time.isoformat() if t.end_time else None,
            user=t.user,
        )
        for t in q.all()
    ]
    return {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}


@router.get("/replication")
def list_replication(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
):
    q = db.query(ProxmoxEntity).filter(ProxmoxEntity.kind == "replication")
    if cluster_id is not None:
        q = q.filter(ProxmoxEntity.cluster_id == cluster_id)
    rows = [{"id": e.id, "cluster_id": e.cluster_id, "external_id": e.external_id, "data": e.data} for e in q.all()]
    if not rows:
        rows = [{"id": 0, "cluster_id": cluster_id or 0, "external_id": "job-1", "data": "{\"vm\":100,\"target\":\"pve2\"}"}]
    return {"data": rows}


@router.get("/ha")
def list_ha(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
):
    q = db.query(ProxmoxEntity).filter(ProxmoxEntity.kind == "ha")
    if cluster_id is not None:
        q = q.filter(ProxmoxEntity.cluster_id == cluster_id)
    rows = [{"id": e.id, "cluster_id": e.cluster_id, "external_id": e.external_id, "data": e.data} for e in q.all()]
    if not rows:
        rows = [{"id": 0, "cluster_id": cluster_id or 0, "external_id": "group-1", "data": "{\"group\":\"vm:100\"}"}]
    return {"data": rows}


@router.get("/findings")
def list_findings(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    cluster_id: int | None = Query(None),
    finding_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
):
    q = db.query(ProxmoxFinding).join(Cluster, ProxmoxFinding.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE)
    if cluster_id is not None:
        q = q.filter(ProxmoxFinding.cluster_id == cluster_id)
    if finding_type:
        q = q.filter(ProxmoxFinding.finding_type == finding_type)
    total = q.count()
    q = q.order_by(ProxmoxFinding.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = [
        FindingRow(
            id=f.id,
            cluster_id=f.cluster_id,
            entity_type=f.entity_type,
            entity_id=f.entity_id,
            finding_type=f.finding_type,
            title=f.title,
            detail=f.detail,
            severity=f.severity,
        )
        for f in q.all()
    ]
    return {"data": rows, "meta": PaginatedMeta(page=page, page_size=page_size, total=total)}


@router.post("/findings/run")
def run_findings(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("drift:write")),
    cluster_id: int | None = Query(None),
):
    cluster_ids = [cluster_id] if cluster_id else _proxmox_cluster_ids(db)
    total = 0
    for cid in cluster_ids:
        total += run_findings_for_cluster(db, cid)
    return {"findings_written": total}


# --- Export helpers ---
def _to_csv(rows: list[dict], columns: list[str]) -> bytes:
    import csv
    buf = BytesIO()
    w = csv.writer(buf)
    w.writerow(columns)
    for r in rows:
        w.writerow([r.get(c, "") for c in columns])
    return buf.getvalue()


def _to_xlsx(rows: list[dict], columns: list[str], sheet_name: str = "Export") -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(columns)
    for r in rows:
        ws.append([r.get(c, "") for c in columns])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _nodes_export_rows(db: Session, cluster_id: int | None, search: str | None) -> list[dict]:
    q = db.query(Host).join(Cluster, Host.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE)
    if cluster_id is not None:
        q = q.filter(Host.cluster_id == cluster_id)
    if search:
        q = q.filter(or_(Host.name.ilike(f"%{search}%"), (Host.external_id.isnot(None) & Host.external_id.ilike(f"%{search}%"))))
    q = q.order_by(Host.name)
    out = []
    for h in q.all():
        c = db.query(Cluster).filter(Cluster.id == h.cluster_id).first()
        out.append({
            "id": h.id, "cluster_id": h.cluster_id or 0, "cluster_name": c.name if c else "",
            "name": h.name, "type": h.type, "external_id": h.external_id or "", "ip_address": getattr(h, "ip_address", "") or "",
        })
    return out


@router.get("/nodes/export")
def export_nodes(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("hosts:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
    search: str | None = Query(None),
):
    rows = _nodes_export_rows(db, cluster_id, search)
    cols = ["id", "cluster_id", "cluster_name", "name", "type", "external_id", "ip_address"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-nodes.csv"})
    body = _to_xlsx(rows, cols, "Nodes")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-nodes.xlsx"})


def _vms_export_rows(db: Session, cluster_id: int | None, node_id: int | None, search: str | None) -> list[dict]:
    q = db.query(VirtualMachine).join(Cluster, VirtualMachine.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE)
    if cluster_id is not None:
        q = q.filter(VirtualMachine.cluster_id == cluster_id)
    if node_id is not None:
        q = q.filter(VirtualMachine.host_id == node_id)
    if search:
        q = q.filter(or_(VirtualMachine.name.ilike(f"%{search}%"), (VirtualMachine.external_id.isnot(None) & VirtualMachine.external_id.ilike(f"%{search}%"))))
    q = q.order_by(VirtualMachine.name)
    out = []
    for v in q.all():
        c = db.query(Cluster).filter(Cluster.id == v.cluster_id).first()
        out.append({
            "id": v.id, "cluster_id": v.cluster_id or 0, "cluster_name": c.name if c else "",
            "host_id": v.host_id or "", "node_name": _node_name(db, v.host_id) or "",
            "name": v.name, "power_state": v.power_state or "", "external_id": v.external_id or "", "ip_address": getattr(v, "ip_address", "") or "",
        })
    return out


@router.get("/vms/export")
def export_vms(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("vms:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
    node_id: int | None = Query(None),
    search: str | None = Query(None),
):
    rows = _vms_export_rows(db, cluster_id, node_id, search)
    cols = ["id", "cluster_id", "cluster_name", "host_id", "node_name", "name", "power_state", "external_id", "ip_address"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-vms.csv"})
    body = _to_xlsx(rows, cols, "Virtual Machines")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-vms.xlsx"})


@router.get("/storage/export")
def export_storage(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
):
    ids = _proxmox_cluster_ids(db)
    if not ids:
        rows = []
    else:
        q = db.query(Datastore).filter(Datastore.cluster_id.in_(ids))
        if cluster_id is not None:
            q = q.filter(Datastore.cluster_id == cluster_id)
        q = q.order_by(Datastore.name)
        rows = []
        for d in q.all():
            c = db.query(Cluster).filter(Cluster.id == d.cluster_id).first()
            rows.append({
                "id": d.id, "cluster_id": d.cluster_id or "", "cluster_name": c.name if c else "",
                "host_id": d.host_id or "", "node_name": _node_name(db, d.host_id) or "",
                "name": d.name, "type": d.type or "", "external_id": d.external_id or "",
            })
    cols = ["id", "cluster_id", "cluster_name", "host_id", "node_name", "name", "type", "external_id"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-storage.csv"})
    body = _to_xlsx(rows, cols, "Storage")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-storage.xlsx"})


@router.get("/snapshots/export")
def export_snapshots(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("vms:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
):
    ids = _proxmox_cluster_ids(db)
    if not ids:
        rows = []
    else:
        q = db.query(ProxmoxSnapshot).filter(ProxmoxSnapshot.cluster_id.in_(ids))
        if cluster_id is not None:
            q = q.filter(ProxmoxSnapshot.cluster_id == cluster_id)
        q = q.order_by(ProxmoxSnapshot.created_at.desc())
        rows = [{"id": s.id, "cluster_id": s.cluster_id, "node_name": s.node_name, "vm_id": s.vm_id, "vm_name": s.vm_name or "", "name": s.name, "created_at": s.created_at.isoformat() if s.created_at else "", "size_bytes": s.size_bytes or ""} for s in q.all()]
    cols = ["id", "cluster_id", "node_name", "vm_id", "vm_name", "name", "created_at", "size_bytes"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-snapshots.csv"})
    body = _to_xlsx(rows, cols, "Snapshots")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-snapshots.xlsx"})


@router.get("/backups/export")
def export_backups(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
):
    q = db.query(BackupStatus).filter(BackupStatus.entity_type == "vm").order_by(BackupStatus.updated_at.desc())
    rows = [{"id": b.id, "entity_type": b.entity_type, "entity_id": b.entity_id, "status": b.status, "last_run_at": b.last_run_at.isoformat() if b.last_run_at else "", "details": b.details or ""} for b in q.all()]
    cols = ["id", "entity_type", "entity_id", "status", "last_run_at", "details"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-backups.csv"})
    body = _to_xlsx(rows, cols, "Backups")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-backups.xlsx"})


@router.get("/findings/export")
def export_findings(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
):
    ids = _proxmox_cluster_ids(db)
    if not ids:
        rows = []
    else:
        q = db.query(ProxmoxFinding).filter(ProxmoxFinding.cluster_id.in_(ids))
        if cluster_id is not None:
            q = q.filter(ProxmoxFinding.cluster_id == cluster_id)
        q = q.order_by(ProxmoxFinding.created_at.desc())
        rows = [{"id": f.id, "cluster_id": f.cluster_id, "entity_type": f.entity_type, "entity_id": f.entity_id, "finding_type": f.finding_type, "title": f.title, "detail": f.detail or "", "severity": f.severity} for f in q.all()]
    cols = ["id", "cluster_id", "entity_type", "entity_id", "finding_type", "title", "detail", "severity"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-findings.csv"})
    body = _to_xlsx(rows, cols, "Findings")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-findings.xlsx"})


@router.get("/networks/export")
def export_networks(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
):
    r = list_networks(db, current_user, cluster_id, 1, MAX_PAGE_SIZE)
    rows = [{"id": x["id"], "cluster_id": x["cluster_id"], "external_id": x.get("external_id", ""), "data": x.get("data", "")} for x in r["data"]]
    cols = ["id", "cluster_id", "external_id", "data"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-networks.csv"})
    body = _to_xlsx(rows, cols, "Networks")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-networks.xlsx"})


@router.get("/containers/export")
def export_containers(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
):
    r = list_containers(db, current_user, cluster_id, 1, MAX_PAGE_SIZE)
    rows = [{"id": x["id"], "cluster_id": x["cluster_id"], "external_id": x.get("external_id", ""), "data": x.get("data", "")} for x in r["data"]]
    cols = ["id", "cluster_id", "external_id", "data"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-containers.csv"})
    body = _to_xlsx(rows, cols, "Containers")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-containers.xlsx"})


@router.get("/disks/export")
def export_disks(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
):
    r = list_disks(db, current_user, cluster_id, 1, MAX_PAGE_SIZE)
    rows = [{"id": x["id"], "cluster_id": x["cluster_id"], "external_id": x.get("external_id", ""), "data": x.get("data", "")} for x in r["data"]]
    cols = ["id", "cluster_id", "external_id", "data"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-disks.csv"})
    body = _to_xlsx(rows, cols, "Disks")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-disks.xlsx"})


@router.get("/replication/export")
def export_replication(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
):
    r = list_replication(db, current_user, cluster_id)
    rows = [{"id": x["id"], "cluster_id": x["cluster_id"], "external_id": x.get("external_id", ""), "data": x.get("data", "")} for x in r["data"]]
    cols = ["id", "cluster_id", "external_id", "data"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-replication.csv"})
    body = _to_xlsx(rows, cols, "Replication")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-replication.xlsx"})


@router.get("/ha/export")
def export_ha(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
):
    r = list_ha(db, current_user, cluster_id)
    rows = [{"id": x["id"], "cluster_id": x["cluster_id"], "external_id": x.get("external_id", ""), "data": x.get("data", "")} for x in r["data"]]
    cols = ["id", "cluster_id", "external_id", "data"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-ha.csv"})
    body = _to_xlsx(rows, cols, "HA")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-ha.xlsx"})


@router.get("/tasks/export")
def export_tasks(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    cluster_id: int | None = Query(None),
    status: str | None = Query(None),
):
    q = db.query(ProxmoxTask).join(Cluster, ProxmoxTask.cluster_id == Cluster.id).filter(Cluster.type == PROXMOX_CLUSTER_TYPE)
    if cluster_id is not None:
        q = q.filter(ProxmoxTask.cluster_id == cluster_id)
    if status:
        q = q.filter(ProxmoxTask.status == status)
    q = q.order_by(ProxmoxTask.start_time.desc().nullslast())
    rows = [{"id": t.id, "cluster_id": t.cluster_id, "node_name": t.node_name, "type": t.type or "", "status": t.status, "start_time": t.start_time.isoformat() if t.start_time else "", "end_time": t.end_time.isoformat() if t.end_time else "", "user": t.user or ""} for t in q.all()]
    cols = ["id", "cluster_id", "node_name", "type", "status", "start_time", "end_time", "user"]
    if format == "csv":
        body = _to_csv(rows, cols)
        return StreamingResponse(BytesIO(body), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=proxmox-tasks.csv"})
    body = _to_xlsx(rows, cols, "Tasks")
    return StreamingResponse(BytesIO(body), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=proxmox-tasks.xlsx"})
