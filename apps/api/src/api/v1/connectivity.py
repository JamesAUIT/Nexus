# Connectivity testing: ping, TCP, DNS; cached recent results
from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session
import json

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import ConnectivityResult
from src.services.connectivity import run_check

router = APIRouter(prefix="/connectivity", tags=["connectivity"])


@router.post("/check")
def run_connectivity_check(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    target: str = Query(...),
    check_type: str = Query(..., regex="^(ping|tcp|dns)$"),
    use_cache: bool = Query(True),
):
    rec = run_check(db, target, check_type, use_cache)
    return {"target": rec.target, "check_type": rec.check_type, "success": rec.success, "result": json.loads(rec.result_json) if rec.result_json else {}, "checked_at": rec.checked_at.isoformat() if rec.checked_at else ""}


@router.get("/recent")
def recent_results(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(ConnectivityResult).order_by(ConnectivityResult.checked_at.desc()).limit(limit)
    rows = [{"id": r.id, "target": r.target, "check_type": r.check_type, "success": r.success, "result": json.loads(r.result_json) if r.result_json else {}, "checked_at": r.checked_at.isoformat() if r.checked_at else ""} for r in q.all()]
    return {"data": rows}
