"""Configuration-related value objects."""

from .config_status import ConfigStatusEnum
# Backwards-compatible alias for legacy imports
ConfigStatus = ConfigStatusEnum
from .vectorization_config_id import VectorizationConfigId

__all__ = [
    "ConfigStatus",
    "ConfigStatusEnum",
    "VectorizationConfigId",
]
