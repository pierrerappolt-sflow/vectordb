"""Repository protocol for DocumentVectorizationStatus tracking."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from vdb_core.domain.value_objects import DocumentId, VectorizationConfigId


class DocumentVectorizationStatusRecord:
    """Read model for document vectorization status.

    This is a simple data structure, not a domain entity, since
    document_vectorization_status is a tracking table for workflow state.
    """

    def __init__(
        self,
        id: str,
        document_id: str,
        config_id: str,
        status: str,
        error_message: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        """Initialize status record.

        Args:
            id: Status entry ID
            document_id: Document ID
            config_id: Vectorization config ID
            status: Processing status (pending, processing, completed, failed)
            error_message: Error message if status is failed
            created_at: Creation timestamp
            updated_at: Last update timestamp

        """
        self.id = id
        self.document_id = document_id
        self.config_id = config_id
        self.status = status
        self.error_message = error_message
        self.created_at = created_at
        self.updated_at = updated_at


class IDocumentVectorizationStatusRepository(Protocol):
    """Repository for managing document vectorization status tracking.

    This repository manages the document_vectorization_status table which
    tracks processing state for each (document, config) pair.

    Status lifecycle:
        pending → processing → completed
                            ↘ failed

    Note: This is a tracking/status table in the infrastructure layer,
    not a core domain aggregate. It exists to coordinate Temporal workflows.
    """

    async def upsert(
        self,
        document_id: DocumentId,
        config_id: VectorizationConfigId,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Create or update status entry for document+config pair.

        Uses INSERT ... ON CONFLICT to handle idempotency.

        Args:
            document_id: Document ID
            config_id: Vectorization config ID
            status: Processing status (pending, processing, completed, failed)
            error_message: Optional error message (only for failed status)

        """
        ...

    async def get(
        self,
        document_id: DocumentId,
        config_id: VectorizationConfigId,
    ) -> DocumentVectorizationStatusRecord | None:
        """Get status for specific document+config pair.

        Args:
            document_id: Document ID
            config_id: Vectorization config ID

        Returns:
            Status record if found, None otherwise

        """
        ...

    async def list_by_document(
        self,
        document_id: DocumentId,
    ) -> list[DocumentVectorizationStatusRecord]:
        """Get all status entries for a document across all configs.

        Args:
            document_id: Document ID

        Returns:
            List of status records

        """
        ...

    async def list_by_config(
        self,
        config_id: VectorizationConfigId,
    ) -> list[DocumentVectorizationStatusRecord]:
        """Get all status entries for a config across all documents.

        Args:
            config_id: Vectorization config ID

        Returns:
            List of status records

        """
        ...

    async def list_pending(
        self,
        limit: int = 100,
    ) -> list[DocumentVectorizationStatusRecord]:
        """Get pending status entries for workflow scheduling.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of pending status records

        """
        ...
