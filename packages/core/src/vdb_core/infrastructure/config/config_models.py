"""Configuration models for VDB infrastructure."""

from enum import Enum

from pydantic import BaseModel, Field


class StorageType(str, Enum):
    """Available storage backend types."""

    INMEMORY = "inmemory"
    DUCKDB = "duckdb"
    POSTGRES = "postgres"


class MessageBusType(str, Enum):
    """Available message bus types."""

    INMEMORY = "inmemory"
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"


class ReadModelType(str, Enum):
    """Available read model storage types."""

    INMEMORY = "inmemory"
    DUCKDB = "duckdb"
    POSTGRES = "postgres"
    REDIS = "redis"


class StorageConfig(BaseModel):
    """Storage backend configuration."""

    type: StorageType = Field(default=StorageType.INMEMORY, description="Storage backend type")
    database_url: str | None = Field(default=None, description="Database connection URL")
    pool_size: int = Field(default=10, description="Connection pool size")


class MessageBusConfig(BaseModel):
    """Message bus configuration."""

    type: MessageBusType = Field(default=MessageBusType.INMEMORY, description="Message bus type")
    broker_url: str | None = Field(default=None, description="Message broker URL")


class ReadModelConfig(BaseModel):
    """Read model storage configuration."""

    type: ReadModelType = Field(default=ReadModelType.INMEMORY, description="Read model storage type")
    database_url: str | None = Field(default=None, description="Database connection URL")


class InfrastructureConfig(BaseModel):
    """Infrastructure layer configuration."""

    storage: StorageConfig = Field(default_factory=StorageConfig)
    message_bus: MessageBusConfig = Field(default_factory=MessageBusConfig)
    read_models: ReadModelConfig = Field(default_factory=ReadModelConfig)


class ApplicationConfig(BaseModel):
    """Application layer configuration."""

    shared_read_write_storage: bool = Field(
        default=True, description="Whether to use same storage for reads and writes"
    )


class ApiConfig(BaseModel):
    """API configuration."""

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    log_level: str = Field(default="info", description="Logging level")


class AppConfig(BaseModel):
    """Root configuration model."""

    infrastructure: InfrastructureConfig = Field(default_factory=InfrastructureConfig)
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)

    def get_storage_type(self) -> StorageType:
        """Get the storage backend type."""
        return self.infrastructure.storage.type

    def get_message_bus_type(self) -> MessageBusType:
        """Get the message bus type."""
        return self.infrastructure.message_bus.type

    def get_read_model_type(self) -> ReadModelType | StorageType:
        """Get the read model storage type.

        If shared_read_write_storage is True, returns the storage type.
        Otherwise, returns the read_models type.
        """
        if self.application.shared_read_write_storage:
            return self.infrastructure.storage.type
        return self.infrastructure.read_models.type
