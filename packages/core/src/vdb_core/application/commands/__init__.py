"""Application commands for write operations.

Commands follow the Command[TInput, TOutput] pattern where:
- Commands are initialized with dependencies (UoW, services, etc.)
- Commands have an execute(input: TInput) -> TOutput method
- Commands encapsulate business logic for write operations
"""

from .document_commands import (
    CreateDocumentCommand,
    CreateDocumentFragmentCommand,
    DeleteDocumentCommand,
    UpdateDocumentCommand,
    UploadDocumentCommand,
)
from .ingestion_commands import (
    ParseAllFragmentsCommand,
    ParseAllFragmentsResult,
    ParseDocumentCommand,
    ParseDocumentResult,
    ProcessVectorizationConfigCommand,
    ProcessVectorizationConfigResult,
)
from .inputs import (
    AddConfigToLibraryInput,
    CreateDocumentFragmentInput,
    CreateDocumentInput,
    CreateLibraryInput,
    CreateQueryInput,
    DeleteDocumentInput,
    DeleteLibraryInput,
    ParseAllFragmentsInput,
    ParseDocumentInput,
    ProcessVectorizationConfigInput,
    RemoveConfigFromLibraryInput,
    UpdateDocumentInput,
    UpdateLibraryInput,
    UploadDocumentInput,
)
from .library_commands import (
    AddConfigToLibraryCommand,
    CreateLibraryCommand,
    DeleteLibraryCommand,
    RemoveConfigFromLibraryCommand,
    UpdateLibraryCommand,
)

__all__ = [
    # Library-config association commands
    "AddConfigToLibraryCommand",
    "AddConfigToLibraryInput",
    # Document commands
    "CreateDocumentCommand",
    "CreateDocumentFragmentCommand",
    "CreateDocumentFragmentInput",
    "CreateDocumentInput",
    # Library commands
    "CreateLibraryCommand",
    # Input dataclasses
    "CreateLibraryInput",
    "CreateQueryInput",
    "DeleteDocumentCommand",
    "DeleteDocumentInput",
    "DeleteLibraryCommand",
    "DeleteLibraryInput",
    # Ingestion commands
    "ParseAllFragmentsCommand",
    "ParseAllFragmentsInput",
    "ParseAllFragmentsResult",
    "ParseDocumentCommand",
    "ParseDocumentInput",
    "ParseDocumentResult",
    "ProcessVectorizationConfigCommand",
    "ProcessVectorizationConfigInput",
    "ProcessVectorizationConfigResult",
    "RemoveConfigFromLibraryCommand",
    "RemoveConfigFromLibraryInput",
    "UpdateDocumentCommand",
    "UpdateDocumentInput",
    "UpdateLibraryCommand",
    "UpdateLibraryInput",
    "UploadDocumentCommand",
    "UploadDocumentInput",
]
