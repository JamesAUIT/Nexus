from datetime import datetime
from pydantic import BaseModel


class SyncJobBase(BaseModel):
    connector_id: int
    schedule_cron: str | None = None


class SyncJobCreate(SyncJobBase):
    pass


class SyncJobResponse(SyncJobBase):
    id: int
    last_run_at: datetime | None = None
    last_status: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncJobRunResponse(BaseModel):
    id: int
    sync_job_id: int
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    error_message: str | None = None
    retry_count: int

    class Config:
        from_attributes = True
