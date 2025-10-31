"""FastAPI application entry point."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_core import ValidationError
from temporalio.client import Client
from vdb_core.application.exceptions import ApplicationException
from vdb_core.domain.exceptions import (
    DomainException,
    EntityNotFoundError,
    TransactionError,
    UnsupportedModalityError,
    ValidationException,
)

from .infrastructure import DIContainer
from .presentation import exception_handlers
from .presentation.routers import configs_router, events_router, libraries_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Startup: Initialize DI container
    container = DIContainer()
    app.state.container = container

    # Startup: Bootstrap default configs
    from vdb_core.infrastructure.bootstrap import DefaultConfigsBootstrap

    bootstrap = DefaultConfigsBootstrap(uow_factory=container.get_unit_of_work)
    await bootstrap.bootstrap_default_configs()

    # Startup: Connect to Temporal (optional for local development)
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost")
    temporal_port = os.getenv("TEMPORAL_PORT", "7233")
    temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")

    try:
        temporal_client = await Client.connect(
            f"{temporal_host}:{temporal_port}",
            namespace=temporal_namespace,
        )
        app.state.temporal_client = temporal_client
    except Exception as e:
        # Temporal not available - API will work without workflow capabilities
        print(f"Warning: Could not connect to Temporal at {temporal_host}:{temporal_port}: {e}")
        app.state.temporal_client = None

    yield

    # Shutdown: Clean up resources
    # Note: Temporal Python SDK client doesn't need explicit close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Vector Database API",
        description="High-performance document processing and vector storage API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS - allow all origins for development
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r".*",  # Allow all origins using regex
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )

    # Register exception handlers (specific to general)
    # Order matters: more specific exceptions first, then more general
    app.add_exception_handler(EntityNotFoundError, exception_handlers.entity_not_found_handler)
    app.add_exception_handler(ValidationException, exception_handlers.validation_exception_handler)
    app.add_exception_handler(ValidationError, exception_handlers.pydantic_validation_error_handler)
    app.add_exception_handler(UnsupportedModalityError, exception_handlers.unsupported_modality_handler)
    app.add_exception_handler(ApplicationException, exception_handlers.application_exception_handler)
    app.add_exception_handler(TransactionError, exception_handlers.transaction_error_handler)
    app.add_exception_handler(DomainException, exception_handlers.domain_exception_handler)
    app.add_exception_handler(Exception, exception_handlers.general_exception_handler)

    # Register routers
    app.include_router(libraries_router)
    app.include_router(events_router)
    app.include_router(configs_router)

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring and e2e tests."""
        return {"status": "healthy"}

    return app


# Create app instance for ASGI servers (uvicorn, gunicorn, etc.)
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "vdb_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
