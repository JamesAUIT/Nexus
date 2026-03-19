"""
Shared connector framework and interface contract for all integrations.
Implementations: NetBox, Proxmox, vSphere, VyOS, AD (and others) must implement
this interface for sync, health check, and credential handling.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SyncResult:
    """Result of a connector sync run."""
    success: bool
    message: str | None = None
    items_synced: int = 0
    error: str | None = None


class ConnectorConfig(ABC):
    """Base for connector-specific config (validated from decrypted JSON)."""
    pass


class ConnectorBase(ABC):
    """Interface contract for all connector implementations."""

    connector_type: str = ""

    @abstractmethod
    def get_config_model(self) -> type[ConnectorConfig]:
        """Return Pydantic model for this connector's config."""
        ...

    @abstractmethod
    def test_connectivity(self, config: dict[str, Any]) -> bool:
        """Test connection to the target system. Returns True if reachable."""
        ...

    @abstractmethod
    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        """
        Perform full sync from the target system into Cloud Nexus models.
        config: decrypted connector config dict.
        connector_id: id of the Connector record (for logging/associations).
        """
        ...

    def health_check(self, config: dict[str, Any]) -> tuple[bool, str | None]:
        """
        Optional: detailed health check. Default uses test_connectivity.
        Returns (healthy, error_message).
        """
        ok = self.test_connectivity(config)
        return ok, None if ok else "Connectivity test failed"
