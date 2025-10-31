"""Generic lazy loading collection for child entities."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable


class LazyCollection[T, ID]:
    """Generic lazy loading collection for child entities.

    Provides a standard interface for lazy loading collections with:
    - Get by ID (single item lookup with caching)
    - Iterate over all items (async iterator)
    - Automatic caching of loaded items
    - Loading state tracking

    Usage:
        # Create collection and configure loader
        fragments = LazyCollection()
        fragments.set_loader(
            loader=fragment_loader_fn,  # Callable[[ID | None], AsyncIterator[T]]
            get_id=lambda f: f.id
        )

        # Get single item by ID (lazy loads if not cached)
        fragment = await fragments.get(fragment_id)

        # Iterate over all items (lazy loads remaining items)
        async for fragment in fragments.all():
            process(fragment)

    """

    def __init__(self) -> None:
        """Initialize empty lazy collection.

        Use set_loader() to configure the loader function.
        """
        self._items: dict[ID, T] = {}
        self._loader: Callable[[ID | None], AsyncIterator[T]] | None = None
        self._loaded: bool = False
        self._get_id: Callable[[T], ID] | None = None

    def set_loader(
        self,
        loader: Callable[[ID | None], AsyncIterator[T]],
        get_id: Callable[[T], ID],
    ) -> None:
        """Configure the loader function and ID extractor.

        Args:
            loader: Async generator that yields items. Accepts optional ID parameter
                   for single-item lookup. If ID is None, should yield all items.
            get_id: Function to extract ID from an item

        """
        self._loader = loader
        self._get_id = get_id

    async def get(self, item_id: ID) -> T:
        """Get item by ID, lazy loading if necessary.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            The requested item

        Raises:
            RuntimeError: If no loader is configured
            ValueError: If item is not found

        """
        # Check cache first
        if item_id in self._items:
            return self._items[item_id]

        # Lazy load
        if not self._loader:
            msg = "No loader configured for this collection"
            raise RuntimeError(msg)

        if not self._get_id:
            msg = "No ID extractor configured for this collection"
            raise RuntimeError(msg)

        async for item in self._loader(item_id):
            current_id = self._get_id(item)
            self._items[current_id] = item
            if current_id == item_id:
                return item

        msg = f"Item {item_id} not found"
        raise ValueError(msg)

    async def all(self) -> AsyncIterator[T]:
        """Iterate over all items, lazy loading if necessary.

        First yields any cached items, then lazy loads remaining items.

        Raises:
            RuntimeError: If no loader is configured

        """
        # First yield cached items
        for item in self._items.values():
            yield item

        # Already loaded all items
        if self._loaded:
            return

        # Lazy load remaining items
        if not self._loader:
            msg = "No loader configured for this collection"
            raise RuntimeError(msg)

        if not self._get_id:
            msg = "No ID extractor configured for this collection"
            raise RuntimeError(msg)

        async for item in self._loader(None):
            item_id = self._get_id(item)
            if item_id not in self._items:
                self._items[item_id] = item
                yield item

        # Mark as fully loaded
        self._loaded = True

    def add_to_cache(self, item: T) -> None:
        """Add item to cache (used when item is created/added during operations).

        Args:
            item: Item to add to cache

        """
        # If no ID extractor is configured, try to get 'id' attribute
        if self._get_id:
            item_id = self._get_id(item)
        # Fallback: try to get 'id' attribute directly
        elif hasattr(item, "id"):
            item_id = item.id
        else:
            msg = "No ID extractor configured and item has no 'id' attribute"
            raise RuntimeError(msg)

        self._items[item_id] = item

    @property
    def cached_items(self) -> list[T]:
        """Get all currently cached items (does not trigger lazy loading).

        Returns:
            List of cached items

        """
        return list(self._items.values())

    @property
    def is_loaded(self) -> bool:
        """Check if all items have been loaded.

        Returns:
            True if all items are loaded, False otherwise

        """
        return self._loaded
