# Cloud Nexus Automation Runner
FROM python:3.12-alpine
WORKDIR /app
RUN adduser -D -u 1000 appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY runner.py .
USER appuser
CMD ["python", "runner.py"]
