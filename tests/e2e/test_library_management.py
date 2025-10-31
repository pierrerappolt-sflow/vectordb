"""E2E tests for library management endpoints."""

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_library(api_client, clean_database) -> None:
    """Test creating a library via API."""
    # Create a library
    response = await api_client.post(
        "/libraries",
        json={"name": "Test Library"},
    )

    assert response.status_code == 201
    data = response.json()

    # Verify response structure
    assert "library" in data
    library = data["library"]

    assert "id" in library
    assert library["name"] == "Test Library"
    assert library["status"] == "active"
    assert "created_at" in library
    assert "updated_at" in library
    assert library["document_count"] == 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_libraries(api_client, clean_database) -> None:
    """Test retrieving all libraries."""
    # Create multiple libraries
    lib1_response = await api_client.post("/libraries", json={"name": "Library 1"})
    lib2_response = await api_client.post("/libraries", json={"name": "Library 2"})

    assert lib1_response.status_code == 201
    assert lib2_response.status_code == 201

    # Get all libraries
    response = await api_client.get("/libraries")

    assert response.status_code == 200
    data = response.json()

    assert "libraries" in data
    assert len(data["libraries"]) == 2

    library_names = {lib["name"] for lib in data["libraries"]}
    assert library_names == {"Library 1", "Library 2"}


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_library_name_validation(api_client, clean_database) -> None:
    """Test that library name validation works."""
    # Try to create library with name too long
    long_name = "x" * 100  # Exceeds 50 char limit

    response = await api_client.post(
        "/libraries",
        json={"name": long_name},
    )

    # Should fail validation
    assert response.status_code in {422, 400}
