"""Input dataclasses for command handlers.

These are the typed inputs that commands receive via their execute() method.
They are simple, immutable data containers with no logic.
"""

from dataclasses import dataclass

# ==================== Library Inputs ====================


@dataclass(frozen=True)
class CreateLibraryInput:
    """Input for creating a new library.

    Attributes:
        name: The library name (will be validated by LibraryName value object)

    """

    name: str


@dataclass(frozen=True)
class UpdateLibraryInput:
    """Input for updating an existing library.

    Attributes:
        library_id: The library's unique identifier (UUID string)
        name: The new library name

    """

    library_id: str
    name: str


@dataclass(frozen=True)
class DeleteLibraryInput:
    """Input for deleting a library.

    Attributes:
        library_id: The library's unique identifier (UUID string)

    """

    library_id: str


# ==================== Document Inputs ====================


@dataclass(frozen=True)
class CreateDocumentInput:
    """Input for creating a new document.

    Attributes:
        library_id: The parent library's ID (UUID string)
        name: The document name

    """

    library_id: str
    name: str


@dataclass(frozen=True)
class UpdateDocumentInput:
    """Input for updating an existing document.

    Attributes:
        document_id: The document's unique identifier (UUID string)
        name: The new document name

    """

    document_id: str
    name: str


@dataclass(frozen=True)
class DeleteDocumentInput:
    """Input for deleting a document.

    Attributes:
        document_id: The document's unique identifier (UUID string)

    """

    document_id: str


@dataclass(frozen=True)
class CreateDocumentFragmentInput:
    """Input for creating a document fragment during streaming upload.

    Attributes:
        library_id: The parent library's ID (UUID string)
        document_id: The parent document's ID (UUID string)
        sequence_number: Order fragment was received
        content: Raw bytes (could be part of image, PDF, etc.)
        is_final: True if this is the last fragment

    """

    library_id: str
    document_id: str
    sequence_number: int
    content: bytes
    is_final: bool = False


@dataclass(frozen=True)
class UploadDocumentInput:
    """Input for streaming document upload.

    Attributes:
        library_id: Parent library ID (UUID string)
        filename: Document filename

    """

    library_id: str
    filename: str


# ==================== Library-Config Association Inputs ====================


@dataclass(frozen=True)
class AddConfigToLibraryInput:
    """Input for adding a vectorization config to a library.

    Attributes:
        library_id: The library's unique identifier (UUID string)
        config_id: The vectorization config's unique identifier (UUID string)

    """

    library_id: str
    config_id: str


@dataclass(frozen=True)
class RemoveConfigFromLibraryInput:
    """Input for removing a vectorization config from a library.

    Attributes:
        library_id: The library's unique identifier (UUID string)
        config_id: The vectorization config's unique identifier (UUID string)

    """

    library_id: str
    config_id: str


# ==================== Query Inputs ====================


@dataclass(frozen=True)
class CreateQueryInput:
    """Input for creating a query.

    Attributes:
        library_id: The library to query
        query_text: The search query text
        top_k: Number of results to return

    """

    library_id: str
    query_text: str
    top_k: int = 10


# ==================== Temporal Workflow Inputs ====================


@dataclass(frozen=True)
class ParseDocumentInput:
    """Input for parsing a document fragment.

    Attributes:
        document_id: ID of the document
        library_id: ID of the library
        fragment_id: ID of the fragment to parse
        sequence_number: Fragment sequence number
        is_final: Whether this is the final fragment

    """

    document_id: str
    library_id: str
    fragment_id: str
    sequence_number: int
    is_final: bool


@dataclass(frozen=True)
class ParseAllFragmentsInput:
    """Input for parsing all fragments of a document into ExtractedContent.

    Attributes:
        library_id: ID of the library
        document_id: ID of the document

    """

    library_id: str
    document_id: str


@dataclass(frozen=True)
class ProcessVectorizationConfigInput:
    """Input for processing a document with a specific VectorizationConfig.

    Attributes:
        document_id: ID of the document
        library_id: ID of the library
        config_id: ID of the vectorization config
        extracted_content_ids: List of ExtractedContent IDs to process

    """

    document_id: str
    library_id: str
    config_id: str
    extracted_content_ids: list[str]
