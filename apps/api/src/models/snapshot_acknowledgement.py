from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class SnapshotAcknowledgement(Base):
    __tablename__ = "snapshot_acknowledgements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False, index=True)
    vm_id: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ack_by: Mapped[str] = mapped_column(String(255), nullable=False)
    ack_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="snapshot_acknowledgements")
