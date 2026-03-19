# Audit logging middleware: auth events, sync events, privileged actions
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str | None:
    if request.client:
        return str(request.client.host)
    return request.headers.get("x-forwarded-for", "").split(",")[0].strip() or None


def log_audit_sync(db: Session, sync_job_id: int, status: str, details: str | None = None) -> None:
    entry = AuditLog(
        user_id=None,
        action="sync_run",
        resource_type="sync_job",
        resource_id=str(sync_job_id),
        details=details,
        ip=None,
    )
    db.add(entry)
    db.commit()


class AuditMiddleware(BaseHTTPMiddleware):
    """Log authentication and privileged API actions to audit_logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        if response.status_code >= 400:
            return response
        path = request.scope.get("path", "")
        method = request.scope.get("method", "")
        # Log privileged mutations (POST/PUT/DELETE on sensitive paths). Login is logged in auth route with user_id.
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            if "/sync-jobs/" in path and "trigger" in path:
                db = SessionLocal()
                try:
                    sync_job_id = path.split("/")[-2] if path.endswith("/trigger") else None
                    if sync_job_id and sync_job_id.isdigit():
                        entry = AuditLog(
                            user_id=None,
                            action="sync_trigger",
                            resource_type="sync_job",
                            resource_id=sync_job_id,
                            details=None,
                            ip=get_client_ip(request),
                        )
                        db.add(entry)
                        db.commit()
                except Exception as e:
                    logger.warning("Audit log failed: %s", e)
                finally:
                    db.close()
        return response


def log_audit(
    db: Session,
    user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: str | None = None,
    ip: str | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip=ip,
    )
    db.add(entry)
    db.commit()
