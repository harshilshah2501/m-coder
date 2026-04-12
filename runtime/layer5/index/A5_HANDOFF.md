# A5 handoff: Layer-5 file index (A4 MVP)

## What exists

- **Module**: `runtime.layer5.index`
- **Entry point**: `build_file_index(identity: WorkspaceIdentity, config: FileIndexConfig | None) -> WorkspaceFileIndex`
- **Stable serialization**: `WorkspaceFileIndex.canonical_json()` — deterministic for a fixed on-disk tree (no timestamps in the payload)

## JSON shape (`to_canonical_dict` / `canonical_json`)

| Field | Type | Meaning |
|-------|------|--------|
| `schema_version` | string | Constant `layer5.file_index.v1`; bump if shape changes |
| `workspace_identity_hash` | string | Copied from `WorkspaceIdentity.identity_hash` (A2) at build time |
| `canonical_root` | string | `Path(identity.canonical_root).resolve()` used as walk root |
| `files` | array | Sorted by `relative_path` (lexicographic) |

Each element of `files`:

| Field | Type | Meaning |
|-------|------|--------|
| `relative_path` | string | Path relative to `canonical_root`, POSIX `/` separators |
| `size_bytes` | int | `st_size` |
| `mtime_ns` | int | `st_mtime_ns` if present, else `int(st_mtime * 1e9)` |

## Guarantees

1. **Scope**: Only files discovered under the resolved workspace root from A2 (`WorkspaceIdentity.canonical_root`). No indexing outside that tree via `os.walk`.
2. **Determinism**: Same filesystem contents and same `identity` fields used at build → same `canonical_json()` byte-for-byte. Traversal uses sorted directory and file names; `files` are sorted by `relative_path`.
3. **Granularity**: **File-level entries are always present.** **Symbol-level index is not implemented** (no `symbols` field).
4. **Lifecycle**: **Full rebuild only** — call `build_file_index` again. `index_matches_workspace(index, identity)` only checks identity hash + resolved root string equality; it does **not** detect changed files.

## Not provided

- Ranking, retrieval, snippets, embeddings
- Incremental/dirty diff indexing
- AST or multi-language parsing; regex symbol extraction (skipped in MVP)
- Graphs or cross-file relationships
- Normalization of paths beyond `Path.resolve()` for the root and `relative_to` for entries

## Config (`FileIndexConfig`)

- `exclude_dir_names`: pruned directory **base names** (compared case-insensitively); default set includes `.git`, `node_modules`, `__pycache__`, `.venv`, `build`, `dist`, `.gradle`, `target`, etc.
- `follow_symlinks`: default `False` — symlink files are skipped; symlink directories are not followed unless `True`.
