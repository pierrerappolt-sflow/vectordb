"""Message handlers for document-related domain events."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.domain.events import (
        DocumentCreated,
        DocumentDeleted,
        DocumentUpdated,
    )


class DocumentMessageHandlers:
    """Handlers for document domain events.

    These handlers react to document lifecycle events.

    Message handlers are called AFTER successful transaction commit,
    so they can safely trigger async operations without worrying
    about transaction rollback.

    Example usage:
        handlers = DocumentMessageHandlers(uow=uow)
        message_bus.register(DocumentCreated, handlers.on_document_created)
        message_bus.register(DocumentUpdated, handlers.on_document_updated)
        message_bus.register(DocumentDeleted, handlers.on_document_deleted)
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize handlers with dependencies.

        Args:
            uow: Unit of Work for loading entities

        """
        self.uow = uow

    async def on_document_created(self, event: DocumentCreated) -> None:
        """Handle document creation event.

        Triggered when a new document is created. This is where you would:
        - Send notifications
        - Update analytics
        - Create initial metadata

        Args:
            event: The document created event

        Note:
            This handler is called AFTER the document has been persisted,
            so the document definitely exists in the database.

        """

    async def on_document_updated(self, event: DocumentUpdated) -> None:
        """Handle document update event.

        Triggered when a document is updated. This is where you would:
        - Re-process document if needed
        - Update search index
        - Invalidate caches

        Args:
            event: The document updated event

        """

    async def on_document_deleted(self, event: DocumentDeleted) -> None:
        """Handle document deletion event.

        Triggered when a document is deleted. This is where you would:
        - Delete associated chunks and embeddings
        - Remove from search index
        - Clean up storage

        Args:
            event: The document deleted event

        """
