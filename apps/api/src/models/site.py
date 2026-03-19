from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    netbox_site_id: Mapped[int | None] = mapped_column(nullable=True)

    racks: Mapped[list["Rack"]] = relationship("Rack", back_populates="site")
    clusters: Mapped[list["Cluster"]] = relationship("Cluster", back_populates="site")
    hosts: Mapped[list["Host"]] = relationship("Host", back_populates="site")
