"""ModalityType - content modality as a single enum."""

from enum import StrEnum


class ModalityType(StrEnum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    MULTIMODAL = "MULTIMODAL"
