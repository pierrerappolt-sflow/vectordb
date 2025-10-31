"""Integration tests for API endpoints."""

import io

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from vdb_api.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client with lifespan context."""
    app = create_app()
    # TestClient automatically handles the lifespan context
    with TestClient(app) as test_client:
        yield test_client


def test_get_libraries_empty(client: TestClient) -> None:
    """Test getting libraries when none exist."""
    response = client.get("/libraries")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["libraries"] == []
    assert data["total"] == 0
    assert data["limit"] == 100
    assert data["offset"] == 0


def test_create_library(client: TestClient) -> None:
    """Test creating a library."""
    response = client.post(
        "/libraries",
        json={"name": "Test Library"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert "library" in data
    assert data["library"]["name"] == "Test Library"
    assert data["library"]["status"] == "active"  # LibraryStatusEnum.ACTIVE.value
    assert "id" in data["library"]
    assert "created_at" in data["library"]
    assert "updated_at" in data["library"]
    assert data["library"]["document_count"] == 0
    assert data["message"] == "Library created successfully"


def test_create_library_empty_name(client: TestClient) -> None:
    """Test that empty name returns validation error."""
    response = client.post("/libraries", json={"name": ""})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()
    assert "detail" in error


def test_create_library_name_too_long(client: TestClient) -> None:
    """Test that name longer than 255 characters returns validation error."""
    long_name = "a" * 256
    response = client.post("/libraries", json={"name": long_name})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()
    assert "detail" in error


def test_create_library_missing_name(client: TestClient) -> None:
    """Test that missing name field returns validation error."""
    response = client.post("/libraries", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()
    assert "detail" in error


def test_create_library_whitespace_only_name(client: TestClient) -> None:
    """Test that whitespace-only name is accepted (no trimming validation)."""
    response = client.post("/libraries", json={"name": "   "})

    # Current behavior: whitespace names are accepted
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["library"]["name"] == "   "


def test_create_library_unicode_name(client: TestClient) -> None:
    """Test that Unicode characters in name are accepted."""
    response = client.post("/libraries", json={"name": "图书馆 📚 Библиотека"})

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["library"]["name"] == "图书馆 📚 Библиотека"


def test_get_libraries_with_data(client: TestClient) -> None:
    """Test getting libraries after creating some."""
    # Create 3 libraries
    client.post("/libraries", json={"name": "Library 1"}).json()
    client.post("/libraries", json={"name": "Library 2"}).json()
    client.post("/libraries", json={"name": "Library 3"}).json()

    # Get all libraries
    response = client.get("/libraries")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data["libraries"]) == 3
    assert data["total"] == 3
    assert data["limit"] == 100
    assert data["offset"] == 0

    # Verify library names
    names = {lib["name"] for lib in data["libraries"]}
    assert names == {"Library 1", "Library 2", "Library 3"}


def test_get_libraries_pagination(client: TestClient) -> None:
    """Test library pagination."""
    # Create 5 libraries
    for i in range(5):
        client.post("/libraries", json={"name": f"Library {i}"})

    # Get first 2
    response = client.get("/libraries?limit=2&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["libraries"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    # Get next 2
    response = client.get("/libraries?limit=2&offset=2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["libraries"]) == 2
    assert data["offset"] == 2


def test_get_libraries_limit_boundary_min(client: TestClient) -> None:
    """Test pagination with minimum limit (1)."""
    # Create 3 libraries
    for i in range(3):
        client.post("/libraries", json={"name": f"Library {i}"})

    response = client.get("/libraries?limit=1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["libraries"]) == 1
    assert data["limit"] == 1


def test_get_libraries_limit_boundary_max(client: TestClient) -> None:
    """Test pagination with maximum limit (1000)."""
    response = client.get("/libraries?limit=1000")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["limit"] == 1000


def test_get_libraries_limit_exceeds_max(client: TestClient) -> None:
    """Test that limit > 1000 returns validation error."""
    response = client.get("/libraries?limit=1001")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()
    assert "detail" in error


def test_get_libraries_limit_negative(client: TestClient) -> None:
    """Test that negative limit returns validation error."""
    response = client.get("/libraries?limit=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()
    assert "detail" in error


def test_get_libraries_offset_negative(client: TestClient) -> None:
    """Test that negative offset returns validation error."""
    response = client.get("/libraries?offset=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()
    assert "detail" in error


def test_get_libraries_offset_beyond_data(client: TestClient) -> None:
    """Test that offset beyond available data returns empty list."""
    # Create 3 libraries
    for i in range(3):
        client.post("/libraries", json={"name": f"Library {i}"})

    # Request offset 100 when only 3 exist
    response = client.get("/libraries?offset=100")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["libraries"] == []
    assert data["offset"] == 100


def test_upload_document(client: TestClient) -> None:
    """Test uploading a document to a library."""
    # First create a library
    library_response = client.post(
        "/libraries",
        json={"name": "Test Library"},
    )
    assert library_response.status_code == status.HTTP_201_CREATED
    library_id = library_response.json()["library"]["id"]

    # Create a test file
    test_content = b"This is a test document with some content."
    test_file = io.BytesIO(test_content)

    # Upload document
    response = client.post(
        f"/libraries/{library_id}/documents",
        files={"file": ("test.txt", test_file, "text/plain")},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["document_id"]
    assert data["library_id"] == library_id
    assert data["filename"] == "test.txt"
    assert data["upload_complete"] is True
    assert "message" in data


def test_upload_large_document(client: TestClient) -> None:
    """Test uploading a large document with streaming."""
    # Create library
    library_response = client.post(
        "/libraries",
        json={"name": "Large File Library"},
    )
    assert library_response.status_code == status.HTTP_201_CREATED
    library_id = library_response.json()["library"]["id"]

    # Create a large test file (2MB)
    large_content = b"X" * (2 * 1024 * 1024)
    test_file = io.BytesIO(large_content)

    # Upload large document
    response = client.post(
        f"/libraries/{library_id}/documents",
        files={"file": ("large.txt", test_file, "text/plain")},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["upload_complete"] is True


def test_upload_document_invalid_library_id(client: TestClient) -> None:
    """Test that invalid library ID format returns 422."""
    test_content = b"Test content"
    test_file = io.BytesIO(test_content)

    # Use invalid UUID format - ValidationError from LibraryId value object
    response = client.post(
        "/libraries/not-a-uuid/documents",
        files={"file": ("test.txt", test_file, "text/plain")},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()
    assert "detail" in error
    assert "errors" in error


def test_upload_document_nonexistent_library(client: TestClient) -> None:
    """Test that non-existent library ID returns 404."""
    from uuid import uuid4

    test_content = b"Test content"
    test_file = io.BytesIO(test_content)

    # Use valid UUID format but non-existent library
    fake_library_id = str(uuid4())

    response = client.post(
        f"/libraries/{fake_library_id}/documents",
        files={"file": ("test.txt", test_file, "text/plain")},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error = response.json()
    assert "detail" in error
    assert error["entity_type"] == "Library"
    assert error["entity_id"] == fake_library_id


def test_upload_document_missing_file(client: TestClient) -> None:
    """Test that missing file field returns validation error."""
    # Create library
    library_response = client.post("/libraries", json={"name": "Test Library"})
    library_id = library_response.json()["library"]["id"]

    # Upload without file
    response = client.post(f"/libraries/{library_id}/documents")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    error = response.json()
    assert "detail" in error


def test_upload_document_empty_file(client: TestClient) -> None:
    """Test uploading an empty file (0 bytes)."""
    # Create library
    library_response = client.post("/libraries", json={"name": "Test Library"})
    library_id = library_response.json()["library"]["id"]

    # Create empty file
    empty_file = io.BytesIO(b"")

    # Upload empty document
    response = client.post(
        f"/libraries/{library_id}/documents",
        files={"file": ("empty.txt", empty_file, "text/plain")},
    )

    # Empty files might be accepted or rejected depending on business logic
    # For now, we just verify it doesn't crash
    assert response.status_code in [
        status.HTTP_201_CREATED,
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
    ]


def test_upload_document_no_filename(client: TestClient) -> None:
    """Test uploading a file without filename."""
    # Create library
    library_response = client.post("/libraries", json={"name": "Test Library"})
    library_id = library_response.json()["library"]["id"]

    # Create file without filename
    test_content = b"Test content"
    test_file = io.BytesIO(test_content)

    response = client.post(
        f"/libraries/{library_id}/documents",
        files={"file": ("", test_file, "text/plain")},
    )

    # Should either accept with default name or return error
    if response.status_code == status.HTTP_201_CREATED:
        data = response.json()
        # Should have some filename (either empty string or "untitled")
        assert "filename" in data


def test_upload_document_various_content_types(client: TestClient) -> None:
    """Test uploading documents with various content types."""
    # Create library
    library_response = client.post("/libraries", json={"name": "Test Library"})
    library_id = library_response.json()["library"]["id"]

    content_types = [
        ("test.pdf", "application/pdf"),
        ("test.doc", "application/msword"),
        ("test.json", "application/json"),
        ("test.xml", "application/xml"),
    ]

    for filename, content_type in content_types:
        test_content = b"Test content for " + filename.encode()
        test_file = io.BytesIO(test_content)

        response = client.post(
            f"/libraries/{library_id}/documents",
            files={"file": (filename, test_file, content_type)},
        )

        # Should accept various content types
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["filename"] == filename
