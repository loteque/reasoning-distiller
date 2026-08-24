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
from .pack_builder import (
    PACK_BUILDER_CONTRACT,
    PACK_CONTRACT,
    ContextPackBuildResult,
    build_context_pack,
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
    "ContextPackBuildResult",
    "CoveAdapterError",
    "CoveSemanticTuple",
    "PACK_BUILDER_CONTRACT",
    "PACK_CONTRACT",
    "PEMS_SEMANTIC",
    "PemsProjectionResult",
    "ProjectedKnowledge",
    "ProjectionCause",
    "ResolvedSource",
    "SERIALIZER",
    "SUPPORTED_TUPLES",
    "SourceResolutionResult",
    "build_context_pack",
    "decode_cove_pems",
    "encode_cove_pems",
    "project_pems",
    "resolve_sources",
]
