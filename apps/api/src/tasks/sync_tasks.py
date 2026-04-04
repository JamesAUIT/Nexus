# Scheduled and manual sync jobs: run connector sync, record history, retries, failure logging
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.tasks.celery_app import app

from src.config import settings
from src.models import Connector, SyncJob, SyncJobRun
from src.core.connector_credentials import load_connector_credentials
from src.connectors.registry import get_connector

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@app.task(bind=True, max_retries=3)
def run_sync_job(self, sync_job_id: int) -> dict[str, Any]:
    """
    Run a single sync job: load connector, decrypt config, run sync, record SyncJobRun.
    On failure: log error, create SyncJobRun with status=failed, retry with backoff.
    """
    db = SessionLocal()
    try:
        sync_job = db.query(SyncJob).filter(SyncJob.id == sync_job_id).first()
        if not sync_job:
            return {"success": False, "error": "SyncJob not found"}
        connector = db.query(Connector).filter(Connector.id == sync_job.connector_id).first()
        if not connector:
            return {"success": False, "error": "Connector not found"}

        impl = get_connector(connector.type)
        if not impl:
            return {"success": False, "error": f"Unknown connector type: {connector.type}"}

        config = load_connector_credentials(connector.encrypted_config)
        if not config:
            return {"success": False, "error": "Failed to decrypt connector config"}

        run = SyncJobRun(
            sync_job_id=sync_job_id,
            started_at=datetime.utcnow(),
            status="running",
            retry_count=self.request.retries,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            result = impl.sync(config, connector.id)
            run.finished_at = datetime.utcnow()
            run.status = "success" if result.success else "failed"
            run.error_message = result.error or result.message
            db.commit()

            sync_job.last_run_at = run.finished_at
            sync_job.last_status = run.status
            if result.success:
                connector.last_ok_at = run.finished_at
                connector.last_error = None
            else:
                connector.last_error = result.error or result.message
            db.commit()

            if not result.success and self.request.retries < self.max_retries:
                raise self.retry(countdown=60 * (self.request.retries + 1))
            return {"success": result.success, "message": result.message, "items_synced": result.items_synced}
        except Exception as e:
            logger.exception("Sync job %s failed: %s", sync_job_id, e)
            run.finished_at = datetime.utcnow()
            run.status = "failed"
            run.error_message = str(e)[:2048]
            db.commit()
            sync_job.last_run_at = run.finished_at
            sync_job.last_status = "failed"
            connector.last_error = str(e)[:1024]
            db.commit()
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
    finally:
        db.close()


def run_sync_job_sync(sync_job_id: int) -> dict[str, Any]:
    """Synchronous helper for manual trigger (e.g. from API)."""
    return run_sync_job.apply(args=(sync_job_id,)).get()
