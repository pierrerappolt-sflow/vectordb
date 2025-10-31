"""SQLAlchemy model for ExtractedContent entity."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document_model import DocumentModel


class ExtractedContentModel(Base):
    """SQLAlchemy model for ExtractedContent entity.

    Maps to extracted_contents table in database.
    """

    __tablename__ = "extracted_contents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_fragment_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    modality_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    modality_sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_last_of_modality: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    document: Mapped[DocumentModel] = relationship("DocumentModel", back_populates="extracted_contents")

    def __repr__(self) -> str:
        return f"<ExtractedContentModel(id={self.id}, modality={self.modality_type}, seq={self.modality_sequence_number})>"
