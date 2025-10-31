"""Tests for LazyCollection - lazy loading collection pattern."""

from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from vdb_core.domain.base import LazyCollection


@dataclass
class MockItem:
    """Mock item for collection testing."""

    id: str
    name: str


async def create_test_loader(items: list[MockItem], item_id: str | None = None) -> AsyncIterator[MockItem]:
    """Create a test loader that yields items."""
    if item_id:
        # Load single item
        for item in items:
            if item.id == item_id:
                yield item
                return
    else:
        # Load all items
        for item in items:
            yield item


@pytest.mark.asyncio
class TestLazyCollection:
    """Tests for LazyCollection lazy loading behavior."""

    async def test_get_loads_single_item(self) -> None:
        """Test that get() loads a single item by ID."""
        # Arrange
        items = [
            MockItem(id="1", name="Item 1"),
            MockItem(id="2", name="Item 2"),
            MockItem(id="3", name="Item 3"),
        ]

        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=lambda item_id: create_test_loader(items, item_id),
            get_id=lambda item: item.id,
        )

        # Act
        result = await collection.get("2")

        # Assert
        assert result.id == "2"
        assert result.name == "Item 2"
        assert not collection.is_loaded  # Only loaded one item, not all

    async def test_get_caches_loaded_item(self) -> None:
        """Test that get() caches loaded items."""
        # Arrange
        load_count = 0

        async def counting_loader(item_id: str | None) -> AsyncIterator[MockItem]:
            nonlocal load_count
            load_count += 1
            if item_id == "1":
                yield MockItem(id="1", name="Item 1")

        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=counting_loader,
            get_id=lambda item: item.id,
        )

        # Act - get same item twice
        result1 = await collection.get("1")
        result2 = await collection.get("1")

        # Assert
        assert result1 is result2  # Same instance from cache
        assert load_count == 1  # Loader called only once

    async def test_all_loads_all_items(self) -> None:
        """Test that all() loads all items."""
        # Arrange
        items = [
            MockItem(id="1", name="Item 1"),
            MockItem(id="2", name="Item 2"),
            MockItem(id="3", name="Item 3"),
        ]

        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=lambda item_id: create_test_loader(items, item_id),
            get_id=lambda item: item.id,
        )

        # Act
        results = []
        async for item in collection.all():
            results.append(item)

        # Assert
        assert len(results) == 3
        assert [r.id for r in results] == ["1", "2", "3"]
        assert collection.is_loaded  # All items loaded

    async def test_all_yields_cached_items_first(self) -> None:
        """Test that all() yields cached items before lazy loading."""
        # Arrange
        items = [
            MockItem(id="1", name="Item 1"),
            MockItem(id="2", name="Item 2"),
            MockItem(id="3", name="Item 3"),
        ]

        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=lambda item_id: create_test_loader(items, item_id),
            get_id=lambda item: item.id,
        )

        # Pre-load item 2
        await collection.get("2")

        # Act
        results = []
        async for item in collection.all():
            results.append(item)

        # Assert - item 2 appears first (from cache), then 1 and 3
        assert len(results) == 3
        assert results[0].id == "2"  # Cached item first
        assert {r.id for r in results} == {"1", "2", "3"}

    async def test_all_does_not_reload_if_already_loaded(self) -> None:
        """Test that all() doesn't reload if collection is already loaded."""
        # Arrange
        load_count = 0

        async def counting_loader(item_id: str | None) -> AsyncIterator[MockItem]:
            nonlocal load_count
            load_count += 1
            yield MockItem(id="1", name="Item 1")

        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=counting_loader,
            get_id=lambda item: item.id,
        )

        # Act - iterate twice
        results1 = [item async for item in collection.all()]
        results2 = [item async for item in collection.all()]

        # Assert
        assert len(results1) == 1
        assert len(results2) == 1
        assert load_count == 1  # Loader called only once

    async def test_get_raises_error_if_item_not_found(self) -> None:
        """Test that get() raises ValueError if item not found."""
        # Arrange
        items = [MockItem(id="1", name="Item 1")]

        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=lambda item_id: create_test_loader(items, item_id),
            get_id=lambda item: item.id,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Item 999 not found"):
            await collection.get("999")

    async def test_get_raises_error_if_no_loader_configured(self) -> None:
        """Test that get() raises RuntimeError if no loader configured."""
        # Arrange
        collection: LazyCollection[MockItem, str] = LazyCollection()

        # Act & Assert
        with pytest.raises(RuntimeError, match="No loader configured"):
            await collection.get("1")

    async def test_all_raises_error_if_no_loader_configured(self) -> None:
        """Test that all() raises RuntimeError if no loader configured."""
        # Arrange
        collection: LazyCollection[MockItem, str] = LazyCollection()

        # Act & Assert
        with pytest.raises(RuntimeError, match="No loader configured"):
            async for _ in collection.all():
                pass

    async def test_add_to_cache_with_configured_id_extractor(self) -> None:
        """Test that add_to_cache() works with configured ID extractor."""
        # Arrange
        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=lambda item_id: create_test_loader([], item_id),
            get_id=lambda item: item.id,
        )

        # Act
        item = MockItem(id="1", name="Item 1")
        collection.add_to_cache(item)

        # Assert
        assert "1" in collection._items
        assert collection._items["1"] is item

    async def test_add_to_cache_with_id_attribute_fallback(self) -> None:
        """Test that add_to_cache() uses id attribute if no extractor configured."""
        # Arrange
        collection: LazyCollection[MockItem, str] = LazyCollection()

        # Act
        item = MockItem(id="1", name="Item 1")
        collection.add_to_cache(item)

        # Assert
        assert "1" in collection._items
        assert collection._items["1"] is item

    async def test_add_to_cache_raises_error_without_id(self) -> None:
        """Test that add_to_cache() raises error if no ID available."""

        @dataclass
        class ItemWithoutId:
            name: str

        # Arrange
        collection: LazyCollection[ItemWithoutId, str] = LazyCollection()

        # Act & Assert
        item = ItemWithoutId(name="Test")
        with pytest.raises(RuntimeError, match="No ID extractor configured"):
            collection.add_to_cache(item)

    async def test_cached_items_returns_list_without_loading(self) -> None:
        """Test that cached_items property returns cached items without lazy loading."""
        # Arrange
        items = [
            MockItem(id="1", name="Item 1"),
            MockItem(id="2", name="Item 2"),
        ]

        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=lambda item_id: create_test_loader(items, item_id),
            get_id=lambda item: item.id,
        )

        # Pre-load one item
        await collection.get("1")

        # Act
        cached = collection.cached_items

        # Assert
        assert len(cached) == 1
        assert cached[0].id == "1"
        assert not collection.is_loaded  # Didn't trigger full load

    async def test_is_loaded_false_initially(self) -> None:
        """Test that is_loaded is False initially."""
        # Arrange
        collection: LazyCollection[MockItem, str] = LazyCollection()

        # Assert
        assert not collection.is_loaded

    async def test_is_loaded_true_after_all_called(self) -> None:
        """Test that is_loaded is True after all() completes."""
        # Arrange
        items = [MockItem(id="1", name="Item 1")]

        collection: LazyCollection[MockItem, str] = LazyCollection()
        collection.set_loader(
            loader=lambda item_id: create_test_loader(items, item_id),
            get_id=lambda item: item.id,
        )

        # Act
        async for _ in collection.all():
            pass

        # Assert
        assert collection.is_loaded
