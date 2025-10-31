"""Tests for exception handlers."""

import pytest
from fastapi import status
from vdb_core.application.exceptions import ApplicationException
from vdb_core.domain.exceptions import (
    DomainException,
    LibraryNotFoundError,
    TransactionError,
    UnsupportedModalityError,
    ValidationException,
)

from vdb_api.presentation import exception_handlers


@pytest.mark.asyncio
async def test_entity_not_found_handler():
    """Test EntityNotFoundError returns 404."""
    exc = LibraryNotFoundError("123e4567-e89b-12d3-a456-426614174000")

    response = await exception_handlers.entity_not_found_handler(None, exc)  # type: ignore[arg-type]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    content = response.body.decode()
    assert "Library" in content
    assert "123e4567-e89b-12d3-a456-426614174000" in content


@pytest.mark.asyncio
async def test_validation_exception_handler():
    """Test ValidationException returns 422."""
    exc = ValidationException("Invalid document status")

    response = await exception_handlers.validation_exception_handler(None, exc)  # type: ignore[arg-type]

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    content = response.body.decode()
    assert "Invalid document status" in content


@pytest.mark.asyncio
async def test_unsupported_modality_handler():
    """Test UnsupportedModalityError returns 400."""
    exc = UnsupportedModalityError("image", "text")

    response = await exception_handlers.unsupported_modality_handler(None, exc)  # type: ignore[arg-type]

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    content = response.body.decode()
    assert "image" in content


@pytest.mark.asyncio
async def test_application_exception_handler():
    """Test ApplicationException returns 500."""
    exc = ApplicationException("Use case failed", details={"reason": "test"})

    response = await exception_handlers.application_exception_handler(None, exc)  # type: ignore[arg-type]

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    content = response.body.decode()
    assert "Use case failed" in content
    assert "test" in content


@pytest.mark.asyncio
async def test_transaction_error_handler():
    """Test TransactionError returns 500."""
    exc = TransactionError("Database deadlock")

    response = await exception_handlers.transaction_error_handler(None, exc)  # type: ignore[arg-type]

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_domain_exception_handler():
    """Test generic DomainException returns 500."""
    exc = DomainException("Unknown domain error")

    response = await exception_handlers.domain_exception_handler(None, exc)  # type: ignore[arg-type]

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    content = response.body.decode()
    assert "Unknown domain error" in content


@pytest.mark.asyncio
async def test_general_exception_handler():
    """Test unexpected Exception returns 500."""
    exc = Exception("Unexpected error")

    response = await exception_handlers.general_exception_handler(None, exc)  # type: ignore[arg-type]

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    content = response.body.decode()
    assert "Internal server error" in content
