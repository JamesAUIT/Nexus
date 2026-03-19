# TODO: Live integration with VyOS (SSH/API)
from typing import Any

from pydantic import BaseModel

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult


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
        # TODO: SSH or REST API connectivity test
        return True

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        # TODO: Pull config/state; store in appropriate models or drift
        return SyncResult(success=True, items_synced=0, message="Stub: sync not implemented")
