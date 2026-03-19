# TODO: Live integration with Proxmox VE API (clusters, nodes, VMs, storage, etc.)
from typing import Any

from pydantic import BaseModel

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult


class ProxmoxConfig(ConnectorConfig, BaseModel):
    url: str
    user: str
    password: str
    verify_ssl: bool = True


class ProxmoxConnector(ConnectorBase):
    connector_type = "proxmox"

    def get_config_model(self) -> type[ConnectorConfig]:
        return ProxmoxConfig

    def test_connectivity(self, config: dict[str, Any]) -> bool:
        # TODO: Login to Proxmox API, GET /api2/json/cluster/resources
        return True

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        # TODO: Fetch clusters, nodes, VMs, storage; upsert Cluster, Host, VirtualMachine, Datastore
        return SyncResult(success=True, items_synced=0, message="Stub: sync not implemented")
