# Celery app for Cloud Nexus (used by worker container)
from celery import Celery
from src.config import settings

app = Celery(
    "cloud_nexus",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
app.conf.task_default_queue = "cloud_nexus"
app.conf.task_routes = {"src.tasks.sync_tasks.*": {"queue": "cloud_nexus"}}
app.autodiscover_tasks(["src.tasks"], related_name="sync_tasks")
