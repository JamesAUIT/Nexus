# Cloud Nexus Celery Worker (uses API code for tasks)
# Build from repo root: docker compose build worker
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy API app (same code that defines tasks and connectors)
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "celery[redis]"

COPY apps/api .
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

CMD ["celery", "-A", "src.tasks.celery_app", "worker", "-l", "info"]
