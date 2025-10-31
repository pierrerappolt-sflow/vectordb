from __future__ import annotations

from vdb_core.domain.value_objects.common import Status
from vdb_core.domain.value_objects.chunk import ChunkStatusEnum, default_chunk_status
from vdb_core.domain.value_objects.strategy import ModalityType, ModalityTypeEnum


def test_status_wrapper_immutability_and_equality():
    a = Status[ChunkStatusEnum](value=ChunkStatusEnum.PENDING)
    b = default_chunk_status()
    c = Status[ChunkStatusEnum](value=ChunkStatusEnum.PENDING)
    assert a == c
    # default factory should produce same value
    assert b.value == ChunkStatusEnum.PENDING
    # hashable
    s = {a, c}
    assert len(s) == 1


def test_modality_type_defaults_to_text():
    m = ModalityType()
    assert m.value == ModalityTypeEnum.TEXT

    m2 = ModalityType(ModalityTypeEnum.IMAGE)
    assert m2.value == ModalityTypeEnum.IMAGE


