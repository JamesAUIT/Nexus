# Active Directory — LDAP bind and search (ldap3).
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult

logger = logging.getLogger(__name__)


class ADConfig(ConnectorConfig, BaseModel):
    url: str
    bind_dn: str
    bind_password: str
    base_dn: str
    user_search_filter: str | None = None


class ADConnector(ConnectorBase):
    connector_type = "ad"

    def get_config_model(self) -> type[ConnectorConfig]:
        return ADConfig

    def test_connectivity(self, config: dict[str, Any]) -> bool:
        try:
            c = ADConfig(**config)
            from ldap3 import ALL, Connection, Server

            parsed = urlparse(c.url if "://" in c.url else f"ldap://{c.url}")
            host = parsed.hostname or c.url.replace("ldap://", "").replace("ldaps://", "").split(":")[0]
            port = parsed.port or (636 if parsed.scheme == "ldaps" else 389)
            use_ssl = parsed.scheme == "ldaps"
            server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL)
            conn = Connection(server, user=c.bind_dn, password=c.bind_password, auto_bind=True)
            ok = conn.search(c.base_dn, "(objectClass=*)", size_limit=1)
            conn.unbind()
            return bool(ok)
        except Exception as e:
            logger.warning("AD/LDAP connectivity failed: %s", e)
            return False

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        return SyncResult(
            success=True,
            items_synced=0,
            message="AD: user/group sync to RBAC not implemented (bind OK)",
        )
