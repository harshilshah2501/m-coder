# M3.12 Completion Report — Narrow Repo-Aware Context Engine

**Date:** 2026-03-15  
**Milestone:** M3.12 Documentation ingestion (narrow deterministic slice)

---

## Verifiable summary

### M3.12 complete / partial

#### 1. Branches used

- **Source branch:** main
- **Cursor branch:** cursor/m3.12-narrow-context-engine
- **Feature branch:** (to be used for merge: feature/m3.12-narrow-context-engine)
- **Integration branch (if used):** (optional integration/m3.12-context-demo)

#### 2. Files created

- runtime/context/manifest_models.py
- runtime/context/manifest_builder.py
- runtime/context/doc_selector.py
- runtime/context/__init__.py
- runtime/tests/test_m312_manifest.py
- runtime/tests/test_m312_doc_selector.py
- docs/runtime/M3_12_NARROW_CONTEXT_ENGINE_SPEC.md
- docs/runtime/m3.12_demo_scenarios.md
- docs/reports/M3_12_COMPLETION_REPORT.md (this file)

#### 3. Files modified

- runtime/ask_service/handlers.py (manifest + doc_selector integration; plan_summary.notes for repo-aware explanation)
- runtime/tests/test_ask_service.py (added test_ask_same_repo_same_query_same_bundle, test_ask_plan_only_no_execution_coupling; removed unused json import and monkeypatch)

#### 4. Functional result

- **Deterministic ingestion:** ManifestBuilder.build(root_path, revision, config) scans only approved path patterns (docs/**/*.md, docs/runtime/**, runtime/context/*.py, README.md by default), reads files, computes content hash, extracts Markdown headings and Python def/class anchors. No wall-clock fields in RepoManifest; same revision + config → same manifest.
- **Deterministic selector:** select_from_manifest(manifest, query, request) returns SelectedContextRef list by path_match, heading_match, symbol match, and adjacency. Same manifest + query + request → same ref list. Capped by request.max_files.
- **Ask contract:** handle_ask_request builds manifest when repo_root is valid, runs doc_selector, passes selected paths as ContextRequest.files with selectors=["direct"], then ContextEngine.build_context_bundle. Response includes context_bundle.files with path and selection_reason, plan_summary.steps and optional plan_summary.notes (repo-aware explanation). Schema remains plan_only_response.v0.1.
- **PLAN_ONLY guaranteed:** governance_posture "PLAN_ONLY" and execution false in all responses; ask path does not call execute service or sandbox.

#### 5. Tests

**Exact commands run:**

```bash
python3 -m pytest runtime/tests/test_context_engine.py runtime/tests/test_m312_manifest.py runtime/tests/test_m312_doc_selector.py runtime/tests/test_ask_service.py -v
```

**Result:** 20 passed (6 context_engine + 7 test_m312_manifest + 4 test_m312_doc_selector + 3 test_ask_service).

**Skips / accepted limitations:** None. All tests pass.

#### 6. Demo readiness

- Repo-aware ask scenarios added in docs/runtime/m3.12_demo_scenarios.md (context selection, repository context engine doc, Plan-Gate).
- Expected selected bundle behavior: path_match, heading_match, symbol, adjacency; same query → same files; PLAN_ONLY and execution false.
- Unlocks for plugin demo: deterministic repo-aware answers from docs and code anchors without execution; explicit provenance (selection_reason) and short explanation in notes.

#### 7. Non-goals preserved

- No embeddings
- No vector DB
- No generalized RAG platform
- No execution from ask path
- No plugin redesign (schema unchanged)
- No broad refactor (extended existing runtime/context and ask_service only)

#### 8. Final status

**M3.12 READY FOR REVIEW**

---

*End of M3.12 Completion Report.*
