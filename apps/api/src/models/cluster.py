from __future__ import annotations

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # proxmox, vsphere
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    site: Mapped["Site"] = relationship("Site", back_populates="clusters")
    hosts: Mapped[list["Host"]] = relationship("Host", back_populates="cluster")
    virtual_machines: Mapped[list["VirtualMachine"]] = relationship("VirtualMachine", back_populates="cluster")
    proxmox_snapshots: Mapped[list["ProxmoxSnapshot"]] = relationship("ProxmoxSnapshot", back_populates="cluster")
    proxmox_findings: Mapped[list["ProxmoxFinding"]] = relationship("ProxmoxFinding", back_populates="cluster")
    proxmox_tasks: Mapped[list["ProxmoxTask"]] = relationship("ProxmoxTask", back_populates="cluster")
    proxmox_entities: Mapped[list["ProxmoxEntity"]] = relationship("ProxmoxEntity", back_populates="cluster")
    snapshot_acknowledgements: Mapped[list["SnapshotAcknowledgement"]] = relationship("SnapshotAcknowledgement", back_populates="cluster")
    haproxy_config_versions: Mapped[list["HAProxyConfigVersion"]] = relationship("HAProxyConfigVersion", back_populates="cluster")
