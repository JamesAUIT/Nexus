"""
Connector credential storage: encrypt at rest (AES-256-GCM), decrypt only when needed.
Never log or return decrypted config to API responses.
"""
import json
from typing import Any

from src.core.encryption import decrypt_connector_config, encrypt_connector_config


def store_connector_credentials(plain_config: dict[str, Any]) -> str:
    """Encrypt connector config (e.g. tokens, passwords) for DB storage."""
    return encrypt_connector_config(json.dumps(plain_config))


def load_connector_credentials(encrypted_config: str | None) -> dict[str, Any] | None:
    """Decrypt connector config for use by connector sync/test. Returns None if invalid."""
    if not encrypted_config:
        return None
    raw = decrypt_connector_config(encrypted_config)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
