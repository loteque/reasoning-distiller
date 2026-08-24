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
    PACK_BUILDER_CONTRACT_V1,
    PACK_BUILDER_CONTRACT_V2,
    PACK_CONTRACT,
    PACK_CONTRACT_V1,
    PACK_CONTRACT_V2,
    ContextPackBuildResult,
    build_context_pack,
)
from .pems_projection import (
    PemsProjectionResult,
    ProjectedKnowledge,
    ProjectionCause,
    project_pems,
)
from .persistence_adapter import (
    IMMUTABLE_OUTPUT_COLLISION,
    NO_CHANGE,
    PERSISTED,
    ImmutableOutputCollisionError,
    PersistenceBoundaryError,
    PersistenceResult,
    persist_immutable_artifact,
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
    "IMMUTABLE_OUTPUT_COLLISION",
    "ImmutableOutputCollisionError",
    "NO_CHANGE",
    "PACK_BUILDER_CONTRACT",
    "PACK_BUILDER_CONTRACT_V1",
    "PACK_BUILDER_CONTRACT_V2",
    "PACK_CONTRACT",
    "PACK_CONTRACT_V1",
    "PACK_CONTRACT_V2",
    "PEMS_SEMANTIC",
    "PERSISTED",
    "PersistenceBoundaryError",
    "PersistenceResult",
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
    "persist_immutable_artifact",
    "project_pems",
    "resolve_sources",
]
