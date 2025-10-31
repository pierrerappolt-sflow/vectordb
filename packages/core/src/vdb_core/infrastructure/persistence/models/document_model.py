"""SQLAlchemy model for Document entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .chunk_model import ChunkModel
    from .document_fragment_model import DocumentFragmentModel
    from .extracted_content_model import ExtractedContentModel
    from .library_model import LibraryModel


class DocumentModel(Base):
    """SQLAlchemy model for Document entity.

    Maps to documents table in database.
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    library_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("libraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    upload_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    library: Mapped[LibraryModel] = relationship("LibraryModel", back_populates="documents")
    fragments: Mapped[list[DocumentFragmentModel]] = relationship(
        "DocumentFragmentModel",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    extracted_contents: Mapped[list[ExtractedContentModel]] = relationship(
        "ExtractedContentModel",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    chunks: Mapped[list[ChunkModel]] = relationship(
        "ChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DocumentModel(id={self.id}, name={self.name}, library_id={self.library_id})>"
