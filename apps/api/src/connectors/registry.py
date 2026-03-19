"""Registry of connector implementations by type."""
from typing import Type

from src.connectors.base import ConnectorBase
from src.connectors.netbox import NetBoxConnector
from src.connectors.proxmox import ProxmoxConnector
from src.connectors.vsphere import VSphereConnector
from src.connectors.vyos import VyOSConnector
from src.connectors.ad import ADConnector

_REGISTRY: dict[str, ConnectorBase] = {
    "netbox": NetBoxConnector(),
    "proxmox": ProxmoxConnector(),
    "vsphere": VSphereConnector(),
    "vyos": VyOSConnector(),
    "ad": ADConnector(),
}


def get_connector(connector_type: str) -> ConnectorBase | None:
    return _REGISTRY.get(connector_type)


def get_connector_class(connector_type: str) -> Type[ConnectorBase] | None:
    impl = _REGISTRY.get(connector_type)
    return type(impl) if impl else None
