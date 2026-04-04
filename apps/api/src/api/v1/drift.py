# Drift: list findings, run drift check (NetBox vs live)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session
from src.core.rbac import require_permission
from src.models.user import User
from src.models import DriftFinding
from src.services.drift_service import run_drift_check

router = APIRouter(prefix="/drift", tags=["drift"])


class DriftFindingResponse(BaseModel):
    id: int
    resource_type: str
    resource_id: str
    drift_type: str | None
    field_name: str
    expected_value: str | None
    actual_value: str | None
    source_of_truth: str
    discovered_from: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[DriftFindingResponse])
def list_drift_findings(
    drift_type: str | None = Query(None),
    resource_type: str | None = Query(None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("drift:read")),
):
    q = db.query(DriftFinding).order_by(DriftFinding.created_at.desc())
    if drift_type:
        q = q.filter(DriftFinding.drift_type == drift_type)
    if resource_type:
        q = q.filter(DriftFinding.resource_type == resource_type)
    rows = q.limit(200).all()
    return [DriftFindingResponse(
        id=r.id,
        resource_type=r.resource_type,
        resource_id=r.resource_id,
        drift_type=r.drift_type,
        field_name=r.field_name,
        expected_value=r.expected_value,
        actual_value=r.actual_value,
        source_of_truth=r.source_of_truth,
        discovered_from=r.discovered_from,
        created_at=r.created_at.isoformat() if r.created_at else "",
    ) for r in rows]


@router.post("/run")
def run_drift(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("drift:write")),
):
    count = run_drift_check(db)
    return {"status": "ok", "findings_count": count}
