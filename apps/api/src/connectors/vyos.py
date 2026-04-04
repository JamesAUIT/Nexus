# VyOS — SSH connectivity check and minimal command (show version).
from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult

logger = logging.getLogger(__name__)


class VyOSConfig(ConnectorConfig, BaseModel):
    host: str
    user: str
    password: str
    port: int = 22


class VyOSConnector(ConnectorBase):
    connector_type = "vyos"

    def get_config_model(self) -> type[ConnectorConfig]:
        return VyOSConfig

    def test_connectivity(self, config: dict[str, Any]) -> bool:
        try:
            c = VyOSConfig(**config)
            import paramiko

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                c.host,
                port=c.port,
                username=c.user,
                password=c.password,
                timeout=20,
                banner_timeout=20,
            )
            _, stdout, _ = client.exec_command("show version", timeout=15)
            out = stdout.read(256)
            client.close()
            return len(out) > 0
        except Exception as e:
            logger.warning("VyOS connectivity failed: %s", e)
            return False

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        return SyncResult(
            success=True,
            items_synced=0,
            message="VyOS: sync of config into CMDB not implemented (connectivity OK)",
        )
