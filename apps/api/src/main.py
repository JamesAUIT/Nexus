import json
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from src.api.v1 import api_router
from src.config import settings
from src.core.audit_middleware import AuditMiddleware
from src.core.cors_util import get_cors_origins
from src.core.limiter import limiter
from src.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.log_json:

        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                payload = {
                    "severity": record.levelname,
                    "message": record.getMessage(),
                    "logger": record.name,
                }
                if record.exc_info:
                    payload["exc_info"] = self.formatException(record.exc_info)
                return json.dumps(payload)

        root = logging.getLogger()
        root.handlers.clear()
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(JsonFormatter())
        root.addHandler(h)
        root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    else:
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    if settings.production_refuse_insecure_defaults:
        if "change-me" in settings.secret_key or "change-me" in settings.encryption_key:
            raise RuntimeError(
                "Insecure default SECRET_KEY or ENCRYPTION_KEY: set production secrets or disable PRODUCTION_REFUSE_INSECURE_DEFAULTS"
            )
    yield


app = FastAPI(
    title="Cloud Nexus API",
    description="Central control plane for cloud/datacentre operations",
    version="0.2.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if settings.trusted_proxy:
    try:
        from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

        app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    except ImportError:
        pass

app.add_middleware(AuditMiddleware)
_origins = get_cors_origins()
_allow_credentials = bool(_origins) and "*" not in _origins
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    """Readiness: DB connectivity check."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        return JSONResponse(
            content={"status": "unhealthy", "detail": str(e)},
            status_code=503,
        )
    return {"status": "ok"}
