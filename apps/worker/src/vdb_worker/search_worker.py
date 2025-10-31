"""Dedicated Temporal worker for search operations.

This specialized worker handles only SearchWorkflow and search-related activities,
allowing independent scaling and resource allocation for search operations.

Architecture:
    Temporal Worker → SearchWorkflow → Search Activities → Search Commands

The worker connects to Temporal and polls for tasks on the 'vdb-search-tasks' queue.
This separation allows search to scale independently from ingestion/processing workflows.
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
from vdb_core.infrastructure.activities.search_activities import (
    enrich_search_results_activity,
    generate_query_embedding_activity,
    search_vectors_activity,
    update_query_status_activity,
)
from vdb_core.infrastructure.workflows.search_workflow import (
    SearchWorkflow,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the dedicated search worker."""
    # Initialize DI container for activities
    logger.info("Initializing DI container for search worker")
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
    task_queue = os.getenv("WORKER_TASK_QUEUE", "vdb-search-tasks")

    # Connect to Temporal server
    temporal_address = f"{temporal_host}:{temporal_port}"
    logger.info("Connecting to Temporal server at %s", temporal_address)

    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
    )

    logger.info("Connected to Temporal namespace: %s", temporal_namespace)
    logger.info("Task queue: %s", task_queue)

    # Register search workflow and activities only
    logger.info("")
    logger.info("=" * 80)
    logger.info("SEARCH WORKER - TEMPORAL WORKFLOWS & ACTIVITIES")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Registered Workflows:")
    logger.info("  - SearchWorkflow")
    logger.info("      → Generates query embedding, searches vectors, enriches results")
    logger.info("")
    logger.info("Registered Activities:")
    logger.info("  Search: generate_query_embedding, search_vectors, enrich_search_results, update_query_status")
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

    # Create worker with search workflow and activities only
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            SearchWorkflow,
        ],
        activities=[
            generate_query_embedding_activity,
            search_vectors_activity,
            enrich_search_results_activity,
            update_query_status_activity,
        ],
        workflow_runner=workflow_runner,
        max_concurrent_activities=20,  # Search is lightweight, allow more concurrency
        max_concurrent_workflow_tasks=20,
    )

    logger.info("✅ Search worker started successfully")
    logger.info("Concurrency limits: max 20 parallel activities, max 20 parallel workflows")
    logger.info("Waiting for search tasks...")
    logger.info("")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
