"""ChunkingStrategy entity - reusable chunking configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
import uuid

from vdb_core.domain.base import IEntity
from vdb_core.domain.value_objects import (
    ChunkingBehavior,
    ChunkingStrategyId,
    ChunkingStrategyStatus,
    ModalityType,
)
from vdb_core.utils.dt_utils import utc_now

# Valid behavior-modality combinations
VALID_BEHAVIORS_BY_MODALITY: dict[ModalityType, set[ChunkingBehavior]] = {
    ModalityType.TEXT: {ChunkingBehavior.SPLIT},
    ModalityType.IMAGE: {ChunkingBehavior.PASSTHROUGH},
}


@dataclass(slots=True, kw_only=True, eq=False)
class ChunkingStrategy(IEntity):
    """Chunking strategy entity - ONE modality per strategy.

    Each strategy is specialized for a specific modality type.
    Strategies are reusable across libraries and referenced by vectorization configs.

    Common chunking parameters are explicit fields.
    Strategy-specific implementation details go in config JSON.

    Behavior determines which parameters are required:
    - SPLIT: chunk_size_tokens, chunk_overlap_tokens (TEXT)
    - PASSTHROUGH: max_content_size_bytes (IMAGE)
    - FRAME_EXTRACT: frame_sample_rate_fps (VIDEO)
    - TIME_SEGMENT: segment_duration_seconds (AUDIO)
    """

    id: ChunkingStrategyId = field(init=False)
    name: str
    model_key: str  # e.g., "sentence-split", "image-passthrough", "video-frame-extract"
    status: ChunkingStrategyStatus = field(default=ChunkingStrategyStatus.ACTIVE, init=False)

    # ⭐ Single modality (not frozenset!)
    modality: ModalityType

    # Behavior determines which params are required
    behavior: ChunkingBehavior

    # === SPLIT behavior params (TEXT) ===
    chunk_size_tokens: int | None = None  # Required for SPLIT
    chunk_overlap_tokens: int | None = None  # Required for SPLIT
    min_chunk_size_tokens: int | None = None  # Optional for SPLIT
    max_chunk_size_tokens: int | None = None  # Hard limit for SPLIT

    # === PASSTHROUGH behavior params (IMAGE) ===
    max_content_size_bytes: int | None = None  # Required for PASSTHROUGH
    max_width_pixels: int | None = None  # Optional for IMAGE
    max_height_pixels: int | None = None  # Optional for IMAGE

    # === FRAME_EXTRACT behavior params (VIDEO) ===
    frame_sample_rate_fps: float | None = None  # Required for FRAME_EXTRACT
    max_frames: int | None = None  # Optional for FRAME_EXTRACT
    max_video_duration_seconds: int | None = None  # Optional for FRAME_EXTRACT

    # === TIME_SEGMENT behavior params (AUDIO) ===
    segment_duration_seconds: float | None = None  # Required for TIME_SEGMENT
    segment_overlap_seconds: float | None = None  # Required for TIME_SEGMENT
    max_audio_duration_seconds: int | None = None  # Optional for TIME_SEGMENT

    # Implementation-specific config
    config: dict[str, object] = field(default_factory=dict)
    # Examples:
    # SPLIT: {"splitter": "nltk", "respect_paragraphs": true}
    # FRAME_EXTRACT: {"resize_to": [224, 224], "format": "JPEG"}

    # Mutable fields
    _mutable_fields: frozenset[str] = frozenset(
        {
            "name",
            "status",
            "chunk_size_tokens",
            "chunk_overlap_tokens",
            "min_chunk_size_tokens",
            "max_content_size_bytes",
            "max_width_pixels",
            "max_height_pixels",
            "frame_sample_rate_fps",
            "max_frames",
            "max_video_duration_seconds",
            "segment_duration_seconds",
            "segment_overlap_seconds",
            "config",
        }
    )

    def __post_init__(self) -> None:
        """Validate chunking strategy invariants."""
        if not self.name or not self.name.strip():
            msg = "name cannot be empty"
            raise ValueError(msg)

        if not self.model_key or not self.model_key.strip():
            msg = "model_key cannot be empty"
            raise ValueError(msg)

        # MULTIMODAL is forbidden for chunking strategies (embedding-only)
        if self.modality == ModalityType.MULTIMODAL:
            msg = "MULTIMODAL modality is not allowed for chunking strategies (embedding-only)"
            raise ValueError(msg)

        # Validate behavior matches modality
        self._validate_behavior_modality_compatibility()

        # Validate behavior-specific required fields
        if self.behavior == ChunkingBehavior.SPLIT:
            self._validate_split_params()
        elif self.behavior == ChunkingBehavior.PASSTHROUGH:
            self._validate_passthrough_params()
        elif self.behavior == ChunkingBehavior.FRAME_EXTRACT:
            self._validate_frame_extract_params()
        elif self.behavior == ChunkingBehavior.TIME_SEGMENT:
            self._validate_time_segment_params()

        # Assign deterministic UUID v5 based on content (model_key)
        namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
        deterministic_id = uuid.uuid5(namespace, f"chunking:{self.model_key}")
        object.__setattr__(self, "id", ChunkingStrategyId(deterministic_id))

        # Call parent __post_init__ directly due to slots=True issue with super()
        IEntity.__post_init__(self)

    def _validate_behavior_modality_compatibility(self) -> None:
        """Ensure behavior is appropriate for modality."""
        modality = self.modality
        valid_behaviors = VALID_BEHAVIORS_BY_MODALITY.get(modality)

        if not valid_behaviors:
            msg = f"Unknown modality type: {modality}"
            raise ValueError(msg)

        if self.behavior not in valid_behaviors:
            valid_str = ", ".join(sorted(b.value for b in valid_behaviors))
            msg = f"{modality} modality requires one of [{valid_str}] behaviors, got {self.behavior}"
            raise ValueError(msg)

    def _validate_split_params(self) -> None:
        """Validate SPLIT behavior requires text-chunking params."""
        if self.chunk_size_tokens is None or self.chunk_size_tokens <= 0:
            msg = "SPLIT behavior requires positive chunk_size_tokens"
            raise ValueError(msg)

        if self.chunk_overlap_tokens is None or self.chunk_overlap_tokens < 0:
            msg = "SPLIT behavior requires non-negative chunk_overlap_tokens"
            raise ValueError(msg)

        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            msg = "chunk_overlap_tokens must be < chunk_size_tokens"
            raise ValueError(msg)

        if self.min_chunk_size_tokens and self.min_chunk_size_tokens > self.chunk_size_tokens:
            msg = "min_chunk_size_tokens cannot exceed chunk_size_tokens"
            raise ValueError(msg)

        if self.max_chunk_size_tokens and self.chunk_size_tokens > self.max_chunk_size_tokens:
            msg = "chunk_size_tokens cannot exceed max_chunk_size_tokens"
            raise ValueError(msg)

    def _validate_passthrough_params(self) -> None:
        """Validate PASSTHROUGH behavior requires size limits."""
        if self.max_content_size_bytes is None or self.max_content_size_bytes <= 0:
            msg = "PASSTHROUGH behavior requires positive max_content_size_bytes"
            raise ValueError(msg)

    def _validate_frame_extract_params(self) -> None:
        """Validate FRAME_EXTRACT behavior requires frame sampling params."""
        if self.frame_sample_rate_fps is None or self.frame_sample_rate_fps <= 0:
            msg = "FRAME_EXTRACT behavior requires positive frame_sample_rate_fps"
            raise ValueError(msg)

    def _validate_time_segment_params(self) -> None:
        """Validate TIME_SEGMENT behavior requires time-based params."""
        if self.segment_duration_seconds is None or self.segment_duration_seconds <= 0:
            msg = "TIME_SEGMENT behavior requires positive segment_duration_seconds"
            raise ValueError(msg)

        if self.segment_overlap_seconds is None or self.segment_overlap_seconds < 0:
            msg = "TIME_SEGMENT behavior requires non-negative segment_overlap_seconds"
            raise ValueError(msg)

    def activate(self) -> None:
        """Mark strategy as active (production-ready)."""
        object.__setattr__(self, "status", ChunkingStrategyStatus.ACTIVE)
        object.__setattr__(self, "updated_at", utc_now())

    def deprecate(self) -> None:
        """Mark strategy as deprecated (no new usage)."""
        object.__setattr__(self, "status", ChunkingStrategyStatus.DEPRECATED)
        object.__setattr__(self, "updated_at", utc_now())

    def deactivate(self) -> None:
        """Mark strategy as inactive (temporarily disabled)."""
        object.__setattr__(self, "status", ChunkingStrategyStatus.INACTIVE)
        object.__setattr__(self, "updated_at", utc_now())
