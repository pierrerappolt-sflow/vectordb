"""Temporal workflow commands.

These commands are designed to be called from Temporal activities.
They encapsulate the business logic for document processing workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from vdb_core.application.base.command import Command
from vdb_core.application.commands.inputs import (
    ParseAllFragmentsInput,
    ParseDocumentInput,
    ProcessVectorizationConfigInput,
)
from vdb_core.domain.value_objects import DocumentId, DocumentStatus, LibraryId

if TYPE_CHECKING:
    from collections.abc import Callable

    from vdb_core.application.i_unit_of_work import IUnitOfWork
    from vdb_core.application.message_bus import IMessageBus
    from vdb_core.domain.services import IParser


@dataclass(frozen=True)
class ParseDocumentResult:
    """Result of parsing a document fragment."""

    extracted_content_ids: list[str]
    sequence_number: int
    is_final: bool


@dataclass(frozen=True)
class ParseAllFragmentsResult:
    """Result of parsing all document fragments."""

    extracted_content_ids: list[str]


@dataclass(frozen=True)
class ProcessVectorizationConfigResult:
    """Result of processing a document with a VectorizationConfig."""

    config_id: str
    num_chunks: int
    num_embeddings: int
    num_indexed: int


class ParseDocumentCommand(Command[ParseDocumentInput, ParseDocumentResult]):
    """Command to parse a document fragment into ExtractedContent.

    This command orchestrates:
    1. Loading fragment from database
    2. Parsing content using appropriate parser (parser handles modality detection)
    3. Saving ExtractedContent and publishing events

    Designed to be called from Temporal activities for durable execution.

    Example:
        command = ParseDocumentCommand(uow_factory, message_bus, parser)
        result = await command.execute(
            ParseDocumentInput(
                document_id="uuid",
                library_id="uuid",
                fragment_id="uuid",
                sequence_number=0,
                is_final=False
            )
        )

    """

    def __init__(
        self,
        uow_factory: Callable[[], IUnitOfWork],
        message_bus: IMessageBus,
        parser: IParser,
    ) -> None:
        """Initialize command with dependencies.

        Args:
            uow_factory: Factory function that creates UoW instances
            message_bus: Message bus for routing events to handlers
            parser: Service for parsing content (handles modality detection internally)

        """
        super().__init__(uow_factory, message_bus)
        self.parser = parser

    async def _execute(self, input: ParseDocumentInput, uow: IUnitOfWork) -> ParseDocumentResult:
        """Execute the parse document command business logic.

        Args:
            input: The parse document input data
            uow: Active Unit of Work (within transaction)

        Returns:
            Result with extracted content IDs and metadata

        Raises:
            DocumentNotFoundError: If document or fragment doesn't exist
            ParseError: If content parsing fails

        """
        document_id_vo = UUID(input.document_id)
        library_id_vo = UUID(input.library_id)
        fragment_id_vo = UUID(input.fragment_id)

        library = await uow.libraries.get(library_id_vo)
        document = await library.get_document(document_id_vo)
        fragment = await document.get_fragment(fragment_id_vo)

        # 2. Parse content (parser handles modality detection)
        extracted_contents = await self.parser.parse(fragment)

        # 3. Add extracted content through aggregate root (propagates events to library)
        for content in extracted_contents:
            await library.add_document_extracted_content(
                document_id=document_id_vo,
                extracted_content=content,
            )

        # 4. If this is the final fragment, mark document as COMPLETED
        if input.is_final:
            document.update(status=DocumentStatus.COMPLETED)

        return ParseDocumentResult(
            extracted_content_ids=[str(c.id) for c in extracted_contents],
            sequence_number=input.sequence_number,
            is_final=input.is_final,
        )


class ParseAllFragmentsCommand(Command[ParseAllFragmentsInput, ParseAllFragmentsResult]):
    """Command to parse all fragments of a document into ExtractedContent.

    This command orchestrates:
    1. Loading all fragments from the document
    2. Parsing each fragment using appropriate parser (parser handles modality detection)
    3. Saving ExtractedContent and publishing events

    Designed to be called from Temporal activities for durable execution.

    Example:
        command = ParseAllFragmentsCommand(uow_factory, message_bus, parser)
        result = await command.execute(
            ParseAllFragmentsInput(
                document_id="uuid",
                library_id="uuid",
            )
        )

    """

    def __init__(
        self,
        uow_factory: Callable[[], IUnitOfWork],
        message_bus: IMessageBus,
        parser: IParser,
    ) -> None:
        """Initialize command with dependencies.

        Args:
            uow_factory: Factory function that creates UoW instances
            message_bus: Message bus for routing events to handlers
            parser: Service for parsing content (handles modality detection internally)

        """
        super().__init__(uow_factory, message_bus)
        self.parser = parser

    async def _execute(
        self, input_data: ParseAllFragmentsInput, uow: IUnitOfWork
    ) -> ParseAllFragmentsResult:
        """Execute the parse all fragments command business logic.

        Args:
            input_data: The parse all fragments input data
            uow: Active Unit of Work (within transaction)

        Returns:
            Result with extracted content IDs

        Raises:
            DocumentNotFoundError: If document doesn't exist
            ParseError: If content parsing fails

        """
        document_id_vo = DocumentId(input_data.document_id)
        library_id_vo = LibraryId(input_data.library_id)

        # Load library and document
        library = await uow.libraries.get(library_id_vo)
        document = await library.get_document(document_id_vo)

        # Parse all fragments
        all_extracted_content_ids: list[str] = []

        # Load and parse each fragment
        async for fragment in document.load_fragments():
            # Parse content (parser handles modality detection)
            extracted_contents = await self.parser.parse(fragment)

            # Add extracted content through aggregate root (propagates events to library)
            for content in extracted_contents:
                await library.add_document_extracted_content(
                    document_id=document_id_vo,
                    extracted_content=content,
                )
                all_extracted_content_ids.append(str(content.id))

        return ParseAllFragmentsResult(
            extracted_content_ids=all_extracted_content_ids,
        )


class ProcessVectorizationConfigCommand:
    """Command to process a document with a specific VectorizationConfig.

    This command orchestrates:
    1. Loading ExtractedContent from database
    2. Chunking content using config's chunking strategy
    3. Generating embeddings using config's embedding strategy
    4. Indexing vectors in pgvector

    Designed to be called from Temporal activities for durable execution.

    Example:
        command = ProcessVectorizationConfigCommand(
            uow, message_bus, chunking_service, embedding_service
        )
        result = await command.execute(
            ProcessVectorizationConfigInput(
                document_id="uuid",
                library_id="uuid",
                config_id="uuid",
                extracted_content_ids=["uuid1", "uuid2"]
            )
        )

    """

    def __init__(
        self,
        uow: IUnitOfWork,
        message_bus: IMessageBus,
        # TODO(pierre): Add chunking and embedding services when implemented
    ) -> None:
        """Initialize command with dependencies.

        Args:
            uow: Unit of Work for transaction management
            message_bus: Message bus for routing events to handlers

        """
        self.uow = uow
        self.message_bus = message_bus

    async def execute(self, input: ProcessVectorizationConfigInput) -> ProcessVectorizationConfigResult:
        """Execute the process vectorization config command.

        Args:
            input: The process config input data

        Returns:
            Result with counts of chunks, embeddings, and indexed vectors

        Raises:
            ConfigNotFoundError: If config doesn't exist
            ChunkingError: If chunking fails
            EmbeddingError: If embedding generation fails
            TransactionError: If database commit fails

        """
        # TODO(pierre): Implement actual processing logic
        # This is a placeholder for the full implementation

        return ProcessVectorizationConfigResult(
            config_id=input.config_id,
            num_chunks=0,
            num_embeddings=0,
            num_indexed=0,
        )
