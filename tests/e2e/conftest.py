"""Pytest fixtures for e2e tests.

Manages docker-compose lifecycle and provides API client fixtures.
"""

import subprocess
import time
from pathlib import Path

import httpx
import pytest


@pytest.fixture(scope="session")
def docker_compose_file():
    """Path to docker-compose.yml file."""
    return Path(__file__).parent.parent.parent / "docker-compose.yml"


@pytest.fixture(scope="session")
def docker_compose_project_name() -> str:
    """Unique project name for docker-compose to avoid conflicts."""
    return "vdb-e2e-test"


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Base URL for the FastAPI backend."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def temporal_ui_url() -> str:
    """Base URL for the Temporal UI."""
    return "http://localhost:8080"


@pytest.fixture(scope="session", autouse=True)
def docker_services(docker_compose_file, docker_compose_project_name):
    """Start docker-compose services for the entire test session.

    This fixture:
    1. Starts all services via docker-compose
    2. Waits for services to be healthy
    3. Yields control to tests
    4. Tears down services after all tests complete
    """
    project_dir = docker_compose_file.parent

    # Start docker-compose
    subprocess.run(
        [
            "docker-compose",
            "-f",
            str(docker_compose_file),
            "-p",
            docker_compose_project_name,
            "up",
            "-d",
            "--build",
        ],
        cwd=project_dir,
        check=True,
    )

    # Wait for services to be healthy
    max_retries = 60  # 60 seconds
    retry_delay = 1

    for i in range(max_retries):
        try:
            # Check if API is responding
            response = httpx.get("http://localhost:8000/health", timeout=2.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            if i == max_retries - 1:
                msg = "API failed to become healthy in time"
                raise RuntimeError(msg)
            time.sleep(retry_delay)

    # Additional wait for Temporal to be fully ready
    time.sleep(5)

    yield

    # Teardown: stop and remove containers
    subprocess.run(
        [
            "docker-compose",
            "-f",
            str(docker_compose_file),
            "-p",
            docker_compose_project_name,
            "down",
            "-v",  # Remove volumes
        ],
        cwd=project_dir,
        check=False,  # Don't fail if already stopped
    )


@pytest.fixture
async def api_client(api_base_url, docker_services):
    """Async HTTP client for the FastAPI backend.

    Provides a clean httpx.AsyncClient for each test.
    """
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
async def clean_database(api_client):
    """Ensure database is clean before each test.

    This fixture:
    1. Deletes all libraries (cascades to documents, chunks, etc.)
    2. Yields control to the test
    3. Can be used to reset state between tests
    """
    # Get all libraries
    response = await api_client.get("/libraries")
    if response.status_code == 200:
        data = response.json()
        for library in data.get("libraries", []):
            # Delete each library (cascades to all children)
            await api_client.delete(f"/libraries/{library['id']}")

    yield

    # Optionally clean up after test as well
    response = await api_client.get("/libraries")
    if response.status_code == 200:
        data = response.json()
        for library in data.get("libraries", []):
            await api_client.delete(f"/libraries/{library['id']}")


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for upload testing."""
    file_path = tmp_path / "sample.txt"
    content = """
    This is a sample document for testing.
    It contains multiple sentences that will be chunked.
    Each sentence should become a separate chunk during ingestion.

    This paragraph is separated by a blank line.
    The chunking strategy will determine how this is split.
    """.strip()

    file_path.write_text(content)
    return file_path


@pytest.fixture
def large_text_file(tmp_path):
    """Create a larger text file for streaming upload testing.

    Generates > 1 MB file to test fragment batching logic.
    """
    file_path = tmp_path / "large_document.txt"

    # Generate ~1.5 MB of text to test batching across 1 MB boundary
    paragraphs = []
    for i in range(1500):  # ~1.5 MB of text
        paragraph = (
            f"This is paragraph {i}. It contains meaningful text content for testing document ingestion and search. "
            * 10
        )
        paragraphs.append(paragraph)

    content = "\n\n".join(paragraphs)
    file_path.write_text(content)
    return file_path
