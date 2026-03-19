from sqlalchemy import String, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class StorageVolume(Base):
    __tablename__ = "storage_volumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    datastore_id: Mapped[int] = mapped_column(ForeignKey("datastores.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    capacity_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    datastore: Mapped["Datastore"] = relationship("Datastore", back_populates="storage_volumes")
