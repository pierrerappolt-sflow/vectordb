"""ContentHash value object."""

import hashlib
from typing import final

from pydantic.dataclasses import dataclass


@final
@dataclass(frozen=True, slots=True)
class ContentHash:
    """Deterministic SHA1 hash of content."""

    value: str

    @classmethod
    def from_content(cls, content: str) -> "ContentHash":
        hash_value = hashlib.sha1(content.encode("utf-8"), usedforsecurity=False).hexdigest()
        return cls(value=hash_value)

    @classmethod
    def from_bytes(cls, content: bytes) -> "ContentHash":
        hash_value = hashlib.sha1(content, usedforsecurity=False).hexdigest()
        return cls(value=hash_value)

    @classmethod
    def from_chunk_components(
        cls,
        document_id: str,
        strategy_name: str,
        start: int,
        end: int,
        text: str,
    ) -> "ContentHash":
        content = f"{document_id}:{strategy_name}:{start}:{end}:{text}"
        return cls.from_content(content)

    @classmethod
    def from_normalized_text(cls, text: str) -> "ContentHash":
        normalized = " ".join(text.lower().split())
        return cls.from_content(normalized)
