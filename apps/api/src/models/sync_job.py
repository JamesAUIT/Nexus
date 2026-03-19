from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    connector_id: Mapped[int] = mapped_column(ForeignKey("connectors.id"), nullable=False, index=True)
    schedule_cron: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    connector: Mapped["Connector"] = relationship("Connector", back_populates="sync_jobs")
    runs: Mapped[list["SyncJobRun"]] = relationship("SyncJobRun", back_populates="sync_job")


class SyncJobRun(Base):
    __tablename__ = "sync_job_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sync_job_id: Mapped[int] = mapped_column(ForeignKey("sync_jobs.id"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # running, success, failed
    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)

    sync_job: Mapped["SyncJob"] = relationship("SyncJob", back_populates="runs")
