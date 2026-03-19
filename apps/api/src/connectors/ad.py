# TODO: Live integration with Active Directory (LDAP/LDAPS)
from typing import Any

from pydantic import BaseModel

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult


class ADConfig(ConnectorConfig, BaseModel):
    url: str  # ldaps://dc.example.com
    bind_dn: str
    bind_password: str
    base_dn: str
    user_search_filter: str | None = None


class ADConnector(ConnectorBase):
    connector_type = "ad"

    def get_config_model(self) -> type[ConnectorConfig]:
        return ADConfig

    def test_connectivity(self, config: dict[str, Any]) -> bool:
        # TODO: LDAP bind and simple search
        return True

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        # TODO: Sync users/groups for AD group → role mapping
        return SyncResult(success=True, items_synced=0, message="Stub: sync not implemented")
