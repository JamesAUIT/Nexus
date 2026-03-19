# TODO: Live integration with NetBox API (sites, racks, devices, etc.)
from typing import Any

from pydantic import BaseModel

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult


class NetBoxConfig(ConnectorConfig, BaseModel):
    url: str
    token: str


class NetBoxConnector(ConnectorBase):
    connector_type = "netbox"

    def get_config_model(self) -> type[ConnectorConfig]:
        return NetBoxConfig

    def test_connectivity(self, config: dict[str, Any]) -> bool:
        # TODO: GET {url}/api/dcim/sites/ with Authorization: Token {token}
        return True

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        # TODO: Fetch sites, racks, devices from NetBox; upsert into Site, Rack, Host models
        return SyncResult(success=True, items_synced=0, message="Stub: sync not implemented")
