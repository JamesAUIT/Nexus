# Sync jobs: manual trigger, list runs, history
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.deps import get_db_session, get_current_user
from src.core.rbac import require_permission
from src.models.user import User
from src.models import SyncJob, SyncJobRun
from src.schemas.sync_job import SyncJobResponse, SyncJobRunResponse
from src.tasks.sync_tasks import run_sync_job

router = APIRouter(prefix="/sync-jobs", tags=["sync-jobs"])


@router.get("", response_model=list[SyncJobResponse])
def list_sync_jobs(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("sync:read")),
):
    jobs = db.query(SyncJob).order_by(SyncJob.id).all()
    return jobs


@router.post("/{sync_job_id}/trigger")
def trigger_sync(
    sync_job_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("sync:write")),
):
    job = db.query(SyncJob).filter(SyncJob.id == sync_job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")
    run_sync_job.delay(sync_job_id)
    return {"status": "queued", "sync_job_id": sync_job_id}


@router.get("/{sync_job_id}/runs", response_model=list[SyncJobRunResponse])
def list_sync_job_runs(
    sync_job_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_permission("sync:read")),
):
    job = db.query(SyncJob).filter(SyncJob.id == sync_job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")
    runs = db.query(SyncJobRun).filter(SyncJobRun.sync_job_id == sync_job_id).order_by(SyncJobRun.started_at.desc()).limit(50).all()
    return runs
