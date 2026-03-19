# Script Library: definitions, parameter forms, RBAC gating, execution history, audit
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission, get_user_permissions
from src.core.audit_middleware import log_audit, get_client_ip
from src.models.user import User
from src.models import ScriptDefinition, ScriptExecution

router = APIRouter(prefix="/scripts", tags=["scripts"])


class ScriptDefResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    script_type: str
    approved_only: bool
    timeout_seconds: int | None
    parameters_schema: str | None
    required_permission: str | None

    class Config:
        from_attributes = True


def _can_run_script(user: User, definition: ScriptDefinition) -> bool:
    perm = definition.required_permission or "scripts:execute"
    perms = get_user_permissions(user)
    return "admin:all" in perms or perm in perms


@router.get("/definitions", response_model=dict)
def list_definitions(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("scripts:read")),
):
    rows = db.query(ScriptDefinition).order_by(ScriptDefinition.name).all()
    out = []
    for r in rows:
        out.append({
            **ScriptDefResponse(id=r.id, name=r.name, slug=r.slug, description=r.description, script_type=r.script_type, approved_only=r.approved_only, timeout_seconds=r.timeout_seconds, parameters_schema=r.parameters_schema, required_permission=r.required_permission).model_dump(),
            "can_execute": _can_run_script(current_user, r),
        })
    return {"data": out}


@router.get("/definitions/{definition_id}")
def get_definition(
    definition_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("scripts:read")),
):
    r = db.query(ScriptDefinition).filter(ScriptDefinition.id == definition_id).first()
    if not r:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Script not found")
    return {
        **ScriptDefResponse(id=r.id, name=r.name, slug=r.slug, description=r.description, script_type=r.script_type, approved_only=r.approved_only, timeout_seconds=r.timeout_seconds, parameters_schema=r.parameters_schema, required_permission=r.required_permission).model_dump(),
        "can_execute": _can_run_script(current_user, r),
    }


class ExecuteBody(BaseModel):
    parameters: dict | None = None


@router.post("/definitions/{definition_id}/execute")
def execute_script(
    definition_id: int,
    request: Request,
    body: ExecuteBody,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    definition = db.query(ScriptDefinition).filter(ScriptDefinition.id == definition_id).first()
    if not definition:
        raise HTTPException(status_code=404, detail="Script not found")
    if not _can_run_script(current_user, definition):
        raise HTTPException(status_code=403, detail="Insufficient permission to run this script")
    now = datetime.now(timezone.utc)
    execution = ScriptExecution(
        script_definition_id=definition_id,
        user_id=current_user.id,
        started_at=now,
        status="completed",
        stdout="(Execution recorded; no runner connected)",
        stderr=None,
        timeout_seconds=definition.timeout_seconds,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    log_audit(db, current_user.id, "script_execute", "script_definition", str(definition_id), details=f"slug={definition.slug}", ip=get_client_ip(request))
    return {"execution_id": execution.id, "status": execution.status}


@router.get("/executions", response_model=dict)
def list_executions(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("scripts:read")),
    script_definition_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = db.query(ScriptExecution).order_by(ScriptExecution.started_at.desc())
    if script_definition_id is not None:
        q = q.filter(ScriptExecution.script_definition_id == script_definition_id)
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = [{"id": e.id, "script_definition_id": e.script_definition_id, "started_at": e.started_at.isoformat() if e.started_at else "", "finished_at": e.finished_at.isoformat() if e.finished_at else None, "status": e.status, "stdout": e.stdout, "stderr": e.stderr} for e in q.all()]
    return {"data": rows, "meta": {"page": page, "page_size": page_size, "total": total}}
