# RBAC: permission constants and dependency for protected endpoints
import json
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.models.user import User

# Permission format: resource:action e.g. sites:read, connectors:write
PERMISSIONS = [
    "dashboard:read",
    "sites:read", "sites:write",
    "hosts:read", "hosts:write",
    "vms:read", "vms:write",
    "connectors:read", "connectors:write",
    "audit:read",
    "settings:read", "settings:write",
    "reports:read",
    "runbooks:read", "runbooks:write",
    "scripts:read", "scripts:write", "scripts:execute",
    "sync:read", "sync:write",
    "drift:read", "drift:write",
]


def get_user_permissions(user: User) -> set[str]:
    if not user.role:
        return set()
    try:
        perms = json.loads(user.role.permissions or "[]")
        return set(perms) if isinstance(perms, list) else set()
    except (json.JSONDecodeError, TypeError):
        return set()


def require_permission(permission: str):
    def _check(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.disabled_at:
            raise HTTPException(status_code=403, detail="Account disabled")
        perms = get_user_permissions(current_user)
        if permission not in perms and "admin:all" not in perms:
            raise HTTPException(status_code=403, detail="Insufficient permission")
        return current_user
    return _check
