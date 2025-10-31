"""Temporal worker for processing VectorDB tasks.

This worker polls the Temporal server for workflow and activity tasks
and executes them using the application's business logic.
"""

import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.worker import Worker
from vdb_core.infrastructure import (
    SearchWorkflow,
    enrich_search_results_activity,
    generate_query_embedding_activity,
    search_vectors_activity,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the Temporal worker."""
    # Get configuration from environment
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("WORKER_TASK_QUEUE", "vdb-tasks")

    # Connect to Temporal server
    temporal_address = f"{temporal_host}:{temporal_port}"
    logger.info(f"Connecting to Temporal server at {temporal_address}")

    client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
    )

    logger.info(f"Connected to Temporal namespace: {temporal_namespace}")
    logger.info(f"Listening on task queue: {task_queue}")

    # Register workflows and activities
    logger.info("Registering workflows: SearchWorkflow")
    logger.info("Registering activities: generate_query_embedding, search_vectors, enrich_search_results")

    # Create and start worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[SearchWorkflow],
        activities=[
            generate_query_embedding_activity,
            search_vectors_activity,
            enrich_search_results_activity,
        ],
    )

    logger.info("Worker started successfully. Waiting for tasks...")

    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
