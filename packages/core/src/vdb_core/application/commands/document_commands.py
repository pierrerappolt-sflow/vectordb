"""Document commands for write operations.

Following the Command pattern with Command[TInput, TOutput] base class.
Each command encapsulates the business logic for a specific write operation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from vdb_core.application.base.command import Command
from vdb_core.application.commands.inputs import (
    CreateDocumentFragmentInput,
    CreateDocumentInput,
    DeleteDocumentInput,
    UpdateDocumentInput,
    UploadDocumentInput,
)
from vdb_core.domain.value_objects import (
    MAX_FRAGMENT_SIZE_BYTES,
    ContentHash,
    DocumentId,
    DocumentName,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from vdb_core.application.i_unit_of_work import IUnitOfWork


class CreateDocumentCommand(Command[CreateDocumentInput, DocumentId]):
    """Command to create a new document.

    Example:
        command = CreateDocumentCommand(uow_factory, message_bus)
        document_id = await command.execute(
            CreateDocumentInput(library_id="uuid", name="doc.pdf")
        )

    """

    async def _execute(self, input_data: CreateDocumentInput, uow: IUnitOfWork) -> DocumentId:
        """Create a new document.

        Args:
            input_data: The create document input data
            uow: Active Unit of Work (within transaction)

        Returns:
            The newly created document's ID

        Raises:
            LibraryNotFoundError: If library doesn't exist

        """
        from vdb_core.domain.exceptions import EntityNotFoundError, LibraryNotFoundError

        library_id_vo = UUID(input_data.library_id)

        try:
            library = await uow.libraries.get(library_id_vo)
        except EntityNotFoundError:
            raise LibraryNotFoundError(input_data.library_id) from None

        document = library.add_document(name=input_data.name)

        return document.id


class UpdateDocumentCommand(Command[UpdateDocumentInput, DocumentId]):
    """Command to update an existing document.

    Example:
        command = UpdateDocumentCommand(uow_factory, message_bus)
        document_id = await command.execute(
            UpdateDocumentInput(document_id="uuid", name="new-name.pdf")
        )

    """

    async def _execute(self, input_data: UpdateDocumentInput, uow: IUnitOfWork) -> DocumentId:
        """Update an existing document.

        Args:
            input_data: The update document input data
            uow: Active Unit of Work (within transaction)

        Returns:
            The updated document's ID

        """
        document_id_vo = UUID(input_data.document_id)

        # Load library (aggregate root)
        library = await uow.libraries.get_by_document_id(document_id_vo)

        # Update document through aggregate root (propagates events to library)
        document = await library.update_document(
            document_id=document_id_vo,
            name=input_data.name,
        )

        return document.id


class DeleteDocumentCommand(Command[DeleteDocumentInput, None]):
    """Command to delete a document.

    Example:
        command = DeleteDocumentCommand(uow_factory, message_bus)
        await command.execute(DeleteDocumentInput(document_id="uuid"))

    """

    async def _execute(self, input_data: DeleteDocumentInput, uow: IUnitOfWork) -> None:
        """Delete a document.

        Args:
            input_data: The delete document input data
            uow: Active Unit of Work (within transaction)

        """
        document_id_vo = UUID(input_data.document_id)
        library = await uow.libraries.get_by_document_id(document_id_vo)
        await library.remove_document(document_id_vo)

class CreateDocumentFragmentCommand(Command[CreateDocumentFragmentInput, str]):
    """Command to create a document fragment during streaming upload.

    Example:
        command = CreateDocumentFragmentCommand(uow_factory, message_bus)
        fragment_id = await command.execute(
            CreateDocumentFragmentInput(
                library_id="uuid",
                document_id="uuid",
                sequence_number=0,
                content=b"...",
                is_final=False
            )
        )

    """

    async def _execute(self, input_data: CreateDocumentFragmentInput, uow: IUnitOfWork) -> str:
        """Create a document fragment.

        Args:
            input_data: The create document fragment input data
            uow: Active Unit of Work (within transaction)

        Returns:
            The newly created fragment's ID (as string)

        Raises:
            LibraryNotFoundError: If library doesn't exist

        """
        from vdb_core.domain.exceptions import LibraryNotFoundError

        library_id_vo = UUID(input_data.library_id)
        document_id_vo = UUID(input_data.document_id)

        # Load library (aggregate root)
        library = await uow.libraries.get(library_id_vo)

        if library is None:
            raise LibraryNotFoundError(input_data.library_id)

        # Add fragment through aggregate root (propagates events to library)
        fragment = await library.add_document_fragment(
            document_id=document_id_vo,
            sequence_number=input_data.sequence_number,
            content=input_data.content,
            content_hash=ContentHash.from_bytes(input_data.content),
            is_final=input_data.is_final,
        )

        return str(fragment.id)


class UploadDocumentCommand:
    """Command for streaming document upload with incremental fragment processing.

    NOTE: This command doesn't inherit from Command[TInput, TOutput] because
    it has a custom execute() signature that takes an additional 'chunks' parameter.
    It orchestrates CreateDocumentCommand and CreateDocumentFragmentCommand.

    Orchestrates:
    1. Document creation (empty) via CreateDocumentCommand
    2. Batching incoming bytes into <= 1 MB fragments
    3. Fragment creation for each batch via CreateDocumentFragmentCommand
    4. Last fragment marked with is_final=True
    5. Event publication for incremental processing

    Following Cosmic Python + DDD:
    - Document is part of Library aggregate
    - Incoming bytes are batched to stay within MAX_FRAGMENT_SIZE_BYTES (1 MB)
    - Each fragment raises DocumentFragmentReceived event
    - Events trigger pipeline processing immediately (before upload completes!)
    - Final fragment (is_final=True) signals processing can finalize

    Example:
        command = UploadDocumentCommand(
            create_document_cmd, create_fragment_cmd
        )

        async def chunk_iterator():
            yield b"x" * 500_000  # 500 KB
            yield b"y" * 600_000  # 600 KB
            yield b"z" * 100_000  # 100 KB

        # Results in 2 fragments: [1MB batch of x+y, 200KB batch of remaining y+z]
        document_id = await command.execute(
            UploadDocumentInput(
                library_id="uuid",
                filename="document.txt"
            ),
            chunks=chunk_iterator()
        )

    """

    def __init__(
        self,
        create_document_command: CreateDocumentCommand,
        create_fragment_command: CreateDocumentFragmentCommand,
    ) -> None:
        """Initialize command with dependencies.

        Args:
            create_document_command: Command for creating documents
            create_fragment_command: Command for creating document fragments

        """
        self.create_document_command = create_document_command
        self.create_fragment_command = create_fragment_command

    async def _batch_chunks(self, chunks: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """Batch incoming chunks into fragments of <= MAX_FRAGMENT_SIZE_BYTES (1 MB).

        Accumulates bytes from the input stream until reaching the fragment size limit,
        then yields a complete batch. This ensures fragments stay within the 1 MB limit
        while maximizing fragment size for efficient processing.

        Args:
            chunks: Async iterator of arbitrary-sized byte chunks

        Yields:
            Batched byte chunks, each <= MAX_FRAGMENT_SIZE_BYTES

        Example:
            Input:  [500KB, 600KB, 400KB, 100KB]
            Output: [1MB, 600KB]  # First two chunks batched, rest yielded as-is

        """
        buffer = bytearray()

        async for chunk in chunks:
            buffer.extend(chunk)

            # Yield complete fragments when buffer exceeds limit
            while len(buffer) >= MAX_FRAGMENT_SIZE_BYTES:
                # Yield exactly MAX_FRAGMENT_SIZE_BYTES
                yield bytes(buffer[:MAX_FRAGMENT_SIZE_BYTES])
                # Keep remainder in buffer
                buffer = buffer[MAX_FRAGMENT_SIZE_BYTES:]

        # Yield any remaining bytes as final fragment
        if buffer:
            yield bytes(buffer)

    async def execute(
        self,
        input_data: UploadDocumentInput,
        chunks: AsyncIterator[bytes],
    ) -> DocumentId:
        """Upload document from async chunk iterator.

        Args:
            input_data: The upload document input data
            chunks: Async iterator yielding document chunks

        Returns:
            The newly created document's ID

        Raises:
            LibraryNotFoundError: If parent library doesn't exist
            ValidationException: If validation fails
            TransactionError: If database commit fails

        """
        # 1. Create empty document using CreateDocumentCommand
        create_doc_input = CreateDocumentInput(
            library_id=input_data.library_id,
            name=input_data.filename,
        )
        document_id = await self.create_document_command.execute(create_doc_input)

        # 2. Stream fragments (each via CreateDocumentFragmentCommand)
        # Batch chunks into <= 1 MB fragments before creating DocumentFragment entities
        # Buffer one fragment to know when we've reached the last one
        sequence = 0
        total_bytes = 0
        previous_batch = None

        async for batch in self._batch_chunks(chunks):
            # If we have a previous batch, create fragment with is_final=False
            if previous_batch is not None:
                fragment_input = CreateDocumentFragmentInput(
                    library_id=input_data.library_id,
                    document_id=str(document_id),
                    sequence_number=sequence,
                    content=previous_batch,
                    is_final=False,
                )
                await self.create_fragment_command.execute(fragment_input)
                sequence += 1
                total_bytes += len(previous_batch)

            # Store current batch to process next iteration
            previous_batch = batch

        # 3. Create final fragment with is_final=True (if any content was uploaded)
        if previous_batch is not None:
            fragment_input = CreateDocumentFragmentInput(
                library_id=input_data.library_id,
                document_id=str(document_id),
                sequence_number=sequence,
                content=previous_batch,
                is_final=True,
            )
            await self.create_fragment_command.execute(fragment_input)

        return document_id
