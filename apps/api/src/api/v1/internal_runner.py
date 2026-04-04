# Internal: automation runner (shared secret only — not for browser use)
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_db_session
from src.config import settings
from src.models import ScriptDefinition

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/scripts/{definition_id}/manifest")
def runner_script_manifest(
    definition_id: int,
    x_automation_secret: str | None = Header(None, alias="X-Automation-Secret"),
    db: Session = Depends(get_db_session),
):
    if not settings.automation_runner_secret or x_automation_secret != settings.automation_runner_secret:
        raise HTTPException(status_code=401, detail="Invalid automation secret")
    d = db.query(ScriptDefinition).filter(ScriptDefinition.id == definition_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Script not found")
    return {
        "id": d.id,
        "slug": d.slug,
        "script_type": d.script_type,
        "timeout_seconds": d.timeout_seconds or 300,
        "approved_only": d.approved_only,
    }
