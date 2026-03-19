# Certificate monitoring: list, scan, severity, dashboard widget
from fastapi import APIRouter, Depends, Query

from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import TLSCertificate
from src.services.tls_scan import scan_host

router = APIRouter(prefix="/certificates", tags=["certificates"])


class CertResponse(BaseModel):
    id: int
    hostname: str
    port: int
    subject: str | None
    issuer: str | None
    not_after: str | None
    days_until_expiry: int | None
    severity: str
    last_scan_at: str
    scan_error: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=dict)
def list_certificates(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    severity: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = db.query(TLSCertificate).order_by(TLSCertificate.not_after.asc())
    if severity:
        q = q.filter(TLSCertificate.severity == severity)
    total = q.count()
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = []
    for c in q.all():
        rows.append(CertResponse(
            id=c.id,
            hostname=c.hostname,
            port=c.port,
            subject=c.subject,
            issuer=c.issuer,
            not_after=c.not_after.isoformat() if c.not_after else None,
            days_until_expiry=c.days_until_expiry,
            severity=c.severity,
            last_scan_at=c.last_scan_at.isoformat() if c.last_scan_at else "",
            scan_error=c.scan_error,
        ))
    return {"data": rows, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.post("/scan")
def run_scan(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("connectors:read")),
    hostname: str = Query(...),
    port: int = Query(443),
):
    cert = scan_host(db, hostname, port)
    return {"id": cert.id, "hostname": cert.hostname, "port": cert.port, "severity": cert.severity, "days_until_expiry": cert.days_until_expiry}


@router.get("/widget")
def widget_expiring(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("dashboard:read")),
    limit: int = Query(10, ge=1, le=50),
):
    q = db.query(TLSCertificate).filter(TLSCertificate.severity.in_(["critical", "high", "medium"])).order_by(TLSCertificate.not_after.asc()).limit(limit)
    rows = [{"id": c.id, "hostname": c.hostname, "port": c.port, "severity": c.severity, "days_until_expiry": c.days_until_expiry} for c in q.all()]
    by_severity = {"critical": db.query(TLSCertificate).filter(TLSCertificate.severity == "critical").count(), "high": db.query(TLSCertificate).filter(TLSCertificate.severity == "high").count(), "medium": db.query(TLSCertificate).filter(TLSCertificate.severity == "medium").count()}
    return {"expiring": rows, "counts_by_severity": by_severity}
