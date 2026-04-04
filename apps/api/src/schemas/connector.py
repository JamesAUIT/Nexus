from datetime import datetime
from pydantic import BaseModel


class ConnectorBase(BaseModel):
    type: str
    name: str
    base_url: str | None = None


class ConnectorCreate(ConnectorBase):
    config_plain: dict | None = None


class ConnectorCreateRequest(BaseModel):
    """Create connector with plaintext config (encrypted at rest)."""

    type: str
    name: str
    base_url: str | None = None
    config_plain: dict
    schedule_cron: str | None = "0 */6 * * *"
    create_sync_job: bool = True


class ConnectorResponse(ConnectorBase):
    id: int
    last_ok_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
