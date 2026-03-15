# M3.12 Integration Verification Report

**Date:** 2026-03-15  
**Integration branch:** integration/m3.12-context-demo  
**Purpose:** Verify M3.12 narrow repo-aware context engine after promotion through feature and integration. Binary result: READY FOR DEMO INTEGRATION or BLOCKED.

---

## 1. Branches used

- **Source branch:** cursor/m3.12-narrow-context-engine  
- **Feature branch:** feature/m3.12-narrow-context-engine  
- **Integration branch:** integration/m3.12-context-demo  

---

## 2. Merge path executed

1. M3.12 implementation committed on cursor/m3.12-narrow-context-engine (commit 7d33414).  
2. feature/m3.12-narrow-context-engine created from main; cursor/m3.12-narrow-context-engine merged in (fast-forward).  
3. integration/m3.12-context-demo created from main; feature/m3.12-narrow-context-engine merged in (fast-forward).  
4. No conflicts. No merge commits (fast-forward only).  

---

## 3. Files changed (corrective fixes)

**None.** No corrective fixes were required during integration verification. All verification checks passed on first run.

---

## 4. Tests run and exact pass counts

**Command run on integration/m3.12-context-demo:**

```bash
python3 -m pytest runtime/tests/test_context_engine.py runtime/tests/test_m312_manifest.py runtime/tests/test_m312_doc_selector.py runtime/tests/test_ask_service.py -v
```

**Result:** 20 passed (6 context_engine + 7 test_m312_manifest + 4 test_m312_doc_selector + 3 test_ask_service).  

Determinism tests (same request/same revision same bundle; same manifest same query same refs; same repo same ask same bundle) all passed. Ask path remains PLAN_ONLY and non-executing.

---

## 5. Ask contract verification result

- **Schema:** Responses conform to plan_only_response.v0.1. No schema bump; repo-aware explanation and provenance use existing fields only (plan_summary.notes, context_bundle.files[].selection_reason).  
- **Invariants:** governance_posture "PLAN_ONLY" and execution false verified on sample ask request. No execution fields imply action beyond plan-only guidance.  
- **Contract check:** handle_ask_request called with valid ask_request; response has required keys and types; selection_reason present per file.  

**Result:** PASS.

---

## 6. Context package verification result

- **Exports:** runtime/context/__init__.py exports are stable and additive (ContextEngine, ContextRequest, SelectedContextRef, ContextBundle, select_from_manifest, ManifestBuilder, RepoManifest, IngestionConfig, ManifestEntry, SectionRange, etc.).  
- **Resolve:** All new public types/modules resolve cleanly (import runtime.context and use of select_from_manifest, ManifestBuilder, RepoManifest, IngestionConfig, ManifestEntry verified).  
- **Structure:** No parallel package structure; M3.12 extends existing runtime/context only.  
- **Ingestion surface:** Limited to intended approved paths per IngestionConfig.default_docs_and_runtime() (docs/**/*.md, docs/runtime/**, runtime/context/*.py, README.md).  

**Result:** PASS.

---

## 7. Integration behavior verification

- **Manifest determinism:** Same revision + same config → same manifest (tests test_same_config_same_revision_same_manifest, test_entry_order_lexicographic passed).  
- **Selector determinism:** Same manifest + same query → same ref list (test_same_manifest_same_query_same_refs passed).  
- **Ask flow:** Uses manifest + doc_selector when repo_root is valid; falls back to existing behavior otherwise; does not call execute_service or sandbox (no execute path in handlers).  
- **Existing runtime:** No changes outside runtime/context and runtime/ask_service; existing runtime tests (test_context_engine, test_ask_service) pass.  

**Result:** PASS.

---

## 8. Plugin compatibility smoke result

- **Plugin build:** ./gradlew build in jetbrains-plugin/ — BUILD SUCCESSFUL.  
- **Ask scenario:** Ask contract remains plan_only_response.v0.1; plugin ask action assumptions (repo_root, revision, query, plan_only response shape) remain compatible.  
- **Contract mismatch:** None introduced; no new required request/response fields.  

**Result:** PASS.

---

## 9. Non-goals preserved

- No embeddings.  
- No vector DB.  
- No generalized RAG platform.  
- No execution from ask path.  
- No plugin redesign.  
- No broad refactor.  

---

## 10. Final binary result

**M3.12 READY FOR DEMO INTEGRATION**

All verification criteria passed. No conflicts. No corrective fixes required. M3.12 is promoted on integration/m3.12-context-demo and is ready for demo orchestration work.

---

*End of M3.12 Integration Verification Report.*
