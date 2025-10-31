"""SQLAlchemy model for VectorizationConfig entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .library_model import LibraryModel


class VectorizationConfigModel(Base):
    """SQLAlchemy model for VectorizationConfig entity.

    Maps to vectorization_configs table in database.
    """

    __tablename__ = "vectorization_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    library_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("libraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunking_strategy_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    embedding_strategy_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    modality_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Relationships
    library: Mapped[LibraryModel] = relationship("LibraryModel", back_populates="vectorization_configs")

    def __repr__(self) -> str:
        return f"<VectorizationConfigModel(id={self.id}, modality={self.modality_type})>"
