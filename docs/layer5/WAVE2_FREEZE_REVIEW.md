# Wave-2 Freeze Review — Layer-5 Workspace Intelligence

**Update (Wave-2.5):** A6 evidence shipped as **`layer5.evidence_bundle.v1`** with strict `evidence_bundle.v1.schema.json`, frozen `selection_reason` enum, golden fingerprint, and `IdentityMismatchError` policy. Earlier references below to `v0_provisional` / loose schema describe the pre-fix state.

## 1. Executive Summary

- **A4 (index)**: Shipped as `layer5.file_index.v1`. Deterministic file-level index under A2-resolved root; full rebuild lifecycle; no symbols.
- **A5 (retrieval)**: Lexical-only `retrieve_lexical` over A4 snapshot; deterministic `(-score, relative_path)` ordering; integer breakdown (path / basename / content substring counts).
- **A6 (evidence)**: `build_evidence_bundle` produces **provisional** bundles; snippets are bounded line windows with fixed anchor rules; A5 scores/order are copied, not recomputed.

**What is working**

- End-to-end chain: A4 index → A5 candidates → A6 grounded entries with traceable line/byte spans (capped-file semantics).
- Determinism: A4 canonical JSON; A5 hits given fixed index + file bytes; A6 `to_json()` stable for fixed inputs.
- Explicit non-goals documented in handoffs (no graph, no embeddings, no symbol index).

**What is still provisional**

- A6 contract: `schema_hint=layer5.evidence_bundle.v0_provisional`, `provisional: true`, JSON Schema allows `additionalProperties` everywhere.
- Cross-layer “freeze” artifacts: no published schema `$id`, no golden bundle hashes, no prod policy for identity mismatch.

**One-line conclusion:** **NEEDS FIXES** (evidence contract **not** ready to freeze; A4/A5 behavior is comparatively stable but not formally declared frozen in this review).

---

## 2. A4 — Index Guarantees

**Guarantees**

- **Determinism**: Same tree + same identity inputs at build → identical `WorkspaceFileIndex.canonical_json()` (sorted traversal, no wall-clock fields in canonical payload).
- **File coverage scope**: Only paths under resolved workspace root from A2; `files[]` sorted by `relative_path` (POSIX).
- **Schema version**: String `layer5.file_index.v1` (`schema_version` on index).

**Does NOT guarantee**

- **Freshness**: `index_matches_workspace` does not detect file edits; rebuild is caller’s responsibility.
- **Symbols**: No symbol-level field; file-level only.
- **Completeness**: Directory excludes by **base name** (e.g. `.git`, `node_modules`, `build`, …); default `follow_symlinks=False` omits symlink files; not all repo files appear.

---

## 3. A5 — Retrieval Guarantees

**Guarantees**

- **Deterministic ranking**: Integer score from weighted `str.count` on path, basename, optional file body (capped); sort `(-score, relative_path)`.
- **Lexical-only**: Substring counts only; no embeddings, graph, or symbol boost (A4 has no symbols).
- **Explainable breakdown**: `path_substrings`, `basename_substrings`, `content_substrings` sum to `score`.

**Does NOT guarantee**

- **Semantic correctness**: Top hits are not “meaning”-optimal; short-token substring bias applies.
- **Freshness**: Index snapshot vs **live** content reads for scoring.
- **Completeness**: Limited to A4-listed files and caps (`max_content_bytes` per file).

**Ranking philosophy**: Simple, repeatable, auditable integers; tie-break by path only.

---

## 4. A6 — Evidence Contract (Current State)

- **EvidenceBundle**: `provisional`, `schema_hint`, echoes `query_raw`, `query_tokens`, `top_k`, `index_schema_version`, `workspace_identity_hash`, `canonical_root`, `a5_authority_note`, `entries[]`.
- **EvidenceEntry**: `rank` (0-based, A5 order), `relative_path`, `retrieval_score` / `retrieval_breakdown` (**verbatim A5**), nested `snippet`.
- **Snippet**: `text`, `start_line`/`end_line` (1-based; `0` when no span e.g. missing file), `start_byte_utf8`/`end_byte_utf8` (UTF-8 offsets into **capped** decoded file; end exclusive per `provisional_schema.md`), `anchor_line`, `matched_tokens` (sorted), `selection_reason`, `truncated_by_max_bytes`.
- **Selection rules (code)**: First physical line (top-down) whose body contains any query token as substring → anchor; else line 1 with `no_query_token_in_body_file_start`; empty tokens → `no_query_tokens_file_start`; I/O → `file_missing` / `file_unreadable` / `empty_file`. Window = `[anchor − context_before, anchor + context_after]` clamped.
- **Determinism**: Same `RetrievalResult` + same `WorkspaceFileIndex` (identity match) + same file bytes → same `EvidenceBundle.to_json()` (breakdown keys sorted in dict export).

👉 **This contract is currently PROVISIONAL** (`v0_provisional`; breaking changes expected until freeze).

---

## 5. Freeze Boundary Definition

### What WILL be frozen at Wave-2 exit (target surface)

- **Evidence fields (bundle)**: `provisional`, `schema_hint`, `query_raw`, `query_tokens`, `top_k`, `index_schema_version`, `workspace_identity_hash`, `canonical_root`, `a5_authority_note`, `entries`.
- **Evidence fields (entry)**: `provisional`, `rank`, `relative_path`, `retrieval_score`, `retrieval_breakdown`, `snippet` (with nested fields as in §4).
- **Ordering guarantees**: `entries` order equals A5 `hits` order; `rank` matches enumeration.
- **Snippet bounding rules**: Configurable `context_lines_before` / `context_lines_after`, `max_file_bytes`; anchor selection as specified in `snippet.py` (frozen verbatim or versioned).
- **`selection_reason`**: Closed set (see §6): `query_token_substring_anchor`, `no_query_token_in_body_file_start`, `no_query_tokens_file_start`, `file_missing`, `file_unreadable`, `empty_file`.
- **`schema_hint`**: Versioned string (e.g. `layer5.evidence_bundle.v1` post-freeze); `provisional` flips to `false` only when checklist passes.

### What will remain flexible (post-freeze evolution allowed)

- **A5 scoring internals**: Weights, `min_token_len`, `read_file_contents`, caps (unless product locks them).
- **Snippet heuristics**: Anchor logic beyond freeze may get a **new** `schema_hint` / major version.
- **Performance**: Per-query full-file reads for all index entries remain a scaling concern; not contract-frozen.

---

## 6. Required Fixes Before Freeze (CRITICAL)

| Issue | Why it matters | Required fix |
|--------|----------------|--------------|
| JSON Schema uses `additionalProperties: true` on bundle, entry, snippet | Consumers cannot validate or reject unknown fields; contract drift is invisible | Set `additionalProperties: false` (or explicit `patternProperties` only where intended); align `provisional_schema.json` with emitted payloads. |
| `selection_reason` is unconstrained `string` in JSON Schema | Typos / new values slip through without version bump | Enumerate allowed values in schema + document as normative enum; add tests for each path. |
| Byte offset semantics split between prose and code | Off-by-one or exclusive/inclusive bugs across UTF-8, cap, replacement chars | Single normative paragraph + examples (empty file, multi-byte char, truncated tail); verify against `extract_snippet` implementation. |
| Identity mismatch: `ValueError` in builder only | Prod API needs fail vs warn vs strip policy | Write explicit policy; integration test for chosen behavior; document in bundle or HTTP contract. |
| No golden bundle fixtures with expected hashes | Regressions in JSON shape go unnoticed | Export fixture(s) from tests, record SHA-256 (or similar) in repo; CI compare. |
| `schema_hint` / `$id` still “provisional” | Registry and codegen cannot anchor | Bump to non-provisional version string; publish stable `$id` URL or repo path; changelog entry. |
| Sample `example_bundle.json` is synthetic | Drift from real `to_json()` output | Regenerate from test helper or assert round-trip validate against strict schema. |
| A4/A5 cross-version matrix absent | Index v2 vs evidence v1 ambiguity | Short compatibility table (which `index_schema_version` pairs with which evidence `schema_hint`). |

---

## 7. Known Limitations (Accepted for Now)

- **Staleness**: Index snapshot vs live reads (A5 content leg, A6 snippet) — documented; not fixable in Wave-2 without new product requirements.
- **Substring anchoring**: False positives / odd windows for short tokens — accepted for MVP lexical stack.
- **Partial visibility**: A4 excludes whole subtrees by directory basename; symlinks skipped by default — retrieval/evidence only see indexed files.
- **Resolver test environment**: `runtime/layer5/tests/test_workspace_resolver.py` can fail when cwd is a non-git path such as `/workspace/runtime/layer5` — environment caveat, not a Layer-5 contract defect.
- **A3 / latency**: A5 handoff notes honest latency samples; **not** a full integrated product path or SLO — accepted scope boundary for Wave-2.

---

## 8. Freeze Checklist Evaluation

Source: `runtime/layer5/evidence/FREEZE_CHECKLIST.md`

| Item | Status | Comment |
|------|--------|---------|
| `schema_hint` version bumped + changelog | **pending** | Still `v0_provisional`; no freeze changelog. |
| `provisional_schema.md` matches shipped JSON | **pending** | Align with strict schema + code after fixes. |
| `provisional_schema.json` aligned / published `$id` | **pending** | Draft-07 file exists; `$id` is URN placeholder; `additionalProperties` loose. |
| Byte offset semantics documented | **partial** | Described in markdown; needs normative closure (§6). |
| `selection_reason` frozen or namespaced | **pending** | Values exist in code; not in schema enum. |
| A4 index schema compatibility matrix | **pending** | Not written. |
| A5 ranking stable doc link | **partial** | `A6_HANDOFF.md` duplicates rules; no single canonical link. |
| A6 no-rescore in integration tests | **partial** | Unit tests assert score/order copy; no full-stack integration test. |
| Max read caps prod vs dev | **pending** | Defaults only; no signed-off limits. |
| Staleness story for product | **partial** | Technical handoffs state it; product-facing signoff missing. |
| PII / secrets in snippet text | **pending** | No review record. |
| Golden bundle fixtures + hashes | **pending** | Only illustrative `samples/example_bundle.json`. |
| Identity-mismatch policy for prod API | **pending** | Code raises `ValueError`; API behavior undefined. |

---

## 9. GO / NO-GO Decision

| Decision | Verdict |
|----------|---------|
| **Freeze A6 evidence contract now** | **NO-GO** |
| **Treat A4 index JSON as frozen** | **GO** for engineering use of `layer5.file_index.v1` as implemented; formal governance freeze still benefits from checklist items (matrix, changelog). |
| **Treat A5 retrieval output as frozen** | **GO** for behavior as documented in `A6_HANDOFF.md`; weight/cap tuning remains intentionally flexible. |

**Blocking items for A6 freeze only** (minimal):

1. Strict JSON Schema (no stray `additionalProperties` on frozen objects).
2. Frozen `selection_reason` enum + tests.
3. Normative byte-offset + truncation semantics.
4. Golden bundle fixture(s) + hash(es) in CI.
5. Published `schema_hint` / `$id` for non-provisional bundle version.
6. Identity-mismatch policy documented + tested for intended integration surface.

---

## 10. Recommendation for A7/A8

- **A7/A8 may start** against **provisional** `layer5.evidence_bundle.v0_provisional` **if** they: version-gate on `schema_hint`, tolerate schema tightening, and avoid hard-coding loose validation.
- **They should not** assume the evidence contract is production-frozen until §9 blocking items are cleared.
- **Recommended sequencing**: Parallelize A7/A8 **spec/API design** with freeze-fix work; defer **immutable** client contracts until strict schema + golden hashes land.

---

*Artifact type: freeze decision review. Not a design specification.*
