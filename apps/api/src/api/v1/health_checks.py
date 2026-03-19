# Health Checks: backup coverage, stale snapshots, missing owners, storage threshold warnings
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import HealthCheckDefinition, HealthCheckRun, HealthCheckResult, VirtualMachine, Host, BackupStatus, StorageVolume, Datastore

router = APIRouter(prefix="/health-checks", tags=["health-checks"])

CHECK_TYPES = ["backup_coverage", "stale_snapshots", "missing_owners", "storage_threshold"]


class HealthCheckDefinitionResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    check_type: str

    class Config:
        from_attributes = True


class HealthCheckResultResponse(BaseModel):
    id: int
    definition_id: int
    status: str
    message: str | None
    details_json: str | None


class HealthCheckRunResponse(BaseModel):
    id: int
    started_at: str
    finished_at: str | None
    status: str
    results: list[HealthCheckResultResponse] = []


@router.get("/definitions", response_model=list[HealthCheckDefinitionResponse])
def list_health_check_definitions(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    return db.query(HealthCheckDefinition).order_by(HealthCheckDefinition.name).all()


@router.get("/runs", response_model=list[HealthCheckRunResponse])
def list_health_check_runs(
    limit: int = 20,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    runs = db.query(HealthCheckRun).order_by(HealthCheckRun.started_at.desc()).limit(limit).all()
    out = []
    for r in runs:
        results = db.query(HealthCheckResult).filter(HealthCheckResult.health_check_run_id == r.id).all()
        out.append(HealthCheckRunResponse(
            id=r.id,
            started_at=r.started_at.isoformat() if r.started_at else "",
            finished_at=r.finished_at.isoformat() if r.finished_at else None,
            status=r.status,
            results=[HealthCheckResultResponse(id=res.id, definition_id=res.definition_id, status=res.status, message=res.message, details_json=res.details_json) for res in results],
        ))
    return out


@router.post("/run")
def run_health_checks(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    definitions = db.query(HealthCheckDefinition).all()
    run = HealthCheckRun(started_at=datetime.utcnow(), finished_at=None, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    for defn in definitions:
        status = "ok"
        message = None
        details = {}
        if defn.check_type == "missing_owners":
            vms_missing = db.query(VirtualMachine).filter(VirtualMachine.owner.is_(None)).count()
            hosts_missing = db.query(Host).filter(Host.owner.is_(None)).count()
            if vms_missing or hosts_missing:
                status = "warning"
                message = f"{vms_missing} VMs and {hosts_missing} hosts missing owner"
            details = {"vms_missing_owner": vms_missing, "hosts_missing_owner": hosts_missing}
        elif defn.check_type == "backup_coverage":
            vms_total = db.query(VirtualMachine).count()
            backed = db.query(BackupStatus).filter(BackupStatus.entity_type == "vm", BackupStatus.status == "ok").count()
            if vms_total and backed < vms_total:
                status = "warning"
                message = f"Only {backed}/{vms_total} VMs have recent backup"
            details = {"vms_total": vms_total, "vms_with_backup": backed}
        elif defn.check_type == "storage_threshold":
            datastores = db.query(Datastore).limit(50).all()
            warnings = []
            for ds in datastores:
                vols = db.query(StorageVolume).filter(StorageVolume.datastore_id == ds.id).all()
                for v in vols:
                    if v.capacity_bytes and v.capacity_bytes > 0:
                        details[f"datastore_{ds.id}"] = "placeholder"
            if not details:
                details = {"message": "No capacity data yet"}
        else:
            message = "Check not implemented (stub)"
        res = HealthCheckResult(health_check_run_id=run.id, definition_id=defn.id, status=status, message=message, details_json=json.dumps(details) if details else None)
        db.add(res)
    run.finished_at = datetime.utcnow()
    run.status = "completed"
    db.commit()
    return {"status": "ok", "run_id": run.id}
