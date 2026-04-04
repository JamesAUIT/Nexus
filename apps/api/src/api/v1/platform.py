# Read-only platform configuration for operators (no secrets).
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.config import settings
from src.core.cors_util import get_cors_origins
from src.core.rbac import require_permission
from src.models.user import User

router = APIRouter(prefix="/platform", tags=["platform"])


class PlatformSettingsResponse(BaseModel):
    api_version: str
    demo_mode: bool
    cors_origins: list[str]
    cors_enabled: bool
    trusted_proxy: bool
    log_json: bool
    production_refuse_insecure_defaults: bool
    auth_login_rate_limit: str
    report_storage_dir: str
    oidc_configured: bool
    ldap_configured: bool
    smtp_configured: bool
    haproxy_ssh_configured: bool
    automation_runner_configured: bool


@router.get("/settings", response_model=PlatformSettingsResponse)
def get_platform_settings(
    current_user: User = Depends(require_permission("connectors:read")),
):
    origins = get_cors_origins()
    return PlatformSettingsResponse(
        api_version="0.2.0",
        demo_mode=settings.demo_mode,
        cors_origins=origins,
        cors_enabled=len(origins) > 0,
        trusted_proxy=settings.trusted_proxy,
        log_json=settings.log_json,
        production_refuse_insecure_defaults=settings.production_refuse_insecure_defaults,
        auth_login_rate_limit=settings.auth_login_rate_limit,
        report_storage_dir=settings.report_storage_dir,
        oidc_configured=bool(settings.oidc_issuer_url and settings.oidc_client_id),
        ldap_configured=bool(
            settings.ldap_url
            and settings.ldap_base_dn
            and settings.ldap_bind_dn
            and settings.ldap_bind_password
        ),
        smtp_configured=bool(settings.smtp_host),
        haproxy_ssh_configured=bool(settings.haproxy_ssh_host and settings.haproxy_remote_config_path),
        automation_runner_configured=bool(settings.automation_runner_secret),
    )
