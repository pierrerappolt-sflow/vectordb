"""SQLAlchemy model for DocumentFragment entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document_model import DocumentModel


class DocumentFragmentModel(Base):
    """SQLAlchemy model for DocumentFragment entity.

    Maps to document_fragments table in database.
    """

    __tablename__ = "document_fragments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    document: Mapped[DocumentModel] = relationship("DocumentModel", back_populates="fragments")

    def __repr__(self) -> str:
        return f"<DocumentFragmentModel(id={self.id}, document_id={self.document_id}, seq={self.sequence_number})>"
