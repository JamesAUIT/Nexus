# Audit logging for sensitive actions
from typing import Any

from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog


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
