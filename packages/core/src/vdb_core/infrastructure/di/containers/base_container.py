"""Base container with singleton management."""

from collections.abc import Callable
from typing import Any, TypeVar, cast

T = TypeVar("T")


class BaseContainer:
    """Base container providing singleton management and lazy initialization.

    Features:
    - Lazy initialization: dependencies created only when first accessed
    - Singleton caching: instances reused across requests
    - Override mechanism for testing
    """

    def __init__(self) -> None:
        """Initialize the container."""
        self._singletons: dict[str, Any] = {}
        self._overrides: dict[str, Callable[[], Any]] = {}

    def _get_or_create(self, key: str, factory: Callable[[], T]) -> T:
        """Get or create a singleton instance.

        Args:
            key: Unique identifier for the singleton
            factory: Factory function to create the instance

        Returns:
            The singleton instance

        """
        # Check for override first
        if key in self._overrides:
            factory = self._overrides[key]

        # Return cached instance if exists
        if key in self._singletons:
            return cast("T", self._singletons[key])

        # Create and cache new instance
        instance = factory()
        self._singletons[key] = instance
        return instance

    def override(self, key: str, factory: Callable[[], Any]) -> None:
        """Override a dependency for testing.

        Args:
            key: The dependency key (e.g., "create_library_use_case")
            factory: Factory function to create the override instance

        """
        self._overrides[key] = factory

    def clear_overrides(self) -> None:
        """Clear all overrides (useful for test cleanup)."""
        self._overrides.clear()

    def reset(self) -> None:
        """Reset the container (clears singletons and overrides)."""
        self._singletons.clear()
        self._overrides.clear()
