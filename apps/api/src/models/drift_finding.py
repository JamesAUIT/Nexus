from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class DriftFinding(Base):
    __tablename__ = "drift_findings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    drift_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # undocumented_asset, missing_asset, ip_mismatch, owner_missing, tag_mismatch
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    expected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_of_truth: Mapped[str] = mapped_column(String(64), nullable=False)
    discovered_from: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
