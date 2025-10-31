"""SQLAlchemy model for Chunk entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document_model import DocumentModel


class ChunkModel(Base):
    """SQLAlchemy model for Chunk entity.

    Maps to chunks table in database.
    """

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunking_strategy_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    extracted_content_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    modality_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Relationships
    document: Mapped[DocumentModel] = relationship("DocumentModel", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<ChunkModel(id={self.id}, document_id={self.document_id}, seq={self.sequence_number})>"
