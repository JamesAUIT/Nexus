"""CORS origin list from settings."""
from src.config import settings


def get_cors_origins() -> list[str]:
    raw = settings.cors_origins.strip()
    if not raw:
        if settings.demo_mode:
            return ["*"]
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]
