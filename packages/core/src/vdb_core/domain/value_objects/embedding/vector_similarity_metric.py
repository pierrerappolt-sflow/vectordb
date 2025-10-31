"""VectorSimilarityMetric value object - defines how vector similarity is measured."""

from enum import StrEnum, auto
from typing import final


@final
class VectorSimilarityMetric(StrEnum):
    """Value object representing a vector similarity/distance metric.

    Different metrics measure similarity in different ways:
    - COSINE: Cosine similarity (angle between vectors, ignores magnitude)
    - L2: Euclidean distance (straight-line distance, magnitude matters)
    - DOT_PRODUCT: Inner product (both direction and magnitude)
    - L1: Manhattan distance (city-block distance)

    Common pairings:
    - Normalized embeddings: COSINE or DOT_PRODUCT
    - Raw embeddings: L2 or L1
    - Text embeddings: Usually COSINE
    - Image embeddings: Often L2
    """

    COSINE = auto()  # Cosine similarity (angle-based)
    L2 = auto()  # Euclidean distance
    DOT_PRODUCT = auto()  # Inner product
    L1 = auto()  # Manhattan distance
