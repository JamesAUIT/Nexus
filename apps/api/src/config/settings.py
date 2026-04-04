# Cloud Nexus API - Configuration from environment
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://cloudnexus:changeme@localhost:5432/cloudnexus"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production-32-bytes-min"
    encryption_key: str = "change-me-32-bytes-for-aes256"

    # Admin seed
    admin_password: str = "changeme"
    demo_mode: bool = False
    seed_db: bool = False

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

    # CORS: comma-separated origins. Empty + not demo_mode = deny cross-origin (same-site / server-side only).
    cors_origins: str = ""

    # Rate limits (slowapi), e.g. "30/minute" for login
    auth_login_rate_limit: str = "30/minute"

    # Refuse startup if default secrets in production (set false for local only)
    production_refuse_insecure_defaults: bool = False

    # SMTP (ops requests send)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True

    # Report file output
    report_storage_dir: str = "/tmp/cloud-nexus-reports"

    # HAProxy push (SSH)
    haproxy_ssh_host: str | None = None
    haproxy_ssh_user: str | None = None
    haproxy_ssh_key_path: str | None = None
    haproxy_remote_config_path: str | None = None

    # Automation runner shared secret (runner -> API callback)
    automation_runner_secret: str | None = None

    # Optional SSO / LDAP
    oidc_issuer_url: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_redirect_uri: str | None = None
    ldap_url: str | None = None
    ldap_base_dn: str | None = None
    ldap_bind_dn: str | None = None
    ldap_bind_password: str | None = None
    # {username} is replaced after LDAP filter escaping (injection-safe).
    ldap_user_search_filter: str = "(sAMAccountName={username})"

    # Proxy
    trusted_proxy: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def strip_cors(cls, v: str | None) -> str:
        return (v or "").strip()


settings = Settings()
