# Reports: prebuilt definitions, execution history, CSV export placeholder, saved filters
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import ReportDefinition, ReportRun

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
    q = db.query(ReportRun).order_by(ReportRun.started_at.desc()).limit(limit)
    if report_definition_id is not None:
        q = q.filter(ReportRun.report_definition_id == report_definition_id)
    runs = q.all()
    return [ReportRunResponse(
        id=r.id,
        report_definition_id=r.report_definition_id,
        started_at=r.started_at.isoformat() if r.started_at else "",
        finished_at=r.finished_at.isoformat() if r.finished_at else None,
        status=r.status,
        result_path=r.result_path,
    ) for r in runs]


@router.post("/definitions/{definition_id}/run")
def run_report(
  definition_id: int,
  db: Session = Depends(get_db_session),
  current_user: User = Depends(require_permission("reports:read")),
):
    defn = db.query(ReportDefinition).filter(ReportDefinition.id == definition_id).first()
    if not defn:
        raise HTTPException(status_code=404, detail="Report not found")
    run = ReportRun(
        report_definition_id=definition_id,
        user_id=current_user.id,
        params_json=None,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        status="completed",
        result_path=None,
    )
    db.add(run)
    db.commit()
    return {"status": "ok", "run_id": run.id, "message": "CSV export placeholder"}
