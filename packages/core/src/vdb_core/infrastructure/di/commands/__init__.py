"""Command provider functions for dependency injection."""

from .document_commands import (
    provide_create_document_command,
    provide_create_document_fragment_command,
    provide_delete_document_command,
    provide_update_document_command,
    provide_upload_document_command,
)
from .ingestion_commands import (
    provide_parse_document_command,
    provide_process_vectorization_config_command,
)
from .library_commands import (
    provide_add_config_to_library_command,
    provide_create_library_command,
    provide_delete_library_command,
    provide_remove_config_from_library_command,
    provide_update_library_command,
)

__all__ = [
    # Document commands
    "provide_create_document_command",
    "provide_create_document_fragment_command",
    # Library commands
    "provide_add_config_to_library_command",
    "provide_create_library_command",
    "provide_delete_document_command",
    "provide_delete_library_command",
    "provide_remove_config_from_library_command",
    # Ingestion commands
    "provide_parse_document_command",
    "provide_process_vectorization_config_command",
    "provide_update_document_command",
    "provide_update_library_command",
    "provide_upload_document_command",
]
