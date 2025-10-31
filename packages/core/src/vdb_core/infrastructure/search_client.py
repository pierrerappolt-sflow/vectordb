"""HTTP client for vector search service."""

from __future__ import annotations

import logging
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)


class SearchServiceClient:
    """HTTP client for communicating with the vector search service.

    This client provides methods to interact with the search service API:
    - Batch index vectors
    - Batch delete vectors
    - Search for similar vectors
    - Get index statistics
    """

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        """Initialize search service client.

        Args:
            base_url: Base URL of the search service (e.g., "http://search:8001")
            timeout: Request timeout in seconds

        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> SearchServiceClient:
        """Async context manager entry."""
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating it if necessary."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self._client

    async def batch_index(
        self,
        library_id: str,
        config_id: str,
        embeddings: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Batch index vectors in the search service.

        Args:
            library_id: Library UUID
            config_id: VectorizationConfig UUID
            embeddings: List of {"embedding_id": str, "vector": list[float]}

        Returns:
            Dict with "indexed_count" and "failed_count"

        Raises:
            httpx.HTTPError: If request fails

        """
        try:
            response = await self.client.post(
                "/index",
                json={
                    "library_id": library_id,
                    "config_id": config_id,
                    "embeddings": embeddings,
                },
            )
            response.raise_for_status()
            return cast("dict[str, int]", response.json())

        except httpx.HTTPError as e:
            logger.error("Failed to batch index vectors: %s", str(e))
            raise

    async def batch_delete(
        self,
        library_id: str,
        config_id: str,
        embedding_ids: list[str],
    ) -> dict[str, int]:
        """Batch delete vectors from the search service.

        Args:
            library_id: Library UUID
            config_id: VectorizationConfig UUID
            embedding_ids: List of embedding UUIDs to delete

        Returns:
            Dict with "deleted_count"

        Raises:
            httpx.HTTPError: If request fails

        """
        try:
            response = await self.client.request(
                "DELETE",
                "/index",
                json={
                    "library_id": library_id,
                    "config_id": config_id,
                    "embedding_ids": embedding_ids,
                },
            )
            response.raise_for_status()
            return cast("dict[str, int]", response.json())

        except httpx.HTTPError as e:
            logger.error("Failed to batch delete vectors: %s", str(e))
            raise

    async def search(
        self,
        library_id: str,
        config_id: str,
        query_vector: list[float],
        k: int = 10,
    ) -> dict[str, Any]:
        """Search for similar vectors.

        Args:
            library_id: Library UUID
            config_id: VectorizationConfig UUID
            query_vector: Query vector
            k: Number of results to return

        Returns:
            Dict with "results" (list of search results) and "total" (int)

        Raises:
            httpx.HTTPError: If request fails

        """
        try:
            response = await self.client.post(
                "/search",
                json={
                    "library_id": library_id,
                    "config_id": config_id,
                    "query_vector": query_vector,
                    "k": k,
                },
            )
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

        except httpx.HTTPError as e:
            logger.error("Failed to search vectors: %s", str(e))
            raise

    async def get_stats(self) -> dict[str, Any]:
        """Get index statistics.

        Returns:
            Dict with "indices" (list) and "total_embeddings" (int)

        Raises:
            httpx.HTTPError: If request fails

        """
        try:
            response = await self.client.get("/stats")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json())

        except httpx.HTTPError as e:
            logger.error("Failed to get stats: %s", str(e))
            raise

    async def health_check(self) -> bool:
        """Check if search service is healthy.

        Returns:
            True if healthy, False otherwise

        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return cast("dict[str, Any]", response.json()).get("status") == "healthy"

        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
