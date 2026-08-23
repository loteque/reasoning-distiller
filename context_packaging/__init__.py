"""Deterministic context-packaging primitives."""

from .cove_adapter import (
    COVE_SEMANTIC,
    PEMS_SEMANTIC,
    SERIALIZER,
    SUPPORTED_TUPLES,
    CoveAdapterError,
    CoveSemanticTuple,
    decode_cove_pems,
    encode_cove_pems,
)
from .pems_projection import (
    PemsProjectionResult,
    ProjectedKnowledge,
    ProjectionCause,
    project_pems,
)
from .source_resolver import (
    AdapterResult,
    ResolvedSource,
    SourceResolutionResult,
    resolve_sources,
)

__all__ = [
    "AdapterResult",
    "COVE_SEMANTIC",
    "CoveAdapterError",
    "CoveSemanticTuple",
    "PEMS_SEMANTIC",
    "PemsProjectionResult",
    "ProjectedKnowledge",
    "ProjectionCause",
    "ResolvedSource",
    "SERIALIZER",
    "SUPPORTED_TUPLES",
    "SourceResolutionResult",
    "decode_cove_pems",
    "encode_cove_pems",
    "project_pems",
    "resolve_sources",
]
