# AES-256-GCM for connector secret encryption at rest
import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.config import settings


def _key_bytes() -> bytes:
    raw = settings.encryption_key
    if len(raw) == 44 and raw.endswith("="):
        return base64.b64decode(raw)
    if len(raw) == 64 and all(c in "0123456789abcdef" for c in raw.lower()):
        return bytes.fromhex(raw)
    return raw.encode("utf-8")[:32].ljust(32, b"\0")


def encrypt_connector_config(plain: str) -> str:
    key = _key_bytes()
    if len(key) != 32:
        key = key[:32].ljust(32, b"\0")
    nonce = os.urandom(12)
    aes = AESGCM(key)
    ct = aes.encrypt(nonce, plain.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_connector_config(cipher: str) -> Optional[str]:
    try:
        key = _key_bytes()
        if len(key) != 32:
            key = key[:32].ljust(32, b"\0")
        raw = base64.b64decode(cipher)
        nonce, ct = raw[:12], raw[12:]
        aes = AESGCM(key)
        return aes.decrypt(nonce, ct, None).decode("utf-8")
    except Exception:
        return None
