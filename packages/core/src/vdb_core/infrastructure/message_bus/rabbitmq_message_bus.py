"""RabbitMQ-based message bus for publishing domain events."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any

import pika
from pika.exceptions import AMQPConnectionError
from pika.exchange_type import ExchangeType

from vdb_core.application.message_bus import IMessageBus

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel

    from vdb_core.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class RabbitMQMessageBus(IMessageBus):
    """RabbitMQ-based event bus for publishing domain events.

    Publishes events to RabbitMQ topic exchange which routes to multiple queues
    based on routing keys (event types). This decouples the API from consumers
    like Temporal workers, analytics services, webhooks, etc.

    Exchange Topology:
        Exchange: vdb.events (topic)
        ├─→ Queue: document_events (routing: document.*)
        │   └─→ Consumed by: TemporalIngestionConsumer
        │
        ├─→ Queue: search_query_events (routing: search.*)
        │   └─→ Consumed by: TemporalSearchConsumer
        │
        └─→ Queue: analytics_events (routing: #)
            └─→ Consumed by: AnalyticsService

    Event Format (JSON):
        {
            "event_type": "DocumentFragmentReceived",
            "event_id": "01234567-89ab-cdef-0123-456789abcdef",
            "timestamp": "2025-10-26T10:30:00.123456Z",
            "data": {
                "document_id": "...",
                "library_id": "...",
                "sequence_number": 0,
                ...
            }
        }

    Usage:
        # In use case
        message_bus = RabbitMQMessageBus(
            host="localhost",
            port=5672,
            exchange_name="vdb.events"
        )

        async with uow:
            library.add_document(...)
            events = await uow.commit()

        # Publish to RabbitMQ
        await message_bus.handle_events(events)
    """

    # Routing key mapping: event type → routing key
    ROUTING_KEYS = {
        # Document lifecycle events
        "DocumentCreated": "document.created",
        "DocumentFragmentReceived": "document.fragment.received",
        "DocumentProcessingCompleted": "document.processing.completed",
        # Search events
        "SearchQueryCreated": "search.query.created",
        "SearchQueryCompleted": "search.query.completed",
        # Pipeline stage events
        "FragmentDecoded": "pipeline.decoded",
        "FragmentChunked": "pipeline.chunked",
        "ChunksEmbedded": "pipeline.embedded",
        "EmbeddingsIndexed": "pipeline.indexed",
        # Library config events
        "LibraryConfigAdded": "library.config.added",
        "LibraryConfigRemoved": "library.config.removed",
        # Vectorization config lifecycle events
        "VectorizationConfigCreated": "config.created",
        "VectorizationConfigVersionCreated": "config.version.created",
        "VectorizationConfigStatusChanged": "config.status.changed",
        # Document vectorization events
        "DocumentVectorizationPending": "vectorization.pending",
        "DocumentVectorizationCompleted": "vectorization.completed",
        "DocumentVectorizationFailed": "vectorization.failed",
        # Extracted content events
        "ExtractedContentCreated": "content.extracted",
    }

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        virtual_host: str = "/",
        exchange_name: str = "vdb.events",
        exchange_type: str = "topic",
    ) -> None:
        """Initialize RabbitMQ connection and declare exchange.

        Args:
            host: RabbitMQ host
            port: RabbitMQ port (default: 5672)
            username: RabbitMQ username
            password: RabbitMQ password
            virtual_host: RabbitMQ virtual host
            exchange_name: Exchange name for event publishing
            exchange_type: Exchange type (topic, fanout, direct)

        """
        self.host = host
        self.port = port
        self.credentials = pika.PlainCredentials(username, password)
        self.virtual_host = virtual_host
        self.exchange_name = exchange_name
        # Convert string to ExchangeType enum for pika
        self.exchange_type = ExchangeType(exchange_type)

        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

        # Connect and declare exchange
        self._ensure_connection()

    def _ensure_connection(self) -> None:
        """Ensure RabbitMQ connection is established."""
        if self._connection and not self._connection.is_closed:
            return

        try:
            # Create connection
            connection_params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=self.credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )

            self._connection = pika.BlockingConnection(connection_params)
            self._channel = self._connection.channel()

            # Declare exchange (idempotent)
            self._channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type=self.exchange_type,
                durable=True,  # Survive broker restart
                auto_delete=False,
            )

            logger.info("Connected to RabbitMQ at %s:%s, exchange=%s", self.host, self.port, self.exchange_name)

        except AMQPConnectionError as e:
            logger.exception("Failed to connect to RabbitMQ: %s", e)
            raise

    async def handle_events(self, events: list[DomainEvent]) -> None:
        """Publish domain events to RabbitMQ exchange.

        Each event is serialized to JSON and published with a routing key
        based on event type. Consumers can subscribe to specific event types
        by binding queues with matching routing patterns.

        Args:
            events: List of domain events to publish

        Raises:
            AMQPConnectionError: If RabbitMQ connection fails

        """
        if not events:
            return

        self._ensure_connection()

        # Ensure channel is available after connection
        if self._channel is None:
            msg = "RabbitMQ channel not initialized"
            raise RuntimeError(msg)

        for event in events:
            try:
                # Serialize event to JSON
                message = self._serialize_event(event)
                routing_key = self._get_routing_key(event)

                # Publish to exchange
                self._channel.basic_publish(
                    exchange=self.exchange_name,
                    routing_key=routing_key,
                    body=message.encode("utf-8"),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent message
                        content_type="application/json",
                        content_encoding="utf-8",
                        message_id=str(event.event_id),
                        timestamp=int(event.occurred_at.timestamp()),
                    ),
                )

                logger.debug(
                    "Published event %s to %s with routing key %s",
                    event.__class__.__name__,
                    self.exchange_name,
                    routing_key,
                )

            except Exception as e:
                logger.exception("Failed to publish event %s: %s", event.__class__.__name__, e)
                # Re-raise to fail the request (ensures at-least-once delivery)
                raise

    def _serialize_event(self, event: DomainEvent) -> str:
        """Serialize domain event to JSON string.

        Handles conversion of value objects to primitive types.

        Args:
            event: Domain event to serialize

        Returns:
            JSON string representation

        """
        # Convert dataclass to dict
        event_dict = asdict(event)

        # Remove base event fields (event_id, occurred_at) since we handle them separately
        event_dict.pop("event_id", None)
        event_dict.pop("occurred_at", None)

        # Convert value objects to primitives
        data = self._convert_value_objects(event_dict)

        return json.dumps(
            {
                "event_type": event.__class__.__name__,
                "event_id": str(event.event_id),
                "timestamp": event.occurred_at.isoformat(),
                "data": data,
            }
        )

    def _convert_value_objects(self, obj: Any) -> Any:
        """Recursively convert value objects to primitive types.

        Args:
            obj: Object to convert (can be dict, list, value object, etc.)

        Returns:
            Converted object with primitives only

        """
        from datetime import datetime
        from uuid import UUID

        if obj is None:
            return None

        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Handle UUID objects
        if isinstance(obj, UUID):
            return str(obj)

        # Handle value objects that got converted to dicts by asdict()
        # E.g., UUID(UUID(...)) becomes {"value": UUID(...)}
        if isinstance(obj, dict) and len(obj) == 1 and "value" in obj:
            return self._convert_value_objects(obj["value"])

        # Handle dictionaries
        if isinstance(obj, dict):
            return {key: self._convert_value_objects(value) for key, value in obj.items()}

        # Handle lists/tuples
        if isinstance(obj, (list, tuple)):
            return [self._convert_value_objects(item) for item in obj]

        # Handle value objects with .value attribute (before asdict)
        if hasattr(obj, "value"):
            # Recursively convert in case value is also a complex object
            return self._convert_value_objects(obj.value)

        # Handle dataclasses (shouldn't happen at top level, but be defensive)
        if is_dataclass(obj) and not isinstance(obj, type):
            return self._convert_value_objects(asdict(obj))

        # Primitives (str, int, float, bool) - return as-is
        return obj

    def _get_routing_key(self, event: DomainEvent) -> str:
        """Get routing key for event type.

        Args:
            event: Domain event

        Returns:
            Routing key string (e.g., "document.fragment.received")

        """
        event_type = event.__class__.__name__
        return self.ROUTING_KEYS.get(event_type, "event.unknown")

    def close(self) -> None:
        """Close RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("Closed RabbitMQ connection")
