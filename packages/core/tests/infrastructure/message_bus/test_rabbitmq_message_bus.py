"""Tests for RabbitMQMessageBus."""

from typing import cast
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from vdb_core.domain.events import DocumentCreated, DocumentFragmentReceived, DomainEvent
from vdb_core.domain.value_objects import (
    DocumentName,
)
from vdb_core.infrastructure.message_bus import RabbitMQMessageBus


@pytest.mark.asyncio
class TestRabbitMQMessageBus:
    """Tests for RabbitMQMessageBus."""

    @patch("vdb_core.infrastructure.message_bus.rabbitmq_message_bus.pika")
    async def test_handle_events_publishes_to_rabbitmq(self, mock_pika: MagicMock) -> None:
        """Test that handle_events publishes events to RabbitMQ."""
        # Arrange
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_connection.is_closed = False

        bus = RabbitMQMessageBus(host="localhost", port=5672)

        events = [
            DocumentCreated(
                document_id=uuid4(),
                library_id=uuid4(),
                name=DocumentName("Test"),
            ),
        ]

        # Act
        await bus.handle_events(cast("list[DomainEvent]", events))

        # Assert
        assert mock_channel.basic_publish.call_count == 1
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]["exchange"] == "vdb.events"
        assert call_args[1]["routing_key"] == "document.created"

    @patch("vdb_core.infrastructure.message_bus.rabbitmq_message_bus.pika")
    async def test_handle_events_with_empty_list(self, mock_pika: MagicMock) -> None:
        """Test handling empty event list doesn't publish."""
        # Arrange
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_connection.is_closed = False

        bus = RabbitMQMessageBus(host="localhost", port=5672)

        # Act
        await bus.handle_events([])

        # Assert
        assert mock_channel.basic_publish.call_count == 0

    @patch("vdb_core.infrastructure.message_bus.rabbitmq_message_bus.pika")
    async def test_handle_events_uses_correct_routing_keys(self, mock_pika: MagicMock) -> None:
        """Test that different event types use correct routing keys."""
        # Arrange
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_connection.is_closed = False

        bus = RabbitMQMessageBus(host="localhost", port=5672)

        document_id = uuid4()
        library_id = uuid4()

        events = [
            DocumentCreated(
                document_id=document_id,
                library_id=library_id,
                name=DocumentName("Test"),
            ),
            DocumentFragmentReceived(
                library_id=library_id,
                document_id=document_id,
                fragment_id=uuid4(),
                sequence_number=0,
                is_final=False,
            ),
        ]

        # Act
        await bus.handle_events(events)

        # Assert
        assert mock_channel.basic_publish.call_count == 2

        # Check first event (DocumentCreated)
        first_call = mock_channel.basic_publish.call_args_list[0]
        assert first_call[1]["routing_key"] == "document.created"

        # Check second event (DocumentFragmentReceived)
        second_call = mock_channel.basic_publish.call_args_list[1]
        assert second_call[1]["routing_key"] == "document.fragment.received"

    @patch("vdb_core.infrastructure.message_bus.rabbitmq_message_bus.pika")
    async def test_serialize_event_converts_value_objects(self, mock_pika: MagicMock) -> None:
        """Test that value objects are properly serialized to primitives."""
        # Arrange
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_connection.is_closed = False

        bus = RabbitMQMessageBus(host="localhost", port=5672)

        document_id = uuid4()
        library_id = uuid4()

        events = [
            DocumentCreated(
                document_id=document_id,
                library_id=library_id,
                name=DocumentName("Test"),
            ),
        ]

        # Act
        await bus.handle_events(cast("list[DomainEvent]", events))

        # Assert
        assert mock_channel.basic_publish.call_count == 1
        call_args = mock_channel.basic_publish.call_args
        body = call_args[1]["body"]

        # Verify body is JSON with primitives (no value objects)
        import json

        event_data = json.loads(body.decode("utf-8"))
        assert event_data["event_type"] == "DocumentCreated"
        assert event_data["data"]["document_id"] == str(document_id)
        assert event_data["data"]["library_id"] == str(library_id)
        assert event_data["data"]["name"] == "Test"

    @patch("vdb_core.infrastructure.message_bus.rabbitmq_message_bus.pika")
    def test_connection_failure_raises_exception(self, mock_pika: MagicMock) -> None:
        """Test that connection failures raise appropriate exceptions."""
        # Arrange
        from pika.exceptions import AMQPConnectionError

        mock_pika.BlockingConnection.side_effect = AMQPConnectionError("Connection failed")

        # Act & Assert
        with pytest.raises(AMQPConnectionError):
            RabbitMQMessageBus(host="invalid-host", port=5672)

    @patch("vdb_core.infrastructure.message_bus.rabbitmq_message_bus.pika")
    async def test_publish_failure_raises_exception(self, mock_pika: MagicMock) -> None:
        """Test that publish failures raise exceptions."""
        # Arrange
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_connection.is_closed = False

        # Make basic_publish raise an exception
        mock_channel.basic_publish.side_effect = Exception("Publish failed")

        bus = RabbitMQMessageBus(host="localhost", port=5672)

        events = [
            DocumentCreated(
                document_id=uuid4(),
                library_id=uuid4(),
                name=DocumentName("Test"),
            ),
        ]

        # Act & Assert
        with pytest.raises(Exception, match="Publish failed"):
            await bus.handle_events(cast("list[DomainEvent]", events))

    @patch("vdb_core.infrastructure.message_bus.rabbitmq_message_bus.pika")
    def test_close_connection(self, mock_pika: MagicMock) -> None:
        """Test that close() properly closes the connection."""
        # Arrange
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_connection.is_closed = False

        bus = RabbitMQMessageBus(host="localhost", port=5672)

        # Act
        bus.close()

        # Assert
        mock_connection.close.assert_called_once()
