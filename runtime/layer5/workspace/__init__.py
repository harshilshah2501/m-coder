"""
Workspace identity resolution and path normalization.

Provides deterministic canonical workspace root resolution for Windows <-> WSL scenarios.
"""

from runtime.layer5.workspace.identity import (
    WorkspaceIdentity,
    WorkspaceRevision,
    WorkspaceError,
    WorkspaceErrorCode,
)
from runtime.layer5.workspace.resolver import (
    WorkspaceResolver,
    ResolverConfig,
)
from runtime.layer5.workspace.path_normalizer import (
    PathNormalizer,
    PathNormalizationResult,
)

__all__ = [
    "WorkspaceIdentity",
    "WorkspaceRevision",
    "WorkspaceError",
    "WorkspaceErrorCode",
    "WorkspaceResolver",
    "ResolverConfig",
    "PathNormalizer",
    "PathNormalizationResult",
]
