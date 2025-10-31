"""Exception handlers for mapping domain and application exceptions to HTTP responses.

Exception Mapping Strategy:
    - EntityNotFoundError → 404 NOT FOUND
    - ValidationException → 422 UNPROCESSABLE ENTITY (domain rule violations)
    - ValidationError (Pydantic) → 422 UNPROCESSABLE ENTITY (input validation)
    - UnsupportedModalityError → 400 BAD REQUEST
    - TransactionError → 500 INTERNAL SERVER ERROR
    - ApplicationException → 500 INTERNAL SERVER ERROR (use case failures)
    - DomainException → 500 INTERNAL SERVER ERROR (catch-all)
    - Exception → 500 INTERNAL SERVER ERROR (unexpected errors)

Following DDD principles:
    - Presentation layer handles HTTP concerns (status codes, response format)
    - Domain exceptions remain pure (no HTTP coupling)
    - Clear mapping between domain concepts and HTTP semantics
"""

import logging
from typing import Any, TypedDict

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic_core import ValidationError
from vdb_core.application.exceptions import ApplicationException
from vdb_core.domain.exceptions import (
    DomainException,
    EntityNotFoundError,
    TransactionError,
    UnsupportedModalityError,
    ValidationException,
)

logger = logging.getLogger(__name__)


class ErrorResponse(TypedDict, total=False):
    """Type-safe error response structure.

    Uses Python 3.13 TypedDict for type safety without runtime overhead.
    """

    detail: str
    type: str
    entity_type: str
    entity_id: str
    errors: list[dict[str, Any]]
    details: dict[str, object]


async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
    """Handle EntityNotFoundError (LibraryNotFoundError, DocumentNotFoundError, etc.).

    Maps to 404 NOT FOUND.

    Args:
        request: FastAPI request object
        exc: The entity not found exception

    Returns:
        JSON response with 404 status code
    """
    logger.warning(f"Entity not found: {exc.entity_type} {exc.entity_id} - {exc.message}")
    error: ErrorResponse = {
        "detail": exc.message,
        "entity_type": exc.entity_type,
        "entity_id": exc.entity_id,
    }
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error)


async def validation_exception_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """Handle domain ValidationException.

    Maps to 422 UNPROCESSABLE_CONTENT.

    Args:
        request: FastAPI request object
        exc: The validation exception

    Returns:
        JSON response with 422 status code
    """
    logger.error(f"Validation error on {request.method} {request.url.path}: {exc.message}")
    error: ErrorResponse = {
        "detail": exc.message,
        "type": "validation_error",
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=error)


async def pydantic_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic ValidationError (from value objects).

    Maps to 422 UNPROCESSABLE_CONTENT.

    Args:
        request: FastAPI request object
        exc: The Pydantic validation error

    Returns:
        JSON response with 422 status code
    """
    logger.error(f"Pydantic validation error on {request.method} {request.url.path}: {exc.errors()}")
    error: ErrorResponse = {
        "detail": "Validation error",
        "type": "pydantic_validation_error",
        "errors": exc.errors(),
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=error)


async def unsupported_modality_handler(request: Request, exc: UnsupportedModalityError) -> JSONResponse:
    """Handle UnsupportedModalityError.

    Maps to 400 BAD REQUEST.

    Args:
        request: FastAPI request object
        exc: The unsupported modality exception

    Returns:
        JSON response with 400 status code
    """
    logger.warning(f"Unsupported modality on {request.method} {request.url.path}: {exc.message}")
    error: ErrorResponse = {
        "detail": exc.message,
        "type": "unsupported_modality",
    }
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=error)


async def application_exception_handler(request: Request, exc: ApplicationException) -> JSONResponse:
    """Handle ApplicationException (use case failures).

    Maps to 500 INTERNAL_SERVER_ERROR.

    Args:
        request: FastAPI request object
        exc: The application exception

    Returns:
        JSON response with 500 status code
    """
    logger.error(
        f"Application error on {request.method} {request.url.path}: {exc.message}", extra={"details": exc.details}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": exc.message,
            "type": "application_error",
            "details": exc.details,
        },
    )


async def transaction_error_handler(request: Request, exc: TransactionError) -> JSONResponse:
    """Handle TransactionError.

    Maps to 500 INTERNAL_SERVER_ERROR.

    Args:
        request: FastAPI request object
        exc: The transaction error

    Returns:
        JSON response with 500 status code
    """
    logger.error(f"Transaction error on {request.method} {request.url.path}: {exc.message}")
    error: ErrorResponse = {
        "detail": exc.message,
        "type": "transaction_error",
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error)


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Handle generic DomainException (catch-all for unhandled domain exceptions).

    Maps to 500 INTERNAL_SERVER_ERROR.

    Args:
        request: FastAPI request object
        exc: The domain exception

    Returns:
        JSON response with 500 status code
    """
    logger.error(f"Domain error on {request.method} {request.url.path}: {exc.message}")
    error: ErrorResponse = {
        "detail": exc.message,
        "type": "domain_error",
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Maps to 500 INTERNAL_SERVER_ERROR.

    Note: Does not expose exception details in production for security.

    Args:
        request: FastAPI request object
        exc: The unexpected exception

    Returns:
        JSON response with 500 status code
    """
    logger.exception(f"Unexpected error on {request.method} {request.url.path}: {exc}")
    error: ErrorResponse = {
        "detail": "Internal server error",
        "type": "unexpected_error",
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error)
