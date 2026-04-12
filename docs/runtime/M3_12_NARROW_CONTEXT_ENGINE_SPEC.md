# M3.12 Narrow Repo-Aware Context Engine — Spec

**Milestone:** M3.12 Documentation ingestion (narrow slice)  
**Layer:** Layer-3 Runtime  
**Scope:** Deterministic documentation ingestion, manifest generation, and repo-aware ask selection. Not a general RAG platform.

---

## 1. Ingestion scope

**In scope:**

- Selected Markdown under `docs/` (e.g. `docs/**/*.md`, `docs/runtime/**`)
- Selected runtime architecture / runtime docs
- Selected source files from approved paths (e.g. `runtime/context/*.py`)
- Top-level `README.md` when present

**Out of scope:**

- PDFs, binaries, arbitrary file zoo
- External web sources
- Embeddings, vector DB, semantic retrieval

Ingestion is configured via `IngestionConfig.path_patterns`. Default: `IngestionConfig.default_docs_and_runtime()`.

---

## 2. Manifest model

- **ManifestEntry:** path (repo-relative), content_hash, file_type, title, headings, section_ranges, symbol_anchors. All deterministic.
- **RepoManifest:** revision, entries. No wall-clock fields (e.g. no `built_at_utc`) in identity-bearing structure so that equality is deterministic.
- **SectionRange:** start_line, end_line (1-based) for bounded sections.
- **IngestionConfig:** path_patterns (glob-style allowlist).

Same repo revision + same config → same manifest (entry order, hashes, headings).

---

## 3. Deterministic selection policy

Selector: `select_from_manifest(manifest, query, request)` → `List[SelectedContextRef]`.

Policy (deterministic only):

1. **Path match:** query tokens vs entry path (substring, case-insensitive).
2. **Title/heading match:** query tokens vs entry.title and entry.headings.
3. **Symbol match:** request.symbol_hints vs entry.symbol_anchors or path.
4. **Adjacency:** same-directory entries from manifest for already-selected paths.

Reasons: `path_match`, `heading_match`, `symbol:hint:<hint>`, `adjacent:dir`. Selector name: `manifest`. Capped by `request.max_files`. Same manifest + query + request → same ref list.

---

## 4. Ask output contract

- **Schema:** plan_only_response.v0.1 (no bump). Repo-aware explanation and provenance expressed via existing fields.
- **Required:** `governance_posture`: `PLAN_ONLY`; `execution`: false; selected files with `path` and `selection_reason`; bounded next steps in `plan_summary.steps`.
- **Repo-aware explanation:** in `plan_summary.notes` (e.g. "Repo-aware selection: N file(s) by path_match, heading_match.").
- No execution, no sandbox, no tool calls from ask path.

---

## 5. Integration

- Ask handler: when `repo_root` is valid, build manifest with default config, run `select_from_manifest`, set `ContextRequest.files` to selected paths, use `selectors=["direct"]`, then existing `ContextEngine.build_context_bundle` materializes. Fallback: existing behavior (selected_file, symbol_hints).
- No change to execute path or Plan-Gate. Governance remains in orchestrator + executor only.

---

## 6. Non-goals

- No embeddings, vector DB, or semantic retrieval.
- No multi-repo support.
- No autonomous code editing or command execution from ask.
- No plugin redesign beyond existing ask contract.
- No broad runtime refactor.
