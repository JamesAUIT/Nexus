from __future__ import annotations

from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class ScriptDefinition(Base):
    __tablename__ = "script_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    script_type: Mapped[str] = mapped_column(String(32), nullable=False)
    approved_only: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parameters_schema: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_permission: Mapped[str | None] = mapped_column(String(64), nullable=True)

    executions: Mapped[list["ScriptExecution"]] = relationship("ScriptExecution", back_populates="script_definition")
