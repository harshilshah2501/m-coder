# A6 handoff: Layer-5 lexical retrieval (A5 MVP)

## Entry point

- `retrieve_lexical(index: WorkspaceFileIndex, query: str, top_k: int, config: LexicalRetrievalConfig | None) -> RetrievalResult`
- Module: `runtime.layer5.retrieval`

## Output shape

### `RetrievalResult`

| Field | Type | Meaning |
|-------|------|--------|
| `query_raw` | str | Original query |
| `query_tokens` | tuple[str, ...] | Normalized tokens (sorted lexicographically for stable representation) |
| `top_k` | int | Requested k |
| `hits` | tuple[RetrievalHit, ...] | Up to k hits, deterministically ordered |
| `index_schema_version` | str | Copied from A4 index |
| `workspace_identity_hash` | str | Copied from A4 index |

### `RetrievalHit`

| Field | Type | Meaning |
|-------|------|--------|
| `relative_path` | str | A4 entry path (POSIX, relative to index root) |
| `score` | int | Total MVP score (sum of breakdown) |
| `breakdown` | dict[str, int] | `path_substrings`, `basename_substrings`, `content_substrings` |

**No snippet text, no line numbers, no evidence bundle** — file-level references only.

## Ranking rules (explicit)

1. Tokens: lowercased alphanumeric runs from the query; tokens shorter than `min_token_len` (default 2) are dropped.
2. Per file, integer score = weighted sum of **non-overlapping** substring counts (Python `str.count`):
   - occurrences of each token in full `relative_path` × `weight_path` (default 1)
   - occurrences in basename × `weight_basename` (default 2)
   - occurrences in file body (first `max_content_bytes`, UTF-8 replace) × `weight_content` (default 1), if `read_file_contents` is true
3. Sort by `(-score, relative_path)` ascending (higher score first, then path lexicographic).
4. Empty query or no tokens: first `top_k` index entries in `relative_path` order, all scores `0`.

## Guarantees

1. **A4-only index input**: Uses `WorkspaceFileIndex.files` and `canonical_root`; does not mutate or rebuild the index.
2. **Determinism**: Same `WorkspaceFileIndex` snapshot + same `query` + same on-disk file bytes (for content leg) ⇒ same `hits` order and scores.
3. **Lexical only**: No embeddings, no graph expansion, no symbol boost (A4 v1 has no symbols).
4. **Top-k stable**: Tie-break is always `relative_path` string order.

## Not guaranteed

- Index freshness (A4 may be stale; content reads see live disk).
- Completeness (A4 excludes directories by base name; symlinks omitted by default).
- Cross-machine identical scores if file mtimes/bodies differ.

## Config (`LexicalRetrievalConfig`)

| Field | Default | Role |
|-------|---------|------|
| `min_token_len` | 2 | Short token filter |
| `max_content_bytes` | 262144 | Per-file read cap for content counts |
| `read_file_contents` | True | Path-only mode if false |
| `weight_path` | 1 | Path substring weight |
| `weight_basename` | 2 | Basename substring weight |
| `weight_content` | 1 | Content substring weight |

## Latency snapshot

Honest, unoptimized stdlib-only path+content reads. Example on a dev machine (golden tree, four small files):

- ~200 sequential `retrieve_lexical` calls with default config: about **0.1 ms per call** wall time in one sample (200 calls ≈ 17 ms total); real disks and larger files increase this via `max_content_bytes` reads.

CI guard: `test_lexical_retrieval_latency_smoke` asserts 40 calls complete in under 2 seconds (very loose; catches gross regressions).

Re-run smoke: `python3 -m pytest runtime/layer5/tests/test_lexical_retrieval.py::test_lexical_retrieval_latency_smoke -v`

## A6 implementation (snippets + evidence)

Bounded snippets and **v1** evidence bundles live in `runtime.layer5.evidence` (`build_evidence_bundle`, `schema_hint=layer5.evidence_bundle.v1`). **Do not rescore or reorder A5 hits** when consuming `RetrievalResult`; treat scores and order as authoritative. Strict schema: `runtime/layer5/evidence/evidence_bundle.v1.schema.json`.
