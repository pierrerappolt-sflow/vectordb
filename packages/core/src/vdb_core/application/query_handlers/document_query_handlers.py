"""Document queries for read operations (CQRS pattern)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.application.base.query import Query
from vdb_core.application.queries import (
    GetDocumentByIdQuery as GetDocumentByIdInput,
)
from vdb_core.application.queries import (
    GetDocumentChunksQuery as GetDocumentChunksInput,
)
from vdb_core.application.queries import (
    GetDocumentFragmentsQuery as GetDocumentFragmentsInput,
)
from vdb_core.application.queries import (
    GetDocumentsQuery as GetDocumentsInput,
)
from vdb_core.application.queries import (
    GetDocumentVectorizationStatusQuery as GetDocumentVectorizationStatusInput,
)
from vdb_core.application.read_models import (
    ChunkReadModel,
    DocumentFragmentReadModel,
    DocumentReadModel,
    DocumentVectorizationStatusReadModel,
)

if TYPE_CHECKING:
    from vdb_core.application.read_repository_provider import ReadRepositoryProvider


class GetDocumentsQuery(Query[GetDocumentsInput, list[DocumentReadModel]]):
    """Query to get all documents in a library.

    Following CQRS + Command pattern:
    - Extends Query base class
    - Uses read repository provider
    - Returns read models (DTOs)
    - No business logic, just data retrieval

    Example:
        query = GetDocumentsQuery(read_repo_provider_factory)
        documents = await query.execute(GetDocumentsInput(library_id="uuid", limit=10))

    """

    async def _execute(
        self, input_data: GetDocumentsInput, read_repo_provider: ReadRepositoryProvider
    ) -> list[DocumentReadModel]:
        """Execute the get documents query.

        Args:
            input_data: The query input with library_id and pagination params
            read_repo_provider: Active read repository provider

        Returns:
            List of document read models

        """
        if read_repo_provider.documents is None:
            msg = "Documents repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.documents.get_all_in_library(
            library_id=input_data.library_id,
            limit=input_data.limit,
            offset=input_data.offset,
        )


class GetDocumentByIdQuery(Query[GetDocumentByIdInput, DocumentReadModel | None]):
    """Query to get a document by ID.

    Following CQRS + Command pattern:
    - Handles single document lookup
    - Returns read model or None
    - No domain logic

    """

    async def _execute(
        self, input_data: GetDocumentByIdInput, read_repo_provider: ReadRepositoryProvider
    ) -> DocumentReadModel | None:
        """Execute the get document by ID query.

        Args:
            input_data: The query input with library_id and document_id
            read_repo_provider: Active read repository provider

        Returns:
            Document read model if found, None otherwise

        """
        if read_repo_provider.documents is None:
            msg = "Documents repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.documents.get_by_id(
            library_id=input_data.library_id,
            document_id=input_data.document_id,
        )


class GetDocumentChunksQuery(Query[GetDocumentChunksInput, list[ChunkReadModel]]):
    """Query to get chunks for a document.

    Following CQRS + Command pattern:
    - Handles chunk retrieval for a document
    - Returns chunk read models with text content
    - No domain logic

    """

    async def _execute(
        self, input_data: GetDocumentChunksInput, read_repo_provider: ReadRepositoryProvider
    ) -> list[ChunkReadModel]:
        """Execute the get document chunks query.

        Args:
            input_data: The query input with library_id, document_id, and pagination params
            read_repo_provider: Active read repository provider

        Returns:
            List of chunk read models

        """
        if read_repo_provider.chunks is None:
            msg = "Chunks repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.chunks.get_chunks_by_document(
            library_id=input_data.library_id,
            document_id=input_data.document_id,
            limit=input_data.limit,
            offset=input_data.offset,
        )


class GetDocumentFragmentsQuery(Query[GetDocumentFragmentsInput, list[DocumentFragmentReadModel]]):
    """Query to get fragments for a document.

    Following CQRS + Command pattern:
    - Handles fragment retrieval for a document
    - Returns fragment read models with content
    - No domain logic

    """

    async def _execute(
        self, input_data: GetDocumentFragmentsInput, read_repo_provider: ReadRepositoryProvider
    ) -> list[DocumentFragmentReadModel]:
        """Execute the get document fragments query.

        Args:
            input_data: The query input with library_id, document_id, and pagination params
            read_repo_provider: Active read repository provider

        Returns:
            List of fragment read models

        """
        if read_repo_provider.document_fragments is None:
            msg = "Document fragments repository not initialized"
            raise RuntimeError(msg)
        return await read_repo_provider.document_fragments.get_all_in_document(
            library_id=input_data.library_id,
            document_id=input_data.document_id,
            limit=input_data.limit,
            offset=input_data.offset,
        )


class GetDocumentVectorizationStatusQuery(
    Query[GetDocumentVectorizationStatusInput, list[DocumentVectorizationStatusReadModel]]
):
    """Query to get vectorization status for a document.

    Following CQRS + Command pattern:
    - Handles status retrieval for document vectorization
    - Returns status read models showing PENDING/PROCESSING/COMPLETED/FAILED
    - No domain logic

    """

    async def _execute(
        self, input_data: GetDocumentVectorizationStatusInput, read_repo_provider: ReadRepositoryProvider
    ) -> list[DocumentVectorizationStatusReadModel]:
        """Execute the get document vectorization status query.

        Args:
            input_data: The query input with library_id and document_id
            read_repo_provider: Active read repository provider

        Returns:
            List of status read models for each config processing this document

        """
        # Need to check if this repository exists on read_repo_provider
        # For now, will need to add this to the ReadRepositoryProvider class
        msg = "Document vectorization status repository not yet added to ReadRepositoryProvider"
        raise NotImplementedError(msg)
