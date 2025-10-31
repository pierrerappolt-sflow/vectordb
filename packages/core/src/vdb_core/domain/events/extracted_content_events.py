"""Events related to ExtractedContent lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from vdb_core.domain.base import DomainEvent

if TYPE_CHECKING:
    from vdb_core.domain.value_objects import (
        DocumentFragmentId,
        DocumentId,
        ExtractedContentId,
        LibraryId,
        ModalityType,
    )


@dataclass(frozen=True)
class ExtractedContentCreated(DomainEvent):
    """Published when ParseDocumentWorkflow creates ExtractedContent.

    This event signals that content has been extracted from a DocumentFragment
    and is ready for vectorization according to library's VectorizationConfigs.

    Subscribers:
        - VectorizationConfig consumer: triggers ProcessVectorizationConfigWorkflow
          for each config that matches this modality

    Attributes:
        library_id: Library this content belongs to
        document_id: Document this content belongs to
        document_fragment_id: Source fragment
        extracted_content_id: ID of created ExtractedContent
        modality: Detected modality (TEXT, IMAGE, VIDEO, AUDIO)
        modality_sequence_number: Order within modality (1st TEXT, 2nd TEXT, etc.)
        is_last_of_modality: True if this is the last content of this modality

    """

    library_id: LibraryId
    document_id: DocumentId
    document_fragment_id: DocumentFragmentId
    extracted_content_id: ExtractedContentId
    modality: ModalityType
    modality_sequence_number: int
    is_last_of_modality: bool
