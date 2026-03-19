"""TLS certificate scanning: connect and extract expiry, compute severity."""
import ssl
import socket
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.models import TLSCertificate


def _days_until_expiry(not_after: datetime) -> int:
    now = datetime.now(not_after.tzinfo or timezone.utc)
    if not_after.tzinfo is None:
        not_after = not_after.replace(tzinfo=timezone.utc)
    return max(0, (not_after - now).days)


def _severity(days: int) -> str:
    if days <= 0:
        return "critical"
    if days <= 7:
        return "high"
    if days <= 30:
        return "medium"
    return "ok"


def scan_host(db: Session, hostname: str, port: int = 443) -> TLSCertificate | None:
    now = datetime.now(timezone.utc)
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
        # cert is dict with 'notAfter', 'notBefore', 'subject', 'issuer'
        not_after_str = cert.get("notAfter")
        not_before_str = cert.get("notBefore")
        from datetime import datetime as dt
        not_after = dt.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc) if not_after_str else now
        not_before = dt.strptime(not_before_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc) if not_before_str else now
        subject = str(cert.get("subject", []))
        issuer = str(cert.get("issuer", []))
        days = _days_until_expiry(not_after)
        severity = _severity(days)
    except Exception as e:
        # Upsert with error
        existing = db.query(TLSCertificate).filter(TLSCertificate.hostname == hostname, TLSCertificate.port == port).first()
        if existing:
            existing.last_scan_at = now
            existing.scan_error = str(e)[:512]
            db.commit()
            return existing
        rec = TLSCertificate(
            hostname=hostname,
            port=port,
            not_after=now,
            days_until_expiry=0,
            severity="critical",
            last_scan_at=now,
            scan_error=str(e)[:512],
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    existing = db.query(TLSCertificate).filter(TLSCertificate.hostname == hostname, TLSCertificate.port == port).first()
    if existing:
        existing.subject = subject[:512]
        existing.issuer = issuer[:512]
        existing.not_before = not_before
        existing.not_after = not_after
        existing.days_until_expiry = days
        existing.severity = severity
        existing.last_scan_at = now
        existing.scan_error = None
        db.commit()
        db.refresh(existing)
        return existing
    rec = TLSCertificate(
        hostname=hostname,
        port=port,
        subject=subject[:512],
        issuer=issuer[:512],
        not_before=not_before,
        not_after=not_after,
        days_until_expiry=days,
        severity=severity,
        last_scan_at=now,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
