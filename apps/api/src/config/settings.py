# Cloud Nexus API - Configuration from environment
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

    # Optional SSO / LDAP (Phase 2)
    oidc_issuer_url: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_redirect_uri: str | None = None
    ldap_url: str | None = None
    ldap_base_dn: str | None = None
    ldap_bind_dn: str | None = None
    ldap_bind_password: str | None = None

    # Proxy
    trusted_proxy: bool = False


settings = Settings()
