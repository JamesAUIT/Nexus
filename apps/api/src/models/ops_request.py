from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class OpsRequestTemplate(Base):
    __tablename__ = "ops_request_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    request_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_template: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    form_schema: Mapped[str | None] = mapped_column(Text, nullable=True)


class OpsRequest(Base):
    __tablename__ = "ops_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("ops_request_templates.id", ondelete="SET NULL"), nullable=True)
    request_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    form_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
