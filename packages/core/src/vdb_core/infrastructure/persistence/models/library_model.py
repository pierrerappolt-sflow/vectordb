"""SQLAlchemy model for Library aggregate root."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document_model import DocumentModel
    from .vectorization_config_model import VectorizationConfigModel


class LibraryModel(Base):
    """SQLAlchemy model for Library aggregate root.

    Maps to libraries table in database.
    """

    __tablename__ = "libraries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    # Relationships
    documents: Mapped[list[DocumentModel]] = relationship(
        "DocumentModel",
        back_populates="library",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    vectorization_configs: Mapped[list[VectorizationConfigModel]] = relationship(
        "VectorizationConfigModel",
        back_populates="library",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<LibraryModel(id={self.id}, name={self.name})>"
