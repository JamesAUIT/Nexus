from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class BackupStatus(Base):
    __tablename__ = "backup_statuses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # vm, container
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_connector_id: Mapped[int | None] = mapped_column(ForeignKey("connectors.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    details: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
