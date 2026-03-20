"""
Layer-5 Local API skeleton.

Provides HTTP endpoints for:
- /healthz: Service health check
- /v1/workspace/resolve: Workspace resolution
- /v1/index/status: Index status query

This skeleton defines the contract; implementations may vary.
"""

from runtime.layer5.api.contracts import (
    WorkspaceResolveRequest,
    WorkspaceResolveResponse,
    IndexStatusRequest,
    IndexStatusResponse,
    HealthResponse,
    IndexState,
)
from runtime.layer5.api.skeleton import Layer5ApiSkeleton

__all__ = [
    "WorkspaceResolveRequest",
    "WorkspaceResolveResponse",
    "IndexStatusRequest",
    "IndexStatusResponse",
    "HealthResponse",
    "IndexState",
    "Layer5ApiSkeleton",
]
