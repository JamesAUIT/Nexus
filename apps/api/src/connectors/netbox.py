# NetBox REST API — sites, racks, devices (dcim).
from __future__ import annotations

import logging
from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult
from src.db.session import SessionLocal
from src.models import Host, Rack, Site

logger = logging.getLogger(__name__)


class NetBoxConfig(ConnectorConfig, BaseModel):
    url: str
    token: str
    verify_ssl: bool = True

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return v.rstrip("/")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Token {token}"}


def _paginate(client: httpx.Client, start_url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    next_url: str | None = start_url
    while next_url:
        r = client.get(next_url, headers=headers)
        r.raise_for_status()
        payload = r.json()
        out.extend(payload.get("results", []))
        next_url = payload.get("next")
    return out


class NetBoxConnector(ConnectorBase):
    connector_type = "netbox"

    def get_config_model(self) -> type[ConnectorConfig]:
        return NetBoxConfig

    def test_connectivity(self, config: dict[str, Any]) -> bool:
        try:
            c = NetBoxConfig(**config)
            with httpx.Client(timeout=20.0, verify=c.verify_ssl) as client:
                r = client.get(
                    f"{c.url}/api/dcim/sites/",
                    headers=_headers(c.token),
                    params={"limit": 1},
                )
                return r.status_code == 200
        except Exception as e:
            logger.warning("NetBox connectivity check failed: %s", e)
            return False

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        try:
            c = NetBoxConfig(**config)
        except Exception as e:
            return SyncResult(success=False, error=str(e), message=str(e))

        db = SessionLocal()
        items = 0
        try:
            with httpx.Client(timeout=180.0, verify=c.verify_ssl) as client:
                headers = _headers(c.token)
                sites = _paginate(client, f"{c.url}/api/dcim/sites/", headers)
                for site in sites:
                    nb_id = int(site["id"])
                    name = str(site["name"])
                    slug = str(site["slug"])
                    row = db.query(Site).filter(Site.netbox_site_id == nb_id).first()
                    if not row:
                        row = db.query(Site).filter(Site.slug == slug).first()
                    if row:
                        row.name = name
                        row.slug = slug
                        row.netbox_site_id = nb_id
                    else:
                        db.add(Site(name=name, slug=slug, netbox_site_id=nb_id))
                    items += 1
                db.flush()

                racks = _paginate(client, f"{c.url}/api/dcim/racks/", headers)
                for rack in racks:
                    site_ref = rack.get("site")
                    site_nb = int(site_ref["id"]) if isinstance(site_ref, dict) else int(site_ref)
                    site_row = db.query(Site).filter(Site.netbox_site_id == site_nb).first()
                    if not site_row:
                        continue
                    rid = int(rack["id"])
                    rname = str(rack["name"])
                    row = db.query(Rack).filter(Rack.netbox_rack_id == rid).first()
                    if row:
                        row.name = rname
                        row.site_id = site_row.id
                    else:
                        db.add(Rack(site_id=site_row.id, name=rname, netbox_rack_id=rid))
                    items += 1
                db.flush()

                devices = _paginate(client, f"{c.url}/api/dcim/devices/", headers)
                for dev in devices:
                    site_ref = dev.get("site")
                    if not site_ref:
                        continue
                    site_nb = int(site_ref["id"]) if isinstance(site_ref, dict) else int(site_ref)
                    site_row = db.query(Site).filter(Site.netbox_site_id == site_nb).first()
                    if not site_row:
                        continue
                    did = int(dev["id"])
                    dname = str(dev.get("name") or f"device-{did}")
                    ext = f"nb-device-{did}"
                    role = dev.get("device_role")
                    dtype = str(role.get("slug", "device")) if isinstance(role, dict) else "device"
                    row = db.query(Host).filter(Host.external_id == ext).first()
                    primary = dev.get("primary_ip")
                    ip = None
                    if isinstance(primary, dict) and primary.get("address"):
                        ip = str(primary["address"]).split("/")[0]
                    if row:
                        row.name = dname
                        row.site_id = site_row.id
                        row.type = dtype[:64]
                        if ip:
                            row.ip_address = ip
                    else:
                        db.add(
                            Host(
                                cluster_id=None,
                                site_id=site_row.id,
                                name=dname,
                                type=dtype[:64],
                                external_id=ext,
                                ip_address=ip,
                            )
                        )
                    items += 1

            db.commit()
            return SyncResult(success=True, items_synced=items, message=f"Synced {items} NetBox object(s)")
        except Exception as e:
            logger.exception("NetBox sync failed")
            db.rollback()
            return SyncResult(success=False, error=str(e)[:2048], message=str(e)[:2048])
        finally:
            db.close()
