# VMware vSphere — pyvmomi connectivity and VM inventory sync.
from __future__ import annotations

import logging
import ssl
from typing import Any

from pydantic import BaseModel

from src.connectors.base import ConnectorBase, ConnectorConfig, SyncResult
from src.db.session import SessionLocal
from src.models import Cluster, Connector, VirtualMachine

logger = logging.getLogger(__name__)


class VSphereConfig(ConnectorConfig, BaseModel):
    host: str
    user: str
    password: str
    verify_ssl: bool = True


def _connect(cfg: VSphereConfig):
    from pyVim.connect import SmartConnect

    ctx = ssl.create_default_context()
    if not cfg.verify_ssl:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return SmartConnect(host=cfg.host, user=cfg.user, pwd=cfg.password, sslContext=ctx)


class VSphereConnector(ConnectorBase):
    connector_type = "vsphere"

    def get_config_model(self) -> type[ConnectorConfig]:
        return VSphereConfig

    def test_connectivity(self, config: dict[str, Any]) -> bool:
        try:
            c = VSphereConfig(**config)
            from pyVim.connect import Disconnect

            si = _connect(c)
            Disconnect(si)
            return True
        except Exception as e:
            logger.warning("vSphere connectivity failed: %s", e)
            return False

    def sync(self, config: dict[str, Any], connector_id: int) -> SyncResult:
        try:
            c = VSphereConfig(**config)
        except Exception as e:
            return SyncResult(success=False, error=str(e), message=str(e))

        from pyVim.connect import Disconnect
        from pyVmomi import vim

        db = SessionLocal()
        items = 0
        try:
            conn = db.query(Connector).filter(Connector.id == connector_id).first()
            if not conn:
                return SyncResult(success=False, error="Connector not found", message="Connector not found")

            ext = f"vsphere-conn-{connector_id}"
            cluster = db.query(Cluster).filter(Cluster.external_id == ext).first()
            if not cluster:
                cluster = Cluster(site_id=None, name=conn.name, type="vsphere", external_id=ext)
                db.add(cluster)
                db.flush()
            else:
                cluster.name = conn.name

            si = _connect(c)
            view = None
            try:
                content = si.RetrieveContent()
                view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
                for vm in view.view:
                    if vm.config is None:
                        continue
                    vmname = vm.config.name
                    mo_id = str(vm._moId)
                    ext_vm = f"vsphere-{mo_id}"
                    ps = "unknown"
                    if vm.runtime and vm.runtime.powerState:
                        ps = str(vm.runtime.powerState)
                    vr = (
                        db.query(VirtualMachine)
                        .filter(
                            VirtualMachine.cluster_id == cluster.id,
                            VirtualMachine.external_id == ext_vm,
                        )
                        .first()
                    )
                    if vr:
                        vr.name = vmname
                        vr.power_state = ps
                    else:
                        db.add(
                            VirtualMachine(
                                host_id=None,
                                cluster_id=cluster.id,
                                name=vmname,
                                external_id=ext_vm,
                                power_state=ps,
                            )
                        )
                    items += 1
            finally:
                if view is not None:
                    view.DestroyView()
                Disconnect(si)
            db.commit()
            return SyncResult(success=True, items_synced=items, message=f"vSphere: synced {items} VM(s)")
        except Exception as e:
            logger.exception("vSphere sync failed")
            db.rollback()
            return SyncResult(success=False, error=str(e)[:2048], message=str(e)[:2048])
        finally:
            db.close()
