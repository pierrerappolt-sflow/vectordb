"""Event log consumer - Infrastructure layer.

Logs all pipeline events to PostgreSQL for monitoring and debugging.
Writes directly to DB - no use case needed (not business logic).

Clean Architecture:
- This is pure infrastructure - observability/monitoring
- NOT a business use case
- Subscribes to ALL events via wildcard routing key
- Independent from pipeline - failures don't affect processing
"""

import asyncio
import json
import logging
import os
import threading
from datetime import UTC, datetime

import pika
from pika.adapters.blocking_connection import BlockingChannel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from vdb_core.infrastructure.message_bus.rabbitmq_message_bus import ExchangeType

logger = logging.getLogger(__name__)


class EventLogConsumer:
    """Infrastructure consumer: Logs all pipeline events to PostgreSQL.

    Binds to wildcard routing key (#) to capture everything.
    Direct SQL writes for performance - no ORM overhead.
    """

    def __init__(self, rabbitmq_host: str, rabbitmq_port: int, database_url: str) -> None:
        """Initialize event log consumer.

        Args:
            rabbitmq_host: RabbitMQ server hostname
            rabbitmq_port: RabbitMQ server port
            database_url: PostgreSQL connection URL

        """
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.database_url = database_url
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

    def start(self) -> None:
        """Start consuming all events."""
        logger.info("Starting EventLogConsumer (Infrastructure - Observability)")

        connection_params = pika.ConnectionParameters(
            host=self.rabbitmq_host,
            port=self.rabbitmq_port,
            credentials=pika.PlainCredentials("guest", "guest"),
            heartbeat=600,
        )

        self._connection = pika.BlockingConnection(connection_params)
        self._channel = self._connection.channel()

        # Declare exchange (must match publisher's exchange name)
        self._channel.exchange_declare(
            exchange="vdb.events",
            exchange_type=ExchangeType.topic,
            durable=True,
        )

        # Declare queue
        self._channel.queue_declare(queue="event_logs", durable=True)

        # Bind to ALL events using wildcard
        # This captures every event published to vdb.events exchange
        self._channel.queue_bind(
            exchange="vdb.events",
            queue="event_logs",
            routing_key="#",  # Wildcard - matches ALL routing keys!
        )

        # High prefetch for logging throughput
        self._channel.basic_qos(prefetch_count=50)

        logger.info("Listening for ALL events on 'vdb.events' exchange (routing_key=#)")
        self._channel.basic_consume(
            queue="event_logs",
            on_message_callback=self._on_message,
            auto_ack=False,
        )

        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("EventLogConsumer stopped by user")
            self.stop()

    def _on_message(
        self,
        channel: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        _properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Log event to PostgreSQL."""
        try:
            event_data = json.loads(body.decode("utf-8"))
            routing_key = method.routing_key

            # Write to database - run async code in a thread to avoid event loop conflicts
            def run_async() -> None:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Create engine and session in this thread's event loop
                    engine = create_async_engine(self.database_url, echo=False, pool_pre_ping=True)
                    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

                    async def write_and_cleanup() -> None:
                        try:
                            await self._write_event_log(event_data, routing_key, async_session)
                        finally:
                            await engine.dispose()

                    loop.run_until_complete(write_and_cleanup())
                finally:
                    loop.close()

            thread = threading.Thread(target=run_async)
            thread.start()
            thread.join(timeout=10)  # 10 second timeout

            # Always ack - logging failures shouldn't block pipeline
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception:
            logger.exception("Error logging event")
            # Don't requeue - logging failures shouldn't retry forever
            channel.basic_ack(delivery_tag=method.delivery_tag)

    async def _write_event_log(
        self, event_data: dict, routing_key: str, async_session: sessionmaker[AsyncSession]
    ) -> None:
        """Write event to event_logs table via direct SQL."""
        async with async_session() as session:
            try:
                # Extract common fields from event payload
                data = event_data.get("data", {})

                # Extract IDs (handle both plain strings and value objects)
                document_id_data = data.get("document_id")
                library_id_data = data.get("library_id")

                document_id = (
                    (document_id_data.get("value") if isinstance(document_id_data, dict) else document_id_data)
                    if document_id_data
                    else None
                )

                library_id = (
                    (library_id_data.get("value") if isinstance(library_id_data, dict) else library_id_data)
                    if library_id_data
                    else None
                )

                # Infer pipeline stage from routing key
                pipeline_stage = self._infer_stage(routing_key)

                # Parse timestamp
                timestamp_str = event_data.get("timestamp")
                timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now(UTC)

                # Direct SQL insert (fastest - no ORM overhead)
                stmt = text("""
                    INSERT INTO event_logs (
                        event_type, event_id, timestamp, routing_key,
                        data, document_id, library_id, pipeline_stage
                    ) VALUES (
                        :event_type, :event_id, :timestamp, :routing_key,
                        CAST(:data AS jsonb), :document_id, :library_id, :pipeline_stage
                    )
                """)

                await session.execute(
                    stmt,
                    {
                        "event_type": event_data.get("event_type", "Unknown"),
                        "event_id": event_data.get("event_id"),
                        "timestamp": timestamp,
                        "routing_key": routing_key,
                        "data": json.dumps(data),
                        "document_id": document_id,
                        "library_id": library_id,
                        "pipeline_stage": pipeline_stage,
                    },
                )

                await session.commit()

            except Exception:
                logger.exception("Failed to write event log")
                await session.rollback()

    def _infer_stage(self, routing_key: str) -> str | None:
        """Infer pipeline stage from RabbitMQ routing key."""
        stage_map = {
            "document.fragment.received": "upload",
            "pipeline.decoded": "decode",
            "pipeline.chunked": "chunk",
            "pipeline.embedded": "embed",
            "pipeline.indexed": "index",
        }
        return stage_map.get(routing_key)

    def stop(self) -> None:
        """Stop consumer and close connections."""
        logger.info("Stopping EventLogConsumer...")
        if self._channel:
            self._channel.stop_consuming()
        if self._connection:
            self._connection.close()
        # No need to dispose engine - each thread creates and disposes its own


async def main() -> None:
    """Start event log consumer."""
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))

    # Convert DATABASE_URL to async driver if needed
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    logger.info("=" * 80)
    logger.info("Event Log Consumer - Infrastructure Layer (Observability)")
    logger.info("RabbitMQ: %s:%s", rabbitmq_host, rabbitmq_port)
    logger.info("Database: %s", database_url.split("@")[1] if "@" in database_url else "N/A")
    logger.info("=" * 80)

    consumer = EventLogConsumer(rabbitmq_host, rabbitmq_port, database_url)
    consumer.start()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
