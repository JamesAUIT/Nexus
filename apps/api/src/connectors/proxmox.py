# Proxmox VE API — ticket auth, cluster resources; upserts Cluster, Host, VirtualMachine.
from __future__ import annotations

import logging
from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult
from src.db.session import SessionLocal
from src.models import Cluster, Connector, Datastore, Host, VirtualMachine

logger = logging.getLogger(__name__)


class ProxmoxConfig(ConnectorConfig, BaseModel):
    """url: e.g. https://pve.example.com:8006 — no trailing path."""

    url: str
    user: str
    password: str
    verify_ssl: bool = True

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return v.rstrip("/")


def _proxmox_username(cfg: ProxmoxConfig) -> str:
    u = cfg.user.strip()
    if "@" in u:
        return u
    return f"{u}@pam"


def _ticket(client: httpx.Client, cfg: ProxmoxConfig) -> str:
    r = client.post(
        "/api2/json/access/ticket",
        data={
            "username": _proxmox_username(cfg),
            "password": cfg.password,
        },
    )
    r.raise_for_status()
    data = r.json().get("data") or {}
    ticket = data.get("ticket")
    if not ticket:
        raise RuntimeError("Proxmox: no ticket in response")
    return ticket


class ProxmoxConnector(ConnectorBase):
    connector_type = "proxmox"

    def get_config_model(self) -> type[ConnectorConfig]:
        return ProxmoxConfig

    def test_connectivity(self, config: dict[str, Any]) -> bool:
        try:
            c = ProxmoxConfig(**config)
            with httpx.Client(base_url=c.url, timeout=25.0, verify=c.verify_ssl) as client:
                ticket = _ticket(client, c)
                r = client.get(
                    "/api2/json/cluster/resources",
                    cookies={"PVEAuthCookie": ticket},
                    params={"type": "node", "limit": 1},
                )
                return r.status_code == 200
        except Exception as e:
            logger.warning("Proxmox connectivity check failed: %s", e)
            return False

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        try:
            c = ProxmoxConfig(**config)
        except Exception as e:
            return SyncResult(success=False, error=str(e), message=str(e))

        db = SessionLocal()
        items = 0
        try:
            conn = db.query(Connector).filter(Connector.id == connector_id).first()
            if not conn:
                return SyncResult(success=False, error="Connector not found", message="Connector not found")

            ext = f"proxmox-conn-{connector_id}"
            cluster = db.query(Cluster).filter(Cluster.external_id == ext).first()
            if not cluster:
                cluster = Cluster(
                    site_id=None,
                    name=conn.name,
                    type="proxmox",
                    external_id=ext,
                )
                db.add(cluster)
                db.flush()
            else:
                cluster.name = conn.name

            with httpx.Client(base_url=c.url, timeout=120.0, verify=c.verify_ssl) as client:
                ticket = _ticket(client, c)
                cookies = {"PVEAuthCookie": ticket}
                r = client.get("/api2/json/cluster/resources", cookies=cookies)
                r.raise_for_status()
                rows = r.json().get("data") or []

            for row in rows:
                if row.get("type") != "node":
                    continue
                name = row.get("name") or ""
                if not name:
                    continue
                h = (
                    db.query(Host)
                    .filter(Host.cluster_id == cluster.id, Host.name == name)
                    .first()
                )
                if h:
                    h.type = "hypervisor"
                else:
                    db.add(
                        Host(
                            cluster_id=cluster.id,
                            site_id=None,
                            name=name,
                            type="hypervisor",
                            external_id=f"node-{name}",
                        )
                    )
                items += 1
            db.flush()
            node_to_host: dict[str, int] = {}
            for h in db.query(Host).filter(Host.cluster_id == cluster.id).all():
                node_to_host[h.name] = h.id

            for row in rows:
                rtype = row.get("type")
                if rtype in ("qemu", "lxc"):
                    vmid = row.get("vmid")
                    node = row.get("node") or ""
                    vmname = row.get("name") or str(vmid)
                    if vmid is None:
                        continue
                    ext_id = f"{node}-{vmid}"
                    hid = node_to_host.get(node)
                    vm = (
                        db.query(VirtualMachine)
                        .filter(
                            VirtualMachine.cluster_id == cluster.id,
                            VirtualMachine.external_id == ext_id,
                        )
                        .first()
                    )
                    status = row.get("status") or row.get("state")
                    if vm:
                        vm.name = vmname
                        vm.power_state = str(status) if status else vm.power_state
                        if hid:
                            vm.host_id = hid
                    else:
                        db.add(
                            VirtualMachine(
                                host_id=hid,
                                cluster_id=cluster.id,
                                name=vmname,
                                external_id=ext_id,
                                power_state=str(status) if status else None,
                            )
                        )
                    items += 1
                elif rtype == "storage":
                    stid = row.get("id") or row.get("storage")
                    stname = str(row.get("storage") or row.get("name") or stid or "storage")
                    if not stid:
                        continue
                    ext_ds = f"pve-{stid}"
                    ds = (
                        db.query(Datastore)
                        .filter(
                            Datastore.cluster_id == cluster.id,
                            Datastore.external_id == ext_ds,
                        )
                        .first()
                    )
                    if ds:
                        ds.name = stname
                    else:
                        db.add(
                            Datastore(
                                cluster_id=cluster.id,
                                host_id=None,
                                name=stname,
                                type="proxmox",
                                external_id=ext_ds,
                            )
                        )
                    items += 1

            db.commit()
            return SyncResult(
                success=True,
                items_synced=items,
                message=f"Synced {items} Proxmox resource row(s)",
            )
        except Exception as e:
            logger.exception("Proxmox sync failed")
            db.rollback()
            return SyncResult(success=False, error=str(e)[:2048], message=str(e)[:2048])
        finally:
            db.close()
