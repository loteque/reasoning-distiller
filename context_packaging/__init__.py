"""Deterministic context-packaging primitives."""

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
    "PemsProjectionResult",
    "ProjectedKnowledge",
    "ProjectionCause",
    "ResolvedSource",
    "SourceResolutionResult",
    "project_pems",
    "resolve_sources",
]
