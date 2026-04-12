# Layer-5: Workspace Resolver and Local API Skeleton

**Owner:** A2 (Workspace Resolver + Local API Skeleton)  
**Status:** v0.1.0 — Initial implementation  
**Wave:** Layer-5 Wave 1

## Overview

Layer-5 provides deterministic workspace identity resolution, path normalization for Windows <-> WSL scenarios, and a minimal local API contract for indexing and retrieval services.

### Ownership Boundaries

| Component | Owner | Responsibility |
|-----------|-------|----------------|
| Workspace identity | A2 | Canonical root resolution, identity hash |
| Path normalization | A2 | Windows/WSL/POSIX path conversion |
| Revision metadata | A2 | Git branch/commit/dirty-state shape |
| Local API skeleton | A2 | healthz, workspace/resolve, index/status endpoints |
| Indexing internals | A4 | Index implementation inside resolved workspace |
| Retrieval ranking | A5 | Snippet logic, evidence schema |

## Quick Start

### Resolve a Workspace

```python
from runtime.layer5.workspace import WorkspaceResolver

resolver = WorkspaceResolver()
identity, error = resolver.resolve("C:\\Users\\dev\\project\\src\\main.py")

if error:
    print(f"Error: {error.code.value}: {error.message}")
else:
    print(f"Canonical root: {identity.canonical_root}")
    print(f"Identity hash: {identity.short_identity()}")
    print(f"Git repo: {identity.is_git_repo}")
    if identity.revision:
        print(f"Branch: {identity.revision.branch}")
        print(f"Commit: {identity.revision.short_sha()}")
        print(f"Dirty: {identity.revision.is_dirty}")
```

### Normalize a Path

```python
from runtime.layer5.workspace import PathNormalizer

# Windows to WSL
result = PathNormalizer.normalize("C:\\Users\\dev\\project")
print(result.canonical_path)  # /mnt/c/Users/dev/project

# Check equivalence
PathNormalizer.paths_equivalent(
    "C:\\Users\\dev\\project",
    "/mnt/c/Users/dev/project"
)  # True
```

### Run the Local API

```python
from runtime.layer5.api import Layer5ApiSkeleton, ApiConfig

config = ApiConfig(host="127.0.0.1", port=8090)
api = Layer5ApiSkeleton(config)
api.serve()  # Blocks and serves HTTP
```

Or from command line:
```bash
python -m runtime.layer5.api.skeleton
```

## API Endpoints

### GET /healthz

Health check endpoint.

**Response:**
```json
{
  "schema_version": "health.v1",
  "status": "ok",
  "version": "0.1.0",
  "timestamp_utc": "2024-01-15T10:30:00+00:00",
  "components": {
    "workspace_resolver": "ok",
    "index_status": "stub"
  }
}
```

### POST /v1/workspace/resolve

Resolve workspace identity from a path.

**Request:**
```json
{
  "input_path": "C:\\Users\\dev\\project\\src\\main.py",
  "require_git": false,
  "include_revision": true
}
```

**Success Response:**
```json
{
  "schema_version": "workspace_resolve_response.v1",
  "success": true,
  "canonical_root": "/mnt/c/Users/dev/project",
  "identity_hash": "a1b2c3d4e5f6...",
  "path_type": "windows",
  "is_git_repo": true,
  "revision": {
    "commit_sha": "abc123def456...",
    "branch": "main",
    "is_dirty": false,
    "is_detached": false,
    "tags": ["v1.0.0"],
    "timestamp_utc": "2024-01-15T10:30:00+00:00"
  },
  "resolved_at_utc": "2024-01-15T10:30:00+00:00"
}
```

**Error Response:**
```json
{
  "schema_version": "workspace_resolve_response.v1",
  "success": false,
  "error_code": "workspace_not_found",
  "error_message": "No workspace root found within 50 levels",
  "resolved_at_utc": "2024-01-15T10:30:00+00:00"
}
```

### POST /v1/index/status

Query index status for a workspace. (Stub implementation — A4 will implement actual tracking.)

**Request:**
```json
{
  "workspace_identity_hash": "a1b2c3d4e5f6..."
}
```

**Response:**
```json
{
  "schema_version": "index_status_response.v1",
  "workspace_identity_hash": "a1b2c3d4e5f6...",
  "state": "not_indexed",
  "file_count": 0,
  "checked_at_utc": "2024-01-15T10:30:00+00:00"
}
```

## Path Normalization Rules

### Input Types

| Type | Example | Detection |
|------|---------|-----------|
| Windows | `C:\Users\dev\project` | Drive letter pattern `[A-Za-z]:[/\\]` |
| WSL | `/mnt/c/Users/dev/project` | `/mnt/[a-z]/` prefix |
| POSIX | `/home/user/project` | Starts with `/`, not `/mnt/` |
| UNC | `\\server\share\path` | `\\` or `//` prefix |

### Normalization Rules (Precedence Order)

1. Detect input path type (Windows, WSL, POSIX, UNC)
2. Convert to canonical POSIX form with forward slashes
3. For Windows paths, convert drive letter to `/mnt/{drive}/...`
4. Lowercase drive letters for consistency
5. Resolve symlinks (when filesystem accessible)
6. Remove trailing slashes

### Examples

| Input | Output | Type |
|-------|--------|------|
| `C:\Users\dev\project` | `/mnt/c/Users/dev/project` | windows |
| `D:/Projects/app` | `/mnt/d/Projects/app` | windows |
| `/mnt/c/Users/dev/project` | `/mnt/c/Users/dev/project` | wsl |
| `/home/user/project` | `/home/user/project` | posix |
| `\\server\share\path` | `/mnt/server/share/path` | unc |

## Workspace Root Resolution

### Root Markers (Precedence Order)

1. `.git` — Git repository root
2. `.workspace` — Explicit workspace marker
3. `pyproject.toml` — Python project
4. `package.json` — Node.js project
5. `Cargo.toml` — Rust project
6. `go.mod` — Go project
7. `pom.xml` — Maven project
8. `build.gradle` — Gradle project
9. `CMakeLists.txt` — CMake project
10. `Makefile` — Generic makefile

### Resolution Algorithm

```
1. Normalize input path to canonical POSIX form
2. If input is a file, start from parent directory
3. Walk up directory tree (max 50 levels)
4. Check each marker in precedence order
5. Return first match as workspace root
6. If no marker found and fallback_to_input=True, use start directory
7. Compute identity hash (SHA-256 of lowercased canonical root)
8. Capture git revision metadata if available
```

## Revision Metadata Shape

```python
@dataclass
class WorkspaceRevision:
    commit_sha: str           # Full 40-char SHA, or "unversioned"
    branch: Optional[str]     # Branch name, None if detached/no git
    is_dirty: bool            # Uncommitted changes present
    is_detached: bool         # HEAD is detached (not on branch)
    tags: List[str]           # Tags pointing to HEAD
    timestamp_utc: str        # When revision info was captured
```

## Error Model

### Error Codes

| Code | Description |
|------|-------------|
| `workspace_not_found` | No workspace root found within max depth |
| `path_outside_workspace` | Path is outside resolved workspace |
| `invalid_path_format` | Empty or malformed path |
| `normalization_failed` | Could not normalize path |
| `git_not_initialized` | require_git=True but no .git found |
| `revision_unavailable` | Could not read git revision info |
| `ambiguous_root` | Multiple potential roots (not implemented) |
| `permission_denied` | Filesystem permission error |

### Error Response Shape

```python
@dataclass
class WorkspaceError:
    code: WorkspaceErrorCode
    message: str
    input_path: Optional[str]
    details: Optional[Dict[str, Any]]
```

## Handoff Notes for A4 (Indexing)

### Assumptions A4 Can Rely On

1. **Deterministic Identity:** Same input path always produces same `identity_hash`
2. **Canonical Root:** All files to index are under `canonical_root`
3. **Path Format:** `canonical_root` is always POSIX-style with forward slashes
4. **Revision Stability:** `WorkspaceRevision` shape is stable; extend via `details` dict if needed
5. **API Contract:** `/v1/index/status` contract is stable; A4 implements actual tracking

### Integration Pattern

```python
from runtime.layer5.workspace import WorkspaceResolver
from runtime.layer5.api import Layer5ApiSkeleton, IndexStatusResponse, IndexState

# 1. Resolve workspace
resolver = WorkspaceResolver()
identity, error = resolver.resolve(user_provided_path)
if error:
    # Handle error
    pass

# 2. Use canonical_root for indexing
index_directory(identity.canonical_root)

# 3. Track index status (A4 implements this)
def get_index_status(identity_hash: str) -> IndexStatusResponse:
    # A4's index tracking logic here
    return IndexStatusResponse(
        workspace_identity_hash=identity_hash,
        state=IndexState.INDEXED,
        indexed_revision=identity.revision.commit_sha if identity.revision else None,
        file_count=count_indexed_files(identity_hash),
    )

# 4. Plug into API skeleton
api = Layer5ApiSkeleton()
api.set_index_status_callback(get_index_status)
api.serve()
```

### File Discovery

A4 should use `canonical_root` as the base for all file operations:

```python
from pathlib import Path

root = Path(identity.canonical_root)
for file_path in root.rglob("*.py"):
    relative_path = file_path.relative_to(root)
    # Index file using relative_path
```

## Testing

Run tests:
```bash
cd /workspace
python -m pytest runtime/layer5/tests/ -v
```

## Legacy Compatibility

For codebases that previously used `runtime.context.selectors._normalize_root()`:

```python
# Old way
from runtime.context.selectors import _normalize_root
root = _normalize_root("/some/path")

# New way (Layer-5)
from runtime.layer5.workspace import PathNormalizer
result = PathNormalizer.normalize("/some/path")
root = result.canonical_path
```

The Layer-5 normalizer is a superset that handles Windows/WSL paths in addition to POSIX.
