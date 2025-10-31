"""RabbitMQ consumer that triggers Temporal workflows."""

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pika
from pika.adapters.blocking_connection import BlockingChannel
from temporalio.client import Client
from vdb_core.infrastructure.workflows import (
    IngestDocumentWorkflow,
    IngestDocumentWorkflowInput,
    ProcessConfigWorkflow,
    ProcessConfigWorkflowInput,
    SearchWorkflow,
    SearchWorkflowInput,
)

logger = logging.getLogger(__name__)


class TemporalIngestionConsumer:
    """Consumes workflow-triggering events from RabbitMQ and triggers Temporal workflows.

    This service bridges RabbitMQ and Temporal:
    1. Subscribes to workflow_events queue
    2. Receives domain events (DocumentCreated, LibraryConfigAdded, etc.)
    3. Triggers appropriate Temporal workflows (IngestDocument, ProcessConfig, etc.)
    4. Acknowledges message after workflow starts

    Each consumer runs in its own process/pod and can be scaled independently.
    """

    def __init__(
        self,
        rabbitmq_host: str,
        rabbitmq_port: int,
        queue_name: str,
        temporal_client: Client,
        task_queue: str,
    ) -> None:
        """Initialize consumer.

        Args:
            rabbitmq_host: RabbitMQ host
            rabbitmq_port: RabbitMQ port
            queue_name: Queue to consume from (e.g., "workflow_events")
            temporal_client: Connected Temporal client
            task_queue: Temporal task queue name

        """
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.queue_name = queue_name
        self.temporal_client = temporal_client
        self.task_queue = task_queue

        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self._executor = ThreadPoolExecutor(max_workers=10)

    def start(self) -> None:
        """Start consuming messages from RabbitMQ."""
        logger.info("Starting TemporalIngestionConsumer for queue %s", self.queue_name)

        # Connect to RabbitMQ
        connection_params = pika.ConnectionParameters(
            host=self.rabbitmq_host,
            port=self.rabbitmq_port,
            credentials=pika.PlainCredentials("guest", "guest"),
            heartbeat=600,
        )

        self._connection = pika.BlockingConnection(connection_params)
        self._channel = self._connection.channel()

        # Declare exchange (idempotent - ensures it exists)
        self._channel.exchange_declare(
            exchange="vdb.events",
            exchange_type="topic",
            durable=True,
        )

        # Declare queue (idempotent)
        self._channel.queue_declare(
            queue=self.queue_name,
            durable=True,  # Survive broker restart
        )

        # Bind queue to exchange with routing patterns
        self._channel.queue_bind(
            exchange="vdb.events",
            queue=self.queue_name,
            routing_key="document.*",  # Match all document events
        )
        self._channel.queue_bind(
            exchange="vdb.events",
            queue=self.queue_name,
            routing_key="library.config.*",  # Match library config events
        )
        self._channel.queue_bind(
            exchange="vdb.events",
            queue=self.queue_name,
            routing_key="vectorization.*",  # Match vectorization events
        )
        self._channel.queue_bind(
            exchange="vdb.events",
            queue=self.queue_name,
            routing_key="content.*",  # Match extracted content events
        )

        # Set QoS - prefetch 1 message at a time
        self._channel.basic_qos(prefetch_count=1)

        # Start consuming
        logger.info("Waiting for messages on queue %s...", self.queue_name)
        self._channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._on_message,
            auto_ack=False,  # Manual ack after processing
        )

        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
            self.stop()

    def _on_message(
        self,
        channel: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Handle incoming message from RabbitMQ.

        Args:
            channel: RabbitMQ channel
            method: Delivery method
            properties: Message properties
            body: Message body (JSON bytes)

        """
        try:
            # Parse event
            event_data = json.loads(body.decode("utf-8"))
            event_type = event_data["event_type"]

            logger.info("Received event: %s", event_type)

            # Run async handler in a thread pool to avoid event loop conflicts
            def run_async_handler():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Route to appropriate handler
                    if event_type == "DocumentFragmentReceived":
                        loop.run_until_complete(self._handle_document_fragment(event_data))

                    elif event_type == "ExtractedContentCreated":
                        loop.run_until_complete(self._handle_extracted_content(event_data))

                    elif event_type == "LibraryConfigAdded":
                        loop.run_until_complete(self._handle_library_config_added(event_data))

                    elif event_type == "LibraryConfigRemoved":
                        loop.run_until_complete(self._handle_library_config_removed(event_data))

                    elif event_type == "VectorizationConfigUpdated":
                        loop.run_until_complete(self._handle_vectorization_config_updated(event_data))

                    elif event_type == "DocumentVectorizationPending":
                        loop.run_until_complete(self._handle_document_vectorization_pending(event_data))

                    elif event_type == "DocumentCreated":
                        loop.run_until_complete(self._handle_document_created(event_data))

                    else:
                        logger.warning("Unknown event type: %s", event_type)
                finally:
                    loop.close()

            # Execute in thread pool
            future = self._executor.submit(run_async_handler)
            future.result()  # Wait for completion

            # Acknowledge message (removes from queue)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug("Acknowledged message %s", method.delivery_tag)

        except Exception as e:
            logger.error("Error processing message: %s", e)

            # Reject and requeue message for retry
            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,  # Put back in queue for retry
            )

    async def _handle_document_fragment(self, event_data: dict[str, Any]) -> None:
        """Handle DocumentFragmentReceived event.

        Fragments are handled by activities, not workflows.
        This event is logged but doesn't trigger a workflow directly.

        Args:
            event_data: Deserialized event data

        """
        data = event_data["data"]
        document_id = data["document_id"]
        fragment_id = data["fragment_id"]
        sequence_number = data["sequence_number"]
        is_final = data.get("is_final", False)

        logger.info(
            "Fragment received for document %s: fragment %s, seq=%s, final=%s",
            document_id,
            fragment_id,
            sequence_number,
            is_final,
        )

    async def _handle_extracted_content(self, event_data: dict[str, Any]) -> None:
        """Handle ExtractedContentCreated event.

        ExtractedContent is processed by activities within workflows, not triggered directly.
        This event is logged for observability.

        Args:
            event_data: Deserialized event data

        """
        data = event_data["data"]
        document_id = data["document_id"]
        extracted_content_id = data["extracted_content_id"]
        modality = data["modality"]
        modality_sequence_number = data.get("modality_sequence_number", 0)

        logger.info(
            "ExtractedContent created for document %s: content_id=%s, modality=%s, seq=%s",
            document_id,
            extracted_content_id,
            modality,
            modality_sequence_number,
        )

    async def _handle_library_config_added(self, event_data: dict[str, Any]) -> None:
        """Handle LibraryConfigAdded event (no action - reprocessing not implemented).

        When a config is added to a library, documents would need to be processed
        with the new config, but this is not currently implemented.

        Args:
            event_data: Deserialized event data

        """
        data = event_data["data"]
        library_id = data["library_id"]
        config_id = data["config_id"]

        # Handle library_id being a dict or string
        if isinstance(library_id, dict):
            library_id = library_id.get("value", library_id)

        logger.info(
            "LibraryConfigAdded event received for library %s with config %s (no reprocessing workflow)",
            library_id,
            config_id,
        )

    async def _handle_document_vectorization_pending(self, event_data: dict[str, Any]) -> None:
        """Handle DocumentVectorizationPending event by triggering ProcessConfigWorkflow.

        This event is raised when:
        1. A config is added to a library (for all existing documents)
        2. A new document is uploaded (for all library configs)
        3. A config version is upgraded (auto-upgrade scenario)

        Args:
            event_data: Deserialized event data

        """
        data = event_data["data"]
        document_id = data["document_id"]
        config_id = data["config_id"]

        # Get library_id from event data - handle string or dict
        library_id = data.get("library_id")
        if isinstance(library_id, dict):
            library_id = library_id.get("value", library_id)

        logger.info(
            "Triggering ProcessConfigWorkflow for document %s with config %s",
            document_id,
            config_id,
        )

        try:
            # Start Temporal workflow for this document+config pair
            workflow_id = f"process-config-{document_id}-{config_id}"

            # Note: We need to fetch extracted_content_ids for this document
            # For now, we'll pass an empty list and the workflow will query them
            # TODO: Include extracted_content_ids in the event to avoid extra DB query

            handle = await self.temporal_client.start_workflow(
                ProcessConfigWorkflow.run,
                ProcessConfigWorkflowInput(
                    library_id=str(library_id),
                    document_id=str(document_id),
                    config_id=str(config_id),
                    extracted_content_ids=[],  # Workflow will query
                ),
                id=workflow_id,
                task_queue=self.task_queue,
            )

            logger.info("Started vectorization workflow %s, run_id=%s", workflow_id, handle.id)

        except Exception as e:
            logger.exception(
                "Failed to start vectorization workflow for document %s config %s: %s",
                document_id,
                config_id,
                e,
            )
            raise  # Re-raise to trigger message requeue

    async def _handle_library_config_removed(self, event_data: dict[str, Any]) -> None:
        """Handle LibraryConfigRemoved event.

        When a config is removed from a library, we log it for now.
        In the future, we might want to clean up vectorization data for that config.

        Args:
            event_data: Deserialized event data

        """
        data = event_data["data"]
        library_id = data["library_id"]
        config_id = data["config_id"]

        # Handle library_id being a dict or string
        if isinstance(library_id, dict):
            library_id = library_id.get("value", library_id)

        logger.info(
            "Config %s removed from library %s. Vectorization data cleanup may be needed.",
            config_id,
            library_id,
        )


    async def _handle_vectorization_config_updated(self, event_data: dict[str, Any]) -> None:
        """Handle VectorizationConfigUpdated event (no action - reprocessing not implemented).

        When a config is updated (new version), libraries using that config would
        need to reprocess their documents, but this is not currently implemented.

        Args:
            event_data: Deserialized event data

        """
        data = event_data["data"]
        config_id = data["config_id"]
        libraries = data.get("affected_library_ids", [])

        logger.info(
            "VectorizationConfigUpdated event received for config %s affecting %s libraries (no reprocessing workflow)",
            config_id,
            len(libraries),
        )

    async def _handle_document_created(self, event_data: dict[str, Any]) -> None:
        """Handle DocumentCreated event by triggering IngestDocumentWorkflow.

        When a document is created, trigger the full ingestion pipeline:
        1. Parse all fragments
        2. Process with all library configs

        Args:
            event_data: Deserialized event data

        """
        data = event_data["data"]
        document_id = data["document_id"]

        # Get library_id from event data - handle string or dict
        library_id = data.get("library_id")
        if isinstance(library_id, dict):
            library_id = library_id.get("value", library_id)

        logger.info("Triggering IngestDocumentWorkflow for document %s", document_id)

        try:
            workflow_id = f"ingest-{document_id}"

            handle = await self.temporal_client.start_workflow(
                IngestDocumentWorkflow.run,
                IngestDocumentWorkflowInput(
                    document_id=str(document_id),
                    library_id=str(library_id),
                ),
                id=workflow_id,
                task_queue=self.task_queue,
            )

            logger.info("Started ingestion workflow %s, run_id=%s", workflow_id, handle.id)

        except Exception as e:
            logger.exception("Failed to start ingestion workflow for document %s: %s", document_id, e)
            raise  # Re-raise to trigger message requeue

    def stop(self) -> None:
        """Stop consuming and close connection."""
        if self._channel:
            self._channel.stop_consuming()
        if self._connection:
            self._connection.close()
        logger.info("Consumer stopped")


class TemporalSearchConsumer:
    """Consumes search query events and triggers Temporal search workflows.

    Separate consumer for search operations, allowing independent scaling
    from ingestion workloads.
    """

    def __init__(
        self,
        rabbitmq_host: str,
        rabbitmq_port: int,
        queue_name: str,
        temporal_client: Client,
        task_queue: str,
    ) -> None:
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.queue_name = queue_name
        self.temporal_client = temporal_client
        self.task_queue = task_queue

        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self._executor = ThreadPoolExecutor(max_workers=10)

    def start(self) -> None:
        """Start consuming search query messages."""
        logger.info("Starting TemporalSearchConsumer for queue %s", self.queue_name)

        connection_params = pika.ConnectionParameters(
            host=self.rabbitmq_host,
            port=self.rabbitmq_port,
            credentials=pika.PlainCredentials("guest", "guest"),
            heartbeat=600,
        )

        self._connection = pika.BlockingConnection(connection_params)
        self._channel = self._connection.channel()

        # Declare exchange (idempotent - ensures it exists)
        self._channel.exchange_declare(
            exchange="vdb.events",
            exchange_type="topic",
            durable=True,
        )

        # Declare queue
        self._channel.queue_declare(queue=self.queue_name, durable=True)

        # Bind to search events
        self._channel.queue_bind(
            exchange="vdb.events",
            queue=self.queue_name,
            routing_key="search.*",
        )

        self._channel.basic_qos(prefetch_count=1)

        logger.info("Waiting for search queries on %s...", self.queue_name)
        self._channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._on_message,
            auto_ack=False,
        )

        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Search consumer stopped by user")
            self.stop()

    def _on_message(
        self,
        channel: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Handle search query message."""
        try:
            event_data = json.loads(body.decode("utf-8"))
            event_type = event_data["event_type"]

            logger.info("Received search event: %s", event_type)

            # Run async handler in a thread pool to avoid event loop conflicts
            def run_async_handler():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    if event_type == "SearchQueryCreated":
                        loop.run_until_complete(self._handle_search_query(event_data))
                finally:
                    loop.close()

            # Execute in thread pool
            future = self._executor.submit(run_async_handler)
            future.result()  # Wait for completion

            channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error("Error processing search query: %s", e)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def _handle_search_query(self, event_data: dict[str, Any]) -> None:
        """Trigger SearchWorkflow in Temporal."""
        data = event_data["data"]
        query_id = data["query_id"]

        logger.info("Triggering search workflow for query %s", query_id)

        workflow_id = f"search-{query_id}"

        # Get library_id from event data
        library_id = data.get("library_id")
        if isinstance(library_id, dict):
            library_id = library_id.get("value", library_id)

        handle = await self.temporal_client.start_workflow(
            SearchWorkflow.run,
            SearchWorkflowInput(
                library_id=str(library_id),
                query_text=data["query_text"],
                top_k=data.get("top_k", 10),
                strategy=data.get("strategy", "cosine"),
            ),
            id=workflow_id,
            task_queue=self.task_queue,
        )

        logger.info("Started search workflow %s, run_id=%s", workflow_id, handle.id)

    def stop(self) -> None:
        """Stop consuming and close connection."""
        if self._channel:
            self._channel.stop_consuming()
        if self._connection:
            self._connection.close()
        logger.info("Search consumer stopped")


async def main() -> None:
    """Start both ingestion and search consumers (or run separately)."""
    # Get config from environment
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")

    # Connect to Temporal
    temporal_address = f"{temporal_host}:{temporal_port}"
    temporal_client = await Client.connect(
        temporal_address,
        namespace=temporal_namespace,
    )

    logger.info("Connected to Temporal at %s", temporal_address)

    # Determine which consumer to run
    consumer_type = os.getenv("CONSUMER_TYPE", "ingestion")

    if consumer_type == "ingestion":
        consumer = TemporalIngestionConsumer(
            rabbitmq_host=rabbitmq_host,
            rabbitmq_port=rabbitmq_port,
            queue_name="workflow_events",
            temporal_client=temporal_client,
            task_queue="vdb-tasks",
        )
        consumer.start()

    elif consumer_type == "search":
        consumer = TemporalSearchConsumer(
            rabbitmq_host=rabbitmq_host,
            rabbitmq_port=rabbitmq_port,
            queue_name="search_query_events",
            temporal_client=temporal_client,
            task_queue="vdb-search-tasks",
        )
        consumer.start()

    else:
        logger.error("Unknown consumer type: %s", consumer_type)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
