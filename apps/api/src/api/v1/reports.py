# Reports: definitions, run with CSV output to REPORT_STORAGE_DIR, download
import csv
import io
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session
from src.config import settings
from src.core.rbac import require_permission
from src.models.user import User
from src.models import ReportDefinition, ReportRun, VirtualMachine, Host

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportDefinitionResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None

    class Config:
        from_attributes = True


class ReportRunResponse(BaseModel):
    id: int
    report_definition_id: int
    started_at: str
    finished_at: str | None
    status: str
    result_path: str | None

    class Config:
        from_attributes = True


def _generate_csv(db: Session, slug: str) -> str:
    buf = io.StringIO()
    if slug == "vm-inventory":
        w = csv.writer(buf)
        w.writerow(["id", "name", "power_state", "cluster_id", "host_id", "external_id", "ip_address"])
        for vm in db.query(VirtualMachine).order_by(VirtualMachine.id).all():
            w.writerow(
                [
                    vm.id,
                    vm.name,
                    vm.power_state or "",
                    vm.cluster_id or "",
                    vm.host_id or "",
                    vm.external_id or "",
                    vm.ip_address or "",
                ]
            )
    elif slug == "host-summary":
        w = csv.writer(buf)
        w.writerow(["id", "name", "type", "site_id", "cluster_id", "external_id", "ip_address"])
        for h in db.query(Host).order_by(Host.id).all():
            w.writerow(
                [
                    h.id,
                    h.name,
                    h.type,
                    h.site_id or "",
                    h.cluster_id or "",
                    h.external_id or "",
                    h.ip_address or "",
                ]
            )
    else:
        w = csv.writer(buf)
        w.writerow(["message"])
        w.writerow([f"Unknown report slug: {slug}"])
    return buf.getvalue()


@router.get("/definitions", response_model=list[ReportDefinitionResponse])
def list_report_definitions(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("reports:read")),
):
    return db.query(ReportDefinition).order_by(ReportDefinition.name).all()


@router.get("/runs", response_model=list[ReportRunResponse])
def list_report_runs(
    report_definition_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("reports:read")),
):
    q = db.query(ReportRun).order_by(ReportRun.started_at.desc())
    if report_definition_id is not None:
        q = q.filter(ReportRun.report_definition_id == report_definition_id)
    runs = q.limit(limit).all()
    return [
        ReportRunResponse(
            id=r.id,
            report_definition_id=r.report_definition_id,
            started_at=r.started_at.isoformat() if r.started_at else "",
            finished_at=r.finished_at.isoformat() if r.finished_at else None,
            status=r.status,
            result_path=r.result_path,
        )
        for r in runs
    ]


@router.post("/definitions/{definition_id}/run")
def run_report(
    definition_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("reports:read")),
):
    defn = db.query(ReportDefinition).filter(ReportDefinition.id == definition_id).first()
    if not defn:
        raise HTTPException(status_code=404, detail="Report not found")
    started = datetime.utcnow()
    run = ReportRun(
        report_definition_id=definition_id,
        user_id=current_user.id,
        params_json=None,
        started_at=started,
        finished_at=None,
        status="running",
        result_path=None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        os.makedirs(settings.report_storage_dir, mode=0o755, exist_ok=True)
        content = _generate_csv(db, defn.slug)
        fname = f"report_{run.id}_{defn.slug}.csv"
        fpath = os.path.join(settings.report_storage_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        run.status = "completed"
        run.finished_at = datetime.utcnow()
        run.result_path = fname
        db.commit()
        return {"status": "ok", "run_id": run.id, "result_path": fname, "message": "Report generated"}
    except Exception as e:
        run.status = "failed"
        run.finished_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/runs/{run_id}/download")
def download_report(
    run_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("reports:read")),
):
    run = db.query(ReportRun).filter(ReportRun.id == run_id).first()
    if not run or not run.result_path:
        raise HTTPException(status_code=404, detail="Report file not found")
    path = os.path.join(settings.report_storage_dir, run.result_path)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(path, filename=run.result_path, media_type="text/csv")
