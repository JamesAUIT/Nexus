# Cloud Nexus - Celery app (Redis broker)
from celery import Celery
import os

broker = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
app = Celery("cloud_nexus", broker=broker, backend=broker)
app.conf.task_default_queue = "cloud_nexus"
app.autodiscover_tasks([])
