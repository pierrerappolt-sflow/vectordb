"""Base class for Cohere embedding strategies with rate limiting."""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod

import cohere


class BaseCohereStrategy(ABC):
    """Base class for all Cohere embedding strategies with rate limiting.

    Handles:
    - API client initialization
    - Rate limiting and retry logic
    - Common error handling

    Subclasses define:
    - Model name
    - Dimensions
    - Identifier
    - Supported modalities
    """

    def __init__(self, config: dict[str, object] | None = None) -> None:
        """Initialize Cohere embedding strategy.

        Args:
            config: Configuration dict with optional keys:
                - api_key: Cohere API key
                - timeout: Request timeout in seconds
                - max_retries: Maximum number of retries (default: 5)
                - initial_backoff: Initial backoff time in seconds (default: 10)

        """
        self.config = config or {}

        # Get API key from config or environment
        api_key = self.config.get("api_key") or os.getenv("COHERE_API_KEY")
        if not api_key:
            msg = "COHERE_API_KEY must be set in config or environment"
            raise ValueError(msg)

        # Initialize Cohere client
        timeout_val = self.config.get("timeout", 60)
        timeout: int = int(timeout_val) if timeout_val is not None else 60  # type: ignore[call-overload]
        self.client = cohere.Client(api_key=str(api_key), timeout=timeout)

        # Aggressive retry configuration for Trial API keys (100 calls/min limit)
        # Default backoff sequence: 10s, 20s, 40s, 80s, 160s = ~5 minutes total
        max_retries_val = self.config.get("max_retries", 5)
        self.max_retries: int = int(max_retries_val) if max_retries_val is not None else 5  # type: ignore[call-overload]
        initial_backoff_val = self.config.get("initial_backoff", 10.0)
        self.initial_backoff: float = float(initial_backoff_val) if initial_backoff_val is not None else 10.0  # type: ignore[arg-type]

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Return the strategy identifier."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the Cohere model name."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return vector dimensions."""

    @property
    def max_tokens(self) -> int:
        """Return max token limit."""
        return 512

    async def _call_cohere_with_retry(
        self,
        texts: list[str],
        input_type: str,
    ) -> list[list[float]]:
        """Call Cohere API with exponential backoff retry.

        Args:
            texts: List of texts to embed
            input_type: Input type for Cohere API ("search_query" or "search_document")

        Returns:
            List of embedding vectors

        Raises:
            Exception: If all retries fail

        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Call Cohere API (sync client in async context)
                # TODO: Use async client when available
                response = self.client.embed(
                    texts=texts,
                    model=self.model_name,
                    input_type=input_type,
                    embedding_types=["float"],
                )

                # Extract embeddings
                if hasattr(response.embeddings, "float_"):
                    embeddings = response.embeddings.float_
                else:
                    # Fallback for different response types
                    embeddings = response.embeddings  # type: ignore[assignment]

                if not embeddings:
                    msg = "No embeddings returned from Cohere API"
                    raise ValueError(msg)

                # Validate dimensions
                for embedding in embeddings:
                    if len(embedding) != self.dimensions:
                        msg = f"Expected {self.dimensions} dimensions, got {len(embedding)}"
                        raise ValueError(msg)

                return list(embeddings)

            except cohere.errors.TooManyRequestsError as e:
                # Rate limit hit - use exponential backoff with jitter
                last_error = e
                backoff_time = self.initial_backoff * (2 ** attempt)

                if attempt < self.max_retries - 1:
                    import logging
                    import random

                    # Add jitter (±20%) to avoid thundering herd
                    jitter = backoff_time * 0.2 * (random.random() * 2 - 1)
                    actual_backoff = backoff_time + jitter

                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Cohere rate limit hit (attempt {attempt + 1}/{self.max_retries}). "
                        f"Retrying in {actual_backoff:.1f}s (Trial key: 100 calls/min limit)"
                    )
                    await asyncio.sleep(actual_backoff)
                else:
                    # Last attempt failed
                    raise

            except Exception as e:
                # Other errors - retry with backoff (less aggressive)
                last_error = e  # type: ignore[assignment]
                backoff_time = self.initial_backoff * (2 ** attempt) / 2  # Half the backoff for non-rate-limit errors

                if attempt < self.max_retries - 1:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Cohere API error (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {backoff_time:.1f}s..."
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    # Last attempt failed
                    raise

        # All retries exhausted
        msg = f"Failed after {self.max_retries} attempts"
        raise RuntimeError(msg) from last_error
