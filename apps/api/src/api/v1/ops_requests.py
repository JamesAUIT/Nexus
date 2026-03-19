# Operations Requests: datacenter entry, asset install/removal; forms, templates, preview, draft/send, audit
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.core.audit_middleware import log_audit, get_client_ip
from src.models.user import User
from src.models import OpsRequestTemplate, OpsRequest

router = APIRouter(prefix="/ops-requests", tags=["ops-requests"])


class CreateOpsRequestBody(BaseModel):
    template_id: int | None = None
    request_type: str
    form_data: dict
    recipient: str | None = None


@router.get("/templates")
def list_templates(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    rows = db.query(OpsRequestTemplate).order_by(OpsRequestTemplate.name).all()
    return {"data": [{"id": t.id, "name": t.name, "slug": t.slug, "request_type": t.request_type, "form_schema": t.form_schema} for t in rows]}


def _render_template(subject_t: str | None, body_t: str | None, form_data: dict) -> tuple[str, str]:
    subject = subject_t or "Operations Request"
    body = body_t or ""
    for k, v in form_data.items():
        subject = subject.replace("{{" + str(k) + "}}", str(v))
        body = body.replace("{{" + str(k) + "}}", str(v))
    return subject, body


@router.post("/preview")
def preview(
    body: CreateOpsRequestBody,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    template = None
    if body.template_id:
        template = db.query(OpsRequestTemplate).filter(OpsRequestTemplate.id == body.template_id).first()
    subject_t = template.subject_template if template else None
    body_t = template.body_template if template else None
    subject, body_html = _render_template(subject_t, body_t, body.form_data)
    return {"subject": subject, "body_html": body_html}


@router.post("")
def create_draft(
    body: CreateOpsRequestBody,
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    template = None
    if body.template_id:
        template = db.query(OpsRequestTemplate).filter(OpsRequestTemplate.id == body.template_id).first()
    subject_t = template.subject_template if template else None
    body_t = template.body_template if template else None
    subject, body_html = _render_template(subject_t, body_t, body.form_data)
    now = datetime.now(timezone.utc)
    rec = OpsRequest(
        template_id=body.template_id,
        request_type=body.request_type,
        status="draft",
        subject=subject,
        body_html=body_html,
        form_data=json.dumps(body.form_data),
        recipient=body.recipient,
        created_by=current_user.id,
        created_at=now,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    log_audit(db, current_user.id, "ops_request_draft", "ops_request", str(rec.id), details=body.request_type, ip=get_client_ip(request))
    return {"id": rec.id, "status": "draft"}


@router.post("/{request_id}/send")
def send_request(
    request_id: int,
    req: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
):
    rec = db.query(OpsRequest).filter(OpsRequest.id == request_id).first()
    if not rec:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Request not found")
    if rec.status != "draft":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Only draft can be sent")
    now = datetime.now(timezone.utc)
    rec.status = "sent"
    rec.sent_at = now
    db.commit()
    log_audit(db, current_user.id, "ops_request_sent", "ops_request", str(request_id), details=rec.request_type, ip=get_client_ip(req))
    return {"id": rec.id, "status": "sent", "sent_at": now.isoformat()}


@router.get("")
def list_requests(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = db.query(OpsRequest).order_by(OpsRequest.created_at.desc())
    if status:
        q = q.filter(OpsRequest.status == status)
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = [{"id": r.id, "request_type": r.request_type, "status": r.status, "subject": r.subject, "recipient": r.recipient, "created_at": r.created_at.isoformat() if r.created_at else "", "sent_at": r.sent_at.isoformat() if r.sent_at else None} for r in q.all()]
    return {"data": rows, "meta": {"page": page, "page_size": page_size, "total": total}}
