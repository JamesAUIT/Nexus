from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Runbook(Base):
    __tablename__ = "runbooks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    tags: Mapped[str | None] = mapped_column(String(512), nullable=True)
    related_systems: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_links: Mapped[str | None] = mapped_column(Text, nullable=True)
