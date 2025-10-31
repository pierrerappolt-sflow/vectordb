"""Tests for strategy-related value objects."""

import pytest
from vdb_core.domain.value_objects.strategy import ChunkingBehavior, ModalityType, ModalityType


class TestModalityType:
    """Tests for ModalityType value object."""

    def test_create_modality_type_with_text(self) -> None:
        """Test creating ModalityType with TEXT."""
        modality = ModalityType(value=ModalityType.TEXT)
        assert modality.value == ModalityType.TEXT
        assert isinstance(modality, ModalityType)

    def test_create_modality_type_with_image(self) -> None:
        """Test creating ModalityType with IMAGE."""
        modality = ModalityType(value=ModalityType.IMAGE)
        assert modality.value == ModalityType.IMAGE

    def test_create_modality_type_with_multimodal(self) -> None:
        """Test creating ModalityType with MULTIMODAL."""
        modality = ModalityType(value=ModalityType.MULTIMODAL)
        assert modality.value == ModalityType.MULTIMODAL

    def test_default_modality_type_is_text(self) -> None:
        """Test that default ModalityType is TEXT."""
        modality = ModalityType()
        assert modality.value == ModalityType.TEXT

    def test_modality_type_equality(self) -> None:
        """Test that ModalityType with same value are equal."""
        modality1 = ModalityType(value=ModalityType.TEXT)
        modality2 = ModalityType(value=ModalityType.TEXT)
        assert modality1 == modality2

    def test_modality_type_inequality(self) -> None:
        """Test that ModalityType with different values are not equal."""
        modality1 = ModalityType(value=ModalityType.TEXT)
        modality2 = ModalityType(value=ModalityType.IMAGE)
        assert modality1 != modality2

    def test_modality_type_is_hashable(self) -> None:
        """Test that ModalityType can be used in sets and dicts."""
        modality1 = ModalityType(value=ModalityType.TEXT)
        modality2 = ModalityType(value=ModalityType.IMAGE)
        modality3 = ModalityType(value=ModalityType.TEXT)

        modality_set = {modality1, modality2, modality3}
        assert len(modality_set) == 2  # modality1 and modality3 are equal

    def test_modality_type_is_immutable(self) -> None:
        """Test that ModalityType is immutable."""
        modality = ModalityType(value=ModalityType.TEXT)
        with pytest.raises(Exception):  # Frozen dataclass error
            modality.value = ModalityType.IMAGE  # type: ignore

    def test_modality_type_enum_values(self) -> None:
        """Test ModalityType has expected values."""
        expected_values = {"text", "image", "multimodal"}
        actual_values = {mod.value for mod in ModalityType}
        assert actual_values == expected_values

    def test_all_modality_types_can_be_created(self) -> None:
        """Test that all ModalityType values can be used."""
        for modality_enum in ModalityType:
            modality = ModalityType(value=modality_enum)
            assert modality.value == modality_enum


class TestChunkingBehavior:
    """Tests for ChunkingBehavior enum."""

    def test_chunking_behavior_is_str_enum(self) -> None:
        """Test that ChunkingBehavior is a StrEnum."""
        assert issubclass(ChunkingBehavior, str)

    def test_chunking_behavior_split(self) -> None:
        """Test ChunkingBehavior.SPLIT value."""
        assert ChunkingBehavior.SPLIT.value == "split"

    def test_chunking_behavior_passthrough(self) -> None:
        """Test ChunkingBehavior.PASSTHROUGH value."""
        assert ChunkingBehavior.PASSTHROUGH.value == "passthrough"

    def test_chunking_behavior_frame_extract(self) -> None:
        """Test ChunkingBehavior.FRAME_EXTRACT value."""
        assert ChunkingBehavior.FRAME_EXTRACT.value == "frame_extract"

    def test_chunking_behavior_time_segment(self) -> None:
        """Test ChunkingBehavior.TIME_SEGMENT value."""
        assert ChunkingBehavior.TIME_SEGMENT.value == "time_segment"

    def test_chunking_behavior_enum_values(self) -> None:
        """Test ChunkingBehavior has expected values."""
        expected_values = {"split", "passthrough", "frame_extract", "time_segment"}
        actual_values = {behavior.value for behavior in ChunkingBehavior}
        assert actual_values == expected_values

    def test_chunking_behavior_can_be_compared(self) -> None:
        """Test that ChunkingBehavior values can be compared."""
        behavior1 = ChunkingBehavior.SPLIT
        behavior2 = ChunkingBehavior.SPLIT
        behavior3 = ChunkingBehavior.PASSTHROUGH

        assert behavior1 == behavior2
        assert behavior1 != behavior3

    def test_chunking_behavior_is_hashable(self) -> None:
        """Test that ChunkingBehavior can be used in sets and dicts."""
        behaviors = {
            ChunkingBehavior.SPLIT,
            ChunkingBehavior.PASSTHROUGH,
            ChunkingBehavior.SPLIT,  # Duplicate
        }
        assert len(behaviors) == 2

    def test_chunking_behavior_string_conversion(self) -> None:
        """Test that ChunkingBehavior converts to string correctly."""
        behavior = ChunkingBehavior.SPLIT
        assert str(behavior) == "split"
        assert isinstance(behavior, str)
