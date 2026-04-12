"""
Layer-5: Workspace Resolver and Local API Skeleton.

Layer-5 provides deterministic workspace identity resolution, path normalization
for Windows <-> WSL scenarios, and a minimal local API contract for indexing
and retrieval services.

Components:
- workspace: Canonical workspace identity resolution and path normalization
- api: Local HTTP API skeleton (healthz, workspace/resolve, index/status)

Ownership boundaries:
- Layer-5 (A2): workspace identity, root normalization, revision awareness, local API skeleton
- Indexing (A4): indexing internals, operates within resolved workspace
- Retrieval (A5): retrieval ranking, snippet logic, evidence schema
"""

__version__ = "0.1.0"
