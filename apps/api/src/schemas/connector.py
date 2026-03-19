from datetime import datetime
from pydantic import BaseModel


class ConnectorBase(BaseModel):
    type: str
    name: str
    base_url: str | None = None


class ConnectorCreate(ConnectorBase):
    config_plain: dict | None = None


class ConnectorResponse(ConnectorBase):
    id: int
    last_ok_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
