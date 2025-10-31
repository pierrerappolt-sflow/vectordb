"""Service for orchestrating document vectorization across configs."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vdb_core.domain.events import DocumentVectorizationPending
from vdb_core.domain.value_objects import DocumentId, LibraryId, VectorizationConfigId

if TYPE_CHECKING:
    from collections.abc import Callable

    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.application.repositories.i_document_read_repository import IDocumentReadRepository
    from vdb_core.application.repositories.i_document_vectorization_status_repository import (
        IDocumentVectorizationStatusRepository,
    )

logger = logging.getLogger(__name__)


class VectorizationOrchestrationService:
    """Application service for orchestrating document vectorization workflows.

    This service encapsulates the coordination logic for scheduling vectorization
    processing across documents and configs. It handles:

    1. When config added to library → schedule all library documents
    2. When document uploaded → schedule all library configs
    3. Managing document_vectorization_status tracking table
    4. Raising DocumentVectorizationPending events

    Following Clean Architecture:
    - Application layer service (orchestrates use cases)
    - Depends on repositories (protocols from application layer)
    - Returns events instead of publishing (SRP - separation from event bus)
    - No infrastructure dependencies (asyncpg, SQL, etc.)

    Architecture:
        Event Handler → Orchestration Service → Repositories
                                             ↓
                                         Returns Events
                                             ↓
                                         Message Bus
    """

    def __init__(
        self,
        uow_factory: Callable[[], IUnitOfWork],
        status_repository: IDocumentVectorizationStatusRepository,
        document_read_repository: IDocumentReadRepository,
    ) -> None:
        """Initialize service with dependencies.

        Args:
            uow_factory: Factory function that creates Unit of Work instances
            status_repository: Repository for vectorization status tracking
            document_read_repository: Read repository for querying documents

        """
        self.uow_factory = uow_factory
        self.status_repository = status_repository
        self.document_read_repository = document_read_repository

    async def schedule_library_documents_for_config(
        self,
        library_id: LibraryId,
        config_id: VectorizationConfigId,
    ) -> list[DocumentVectorizationPending]:
        """Schedule all documents in a library for processing with a config.

        Called when:
        - Config is added to a library
        - Config version is upgraded (future)

        Flow:
        1. Query all active documents in library
        2. For each document, create status entry (PENDING)
        3. Generate DocumentVectorizationPending event for each

        Args:
            library_id: Library ID
            config_id: Vectorization config ID

        Returns:
            List of DocumentVectorizationPending events to be published

        """
        logger.info(
            "Scheduling library %s documents for processing with config %s", library_id, config_id
        )

        # Query all active documents in library
        documents = await self.document_read_repository.get_all_in_library(
            library_id=str(library_id),
            limit=10000,  # Large limit to get all documents
            offset=0,
        )

        # Filter out deleted documents
        active_documents = [doc for doc in documents if doc.status != "deleted"]

        if not active_documents:
            logger.info("No active documents found in library %s", library_id)
            return []

        logger.info(
            "Found %s active documents in library %s", len(active_documents), library_id
        )

        # Create status entries and generate events
        events = []
        for doc in active_documents:
            # Create/update status entry as PENDING
            await self.status_repository.upsert(
                document_id=DocumentId(doc.id),
                config_id=config_id,
                status="pending",
                error_message=None,
            )

            # Generate event to trigger workflow
            events.append(
                DocumentVectorizationPending(
                    document_id=DocumentId(doc.id),
                    config_id=config_id,
                    library_id=library_id,
                )
            )

        logger.info(
            "Created %s vectorization status entries for library %s", len(events), library_id
        )

        return events

    async def schedule_document_for_library_configs(
        self,
        document_id: DocumentId,
        library_id: LibraryId,
    ) -> list[DocumentVectorizationPending]:
        """Schedule a document for processing with all library configs.

        Called when:
        - New document is uploaded to library
        - Document is marked as ready for vectorization

        Flow:
        1. Get all active configs associated with library
        2. For each config, create status entry (PENDING)
        3. Generate DocumentVectorizationPending event for each

        Args:
            document_id: Document ID
            library_id: Library ID

        Returns:
            List of DocumentVectorizationPending events to be published

        """
        logger.info(
            "Scheduling document %s for processing with library %s configs", document_id, library_id
        )

        # Get library to access its config_ids
        async with self.uow_factory() as uow:
            library = await uow.libraries.get(library_id)

            if not library.config_ids:
                logger.info("No configs associated with library %s", library_id)
                return []

            logger.info(
                "Found %s configs for library %s", len(library.config_ids), library_id
            )

            # Create status entries and generate events
            events = []
            for config_id in library.config_ids:
                # Create/update status entry as PENDING
                await self.status_repository.upsert(
                    document_id=document_id,
                    config_id=config_id,
                    status="pending",
                    error_message=None,
                )

                # Generate event to trigger workflow
                events.append(
                    DocumentVectorizationPending(
                        document_id=document_id,
                        config_id=config_id,
                        library_id=library_id,
                    )
                )

            logger.info(
                "Created %s vectorization status entries for document %s", len(events), document_id
            )

            return events
