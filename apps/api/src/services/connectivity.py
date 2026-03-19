"""Connectivity testing: ping, TCP port, DNS. Cached results."""
import socket
import subprocess
import platform
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from src.models import ConnectivityResult

CACHE_SECONDS = 300  # 5 min


def _run_ping(target: str) -> tuple[bool, str]:
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        cmd = ["ping", param, "1", target]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.returncode == 0, r.stdout or r.stderr or ""
    except Exception as e:
        return False, str(e)


def _run_tcp(host: str, port: int) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=5) as _:
            return True, "open"
    except Exception as e:
        return False, str(e)


def _run_dns(name: str) -> tuple[bool, str]:
    try:
        socket.gethostbyname(name)
        return True, "resolved"
    except Exception as e:
        return False, str(e)


def run_check(db: Session, target: str, check_type: str, use_cache: bool = True) -> ConnectivityResult:
    now = datetime.now(timezone.utc)
    if use_cache:
        cutoff = now - timedelta(seconds=CACHE_SECONDS)
        existing = db.query(ConnectivityResult).filter(
            ConnectivityResult.target == target,
            ConnectivityResult.check_type == check_type,
            ConnectivityResult.checked_at >= cutoff,
        ).order_by(ConnectivityResult.checked_at.desc()).first()
        if existing:
            return existing

    if check_type == "ping":
        success, detail = _run_ping(target)
    elif check_type == "tcp":
        parts = target.rsplit(":", 1)
        host = parts[0]
        port = int(parts[1]) if len(parts) == 2 else 80
        success, detail = _run_tcp(host, port)
    elif check_type == "dns":
        success, detail = _run_dns(target)
    else:
        success, detail = False, "unknown check_type"

    import json
    rec = ConnectivityResult(target=target, check_type=check_type, success=success, result_json=json.dumps({"detail": detail}), checked_at=now)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
