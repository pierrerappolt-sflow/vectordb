"""VectorIndexingStrategy value object - defines the data structure for storing/searching vectors."""

from enum import StrEnum, auto
from typing import final


@final
class VectorIndexingStrategy(StrEnum):
    """Value object representing a vector index data structure.

    Different strategies optimize for different trade-offs (speed vs accuracy vs memory):
    - HNSW: Hierarchical Navigable Small World (fast ANN, high memory)
    - IVF: Inverted File Index (clustering-based, good for large datasets)
    - FLAT: Brute force exact search (slow but accurate)
    - PQ: Product Quantization (compressed vectors, lower memory)
    """

    HNSW = auto()  # Hierarchical Navigable Small World
    IVF = auto()  # Inverted File Index
    FLAT = auto()  # Brute force exact search
    PQ = auto()  # Product Quantization
