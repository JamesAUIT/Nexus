from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class HealthCheckDefinition(Base):
    __tablename__ = "health_check_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_type: Mapped[str] = mapped_column(String(64), nullable=False)


class HealthCheckRun(Base):
    __tablename__ = "health_check_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    results: Mapped[list["HealthCheckResult"]] = relationship("HealthCheckResult", back_populates="run")


class HealthCheckResult(Base):
    __tablename__ = "health_check_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    health_check_run_id: Mapped[int] = mapped_column(ForeignKey("health_check_runs.id"), nullable=False, index=True)
    definition_id: Mapped[int] = mapped_column(ForeignKey("health_check_definitions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped["HealthCheckRun"] = relationship("HealthCheckRun", back_populates="results")
