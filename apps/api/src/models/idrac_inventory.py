from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class IDracInventory(Base):
    __tablename__ = "idrac_inventory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    host_id: Mapped[int | None] = mapped_column(ForeignKey("hosts.id", ondelete="SET NULL"), nullable=True, index=True)
    connector_id: Mapped[int | None] = mapped_column(ForeignKey("connectors.id", ondelete="SET NULL"), nullable=True)
    target_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bios_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idrac_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    firmware_inventory: Mapped[str | None] = mapped_column(Text, nullable=True)
    compliance_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_scan_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scan_error: Mapped[str | None] = mapped_column(String(512), nullable=True)

    host: Mapped["Host | None"] = relationship("Host", back_populates="idrac_inventory", lazy="select")
