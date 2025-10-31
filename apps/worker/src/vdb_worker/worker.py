"""Temporal worker for processing VectorDB tasks.

This unified worker handles all VectorDB workflows and activities using
the Command pattern for decoupled, testable business logic.

Architecture:
    Temporal Worker → Workflows (orchestration) → Activities (thin wrappers) → Commands (business logic)

The worker connects to Temporal server and polls for tasks on the configured
task queue. Commands contain all business logic and can be tested independently.
"""

import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions
from vdb_core.infrastructure import (
    DIContainer,
)
from vdb_core.infrastructure.activities import (
    set_di_container,
)
from vdb_core.infrastructure.activities.ingestion_activities import (
    get_library_configs_activity,
    mark_document_completed_activity,
    parse_all_fragments_activity,
)
from vdb_core.infrastructure.activities.process_config_activities import (
    chunk_content_activity,
    generate_embeddings_activity,
    index_vectors_activity,
    load_extracted_content_activity,
    mark_config_processing_completed_activity,
)
from vdb_core.infrastructure.workflows.ingest_document_workflow import (
    IngestDocumentWorkflow,
)
from vdb_core.infrastructure.workflows.process_config_workflow import (
    ProcessConfigWorkflow,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the Temporal worker for VectorDB operations."""
    # Initialize DI container for activities
    logger.info("Initializing DI container")
    container = DIContainer()

    # Log configuration for debugging
    storage_type = container.config.get_storage_type()
    logger.info("📊 Configuration loaded:")
    logger.info("  - Storage type: %s", storage_type.value)
    logger.info("  - Message bus: %s", container.config.infrastructure.message_bus.type)
    logger.info("  - Read models: %s", container.config.infrastructure.read_models.type)

    set_di_container(container)

    # Get configuration from environment
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("WORKER_TASK_QUEUE", "vdb-tasks")

    # Connect to Temporal server
    temporal_address = f"{temporal_host}:{temporal_port}"
    logger.info("Connecting to Temporal server at %s", temporal_address)

    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
    )

    logger.info("Connected to Temporal namespace: %s", temporal_namespace)
    logger.info("Task queue: %s", task_queue)

    # Register workflows and activities
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEMPORAL WORKFLOWS & ACTIVITIES")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Registered Workflows:")
    logger.info("  - IngestDocumentWorkflow")
    logger.info("      → Parses document fragments and triggers vectorization")
    logger.info("  - ProcessConfigWorkflow")
    logger.info("      → Chunks content, generates embeddings, indexes vectors")
    logger.info("")
    logger.info("Registered Activities:")
    logger.info("  Ingestion: parse_all_fragments, get_library_configs, mark_document_completed")
    logger.info("  Processing: load_extracted_content, chunk_content, generate_embeddings, index_vectors, mark_config_processing_completed")
    logger.info("")
    logger.info("Note: SearchWorkflow runs on dedicated search-worker (task queue: vdb-search-tasks)")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

    # Configure sandbox with passthrough for vdb_core modules
    workflow_runner = SandboxedWorkflowRunner(
        restrictions=SandboxRestrictions.default.with_passthrough_modules(
            "vdb_core",
            "vdb_core.domain",
            "vdb_core.domain.value_objects",
            "vdb_core.infrastructure",
            "vdb_core.infrastructure.workflows",
        )
    )

    # Create worker with ingestion and processing workflows only
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            IngestDocumentWorkflow,
            ProcessConfigWorkflow,
        ],
        activities=[
            # Ingestion workflow activities
            parse_all_fragments_activity,
            get_library_configs_activity,
            mark_document_completed_activity,
            # Process config activities
            load_extracted_content_activity,
            chunk_content_activity,
            generate_embeddings_activity,
            index_vectors_activity,
            mark_config_processing_completed_activity,
        ],
        workflow_runner=workflow_runner,
        max_concurrent_activities=10,  # Limit parallel activity execution
        max_concurrent_workflow_tasks=10,   # Limit parallel workflow task execution
    )

    logger.info("✅ VectorDB worker started successfully")
    logger.info("Concurrency limits: max 10 parallel activities, max 10 parallel workflows")
    logger.info("Waiting for tasks...")
    logger.info("")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
