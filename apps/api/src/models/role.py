from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # JSON list of permission strings e.g. ["sites:read", "sites:write"]
    permissions: Mapped[str] = mapped_column(String(2048), nullable=False, default="[]")

    users: Mapped[list["User"]] = relationship("User", back_populates="role")
