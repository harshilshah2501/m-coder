# Phase 5 — Layer-4 Observation Structure Audit Report

**Repository:** m-coder  
**Audit phase:** Phase 5 only (Layer-4 observation structural audit, read-only)  
**Date:** 2026-03-15  
**Scope:** Top-level observation/, runtime/observation/, dual-tree split, CLI/tool vs library boundary, public/internal surfaces, path contracts, docs clarity, cross-layer coupling. No moves, renames, edits, or remediation performed.

---

## 1. Purpose and scope

This document is the deliverable for **Phase 5** of the m-coder structural audit. It is a **read-only structural audit** of **Layer-4 observation** only. It does not move or rename files, edit docs or code, refactor, clean up reports, or perform remediation. The audit inventories Layer-4 anchors, classifies both observation trees, assesses dual-tree coherence, CLI vs library boundary, public vs internal surfaces, runtime-schema coupling, docs-placement clarity, path-contract sensitivity, and cross-layer leakage.

---

## 2. Executive assessment

- **Overall Layer-4 structural health:** Good with a **docs-placement gap**. Layer-4 is canonically anchored in docs (docs/LAYER4_OBSERVATION_SPEC.md, docs/OBSERVATION/README.md, observation/README.md) and in two code trees: **observation/** (top-level) and **runtime/observation/** (under runtime). The **top-level observation/** tree is the Layer-4 operator/CLI boundary: ingest (validate, reconcile, report), baseline (baseline/compare modes, drift thresholds), and judge_drift_suite (runner, coverage metrics, weekly report, verdict normalizer). It does **not** import runtime.observation; it only references **runtime schema file paths** (runtime/schemas, runtime/ide/schemas, runtime/shadow/schemas) for validation in observation/ingest/validate.py and ingest/cli.py — disciplined, read-only schema coupling. The **runtime/observation/** tree is the Layer-4 implementation library (M4.1–M4.6): TraceBuilder, RuntimeSummaryQueries, ExplanationBuilder, BaselineBuilder, BaselineStore, CollapseClassifier, CollapseQueryService, LedgerReconciliationService, GREG escalation/bundle, RuntimeMetricsService. It is consumed by runtime/tests and by runtime code (trace_builder, summary_queries, reconciliation, runtime_metrics use runtime.sandbox.sandbox_ledger_store and runtime.ledger.store). It also exposes one CLI: report_runtime_summary (python -m runtime.observation.report_runtime_summary). The **split is structurally coherent**: boundary/CLI vs runtime-consumed library; no duplicate responsibility (root does not reimplement trace/baseline/collapse/reconciliation). The **canonical spine does not document this split**: LAYER4_OBSERVATION_SPEC says “Directory: observation/” only; ARCHITECTURE_4_LAYER says “Layer-4: observation/” only; observation/README and docs/OBSERVATION/README do not mention runtime/observation/. So the **biggest risk** is docs-placement: a new contributor cannot infer from the spine that Layer-4 has two trees. Phase 1 and Phase 4 already identified this; this phase confirms it and adds the full Layer-4 inventory and path-contract register.

- **Does Layer-4 have a clear canonical anchor?** Partially. The **spec anchor** is clear: docs/LAYER4_OBSERVATION_SPEC.md and docs/OBSERVATION/README.md (and observation/README.md). The **code anchor** is split: observation/ (boundary) and runtime/observation/ (library). The split is not stated in the spine.

- **Biggest Layer-4 structural risks:** (1) **Dual-tree split not in spine** — no canonical sentence that observation/ = boundary/CLI and runtime/observation/ = runtime-consumed library. (2) **Dual observation index paths** — docs/OBSERVATION/README.md vs observation/README.md; on case-sensitive systems “OBSERVATION” and “observation” are different paths; MASTER_SYSTEM_SPEC links to OBSERVATION/README (docs). (3) **Milestone docs carry structural truth** — M4.1–M4.6 milestone docs are the only place that list runtime/observation/ modules; architecture should not rely on milestone docs for ownership.

---

## 3. Layer-4 canonical spine

For each major Layer-4 anchor we state: path; role; canonical / pointer / supporting; whether it competes; confidence.

| Anchor | Path | Role | Canonical / pointer / supporting | Competes? | Confidence |
|--------|------|------|----------------------------------|-----------|-------------|
| Layer-4 comprehensive spec | docs/LAYER4_OBSERVATION_SPEC.md | Purpose, ingest, baseline, drift, collapse, GREG, thresholds; “Directory: observation/” | canonical | No | **partially clear** (single dir only) |
| Layer-4 index (docs) | docs/OBSERVATION/README.md | Layer-4 index; ingest, baseline; links to observation/ingest, observation/baseline | canonical pointer | Dual with observation/README | **partially clear** (case; no runtime/observation) |
| Layer-4 package README | observation/README.md | Purpose, boundaries, ingest, baseline, judge_drift_suite, drift, GREG; links to ARCHITECTURE_4_LAYER | canonical pointer | Dual with docs/OBSERVATION | **partially clear** (no runtime/observation) |
| Top-level observation tree | observation/ | Ingest CLI, baseline CLI, judge_drift_suite; operator/tool boundary | canonical | No | **clear** |
| Runtime observation library | runtime/observation/ | M4.1–M4.6 library; trace, baseline, collapse, reconciliation, GREG, metrics; report_runtime_summary CLI | canonical (library) | No | **partially clear** (docs) |
| MASTER_SYSTEM_SPEC | docs/MASTER_SYSTEM_SPEC.md | Links to OBSERVATION/README.md, LAYER4_OBSERVATION_SPEC | pointer | No | **clear** |
| ARCHITECTURE_4_LAYER | docs/ARCHITECTURE_4_LAYER.md | “Layer-4: observation/”; allowed/forbidden | supporting | No | **partially clear** (single dir) |
| M4.x milestone docs | docs/runtime/milestones/M4_1*.md … M4_6*.md | List runtime/observation/ modules and tests | supporting | No (milestone-specific) | **clear** (not spine) |

---

## 4. Layer-4 inventory by role

Structured inventory covering observation/ (top-level), runtime/observation/, and related docs.

| Path | Role / topic | Classification | Canonical status | Placement quality | Notes |
|------|----------------|----------------|------------------|-------------------|-------|
| observation/ | Layer-4 boundary root | canonical Layer-4 boundary/tool surface | canonical | good | ingest, baseline, judge_drift_suite, tests |
| observation/README.md | Package index | docs/index/pointer | canonical | good | No runtime/observation/ |
| observation/ingest/ | CLI: validate, reconcile, report | canonical Layer-4 boundary/tool surface | canonical | good | Uses runtime schema paths only (file paths) |
| observation/ingest/cli.py | Ingest CLI entrypoint | canonical Layer-4 boundary/tool surface | canonical | good | python -m observation.ingest.cli |
| observation/ingest/validate.py | Schema + rule validation | schema/contract-dependent Layer-4 surface | canonical | good | RUNTIME_SCHEMAS, IDE_SCHEMAS, SHADOW_SCHEMAS (path refs) |
| observation/ingest/reconcile.py | Reconcile by (request_id, plan_hash) | internal Layer-4 implementation | canonical | good | |
| observation/ingest/report.py | report.json, report.md | internal Layer-4 implementation | canonical | good | |
| observation/ingest/README.md | Ingest usage, schemas list | docs/index/pointer | canonical | good | Lists runtime/schemas paths |
| observation/baseline/ | CLI: baseline mode, compare mode | canonical Layer-4 boundary/tool surface | canonical | good | Uses observation.ingest.validate |
| observation/baseline/cli.py | Baseline CLI entrypoint | canonical Layer-4 boundary/tool surface | canonical | good | python -m observation.baseline.cli |
| observation/baseline/load.py | Load batches | internal Layer-4 implementation | canonical | good | Uses observation.ingest.validate |
| observation/baseline/compare.py | Drift compare | internal Layer-4 implementation | canonical | good | |
| observation/baseline/metrics.py | Metrics computation | internal Layer-4 implementation | canonical | good | |
| observation/baseline/report.py | baseline_report, drift_report | internal Layer-4 implementation | canonical | good | |
| observation/baseline/README.md | Baseline usage | docs/index/pointer | canonical | good | |
| observation/judge_drift_suite/ | Suite runner, coverage, weekly report | canonical Layer-4 boundary/tool surface | canonical | good | run_suite, generate_weekly_report, etc. |
| observation/judge_drift_suite/runner.py | Suite runner | canonical Layer-4 boundary/tool surface | canonical | good | |
| observation/judge_drift_suite/coverage_metrics.py | Coverage metrics | internal Layer-4 implementation | canonical | good | |
| observation/judge_drift_suite/weekly_report.py | Weekly report, STATUS_DRIFT/STABLE | internal Layer-4 implementation | canonical | good | |
| observation/judge_drift_suite/verdict_normalizer.py | Verdict normalization | internal Layer-4 implementation | canonical | good | |
| observation/judge_drift_suite/entropy_tracker.py | Entropy tracking | internal Layer-4 implementation | canonical | good | |
| observation/judge_drift_suite/threshold_loader.py | Threshold loading | internal Layer-4 implementation | canonical | good | |
| observation/tests/ | Tests for ingest, baseline, judge_drift_suite | test-only surface | non-canonical | good | |
| runtime/observation/ | M4.1–M4.6 library | canonical Layer-4 implementation library / runtime-coupled | canonical | good (placement); questionable (docs) | __all__ exports; consumed by runtime |
| runtime/observation/__init__.py | Package exports (TraceBuilder, BaselineStore, etc.) | canonical Layer-4 implementation library | canonical | good | |
| runtime/observation/trace_builder.py | TraceBuilder | runtime-coupled Layer-4 library | canonical | good | Uses SandboxLedgerStore |
| runtime/observation/summary_queries.py | RuntimeSummaryQueries | runtime-coupled Layer-4 library | canonical | good | Uses SandboxLedgerStore |
| runtime/observation/explanation_builder.py | ExplanationBuilder | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/report_runtime_summary.py | CLI --summary, --request-id, --canonical-hash | canonical Layer-4 boundary/tool surface (inside runtime tree) | canonical | good | python -m runtime.observation.report_runtime_summary |
| runtime/observation/drift_baseline.py | BaselineBuilder | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/baseline_store.py | BaselineStore | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/baseline_models.py | BaselineDimension, etc. | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/collapse_vectors.py | CollapseClassifier | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/collapse_models.py | CollapseClass, etc. | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/collapse_queries.py | CollapseQueryService | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/reconciliation.py | LedgerReconciliationService | runtime-coupled Layer-4 library | canonical | good | Uses sandbox_ledger_store |
| runtime/observation/reconciliation_models.py | Mismatch types, etc. | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/greg_escalation.py | EscalationPolicy, GREG | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/greg_bundle.py | GREGBundle, EscalationEvidence | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/bundle_builder.py | BundleBuilder | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/runtime_metrics.py | RuntimeMetricsService | runtime-coupled Layer-4 library | canonical | good | Uses ledger.store, sandbox_ledger_store |
| runtime/observation/metrics_models.py | PostureCounts, etc. | runtime-coupled Layer-4 library | canonical | good | |
| runtime/observation/models.py | TraceEvent, RuntimeSummary, etc. | runtime-coupled Layer-4 library | canonical | good | |
| runtime/tests/test_trace_builder.py, test_drift_baseline.py, … | Tests for runtime/observation | test-only surface | non-canonical | good | |
| docs/LAYER4_OBSERVATION_SPEC.md | Layer-4 spec | canonical | canonical | good | “Directory: observation/” only |
| docs/OBSERVATION/README.md | Layer-4 index in docs | canonical pointer | canonical | questionable | Case OBSERVATION; no runtime/observation |
| docs/ARCHITECTURE_4_LAYER.md | Layer-4: observation/ | supporting | canonical | partially clear | Single dir |

---

## 5. Layer-4 structural findings

Each finding uses: Finding; Why it is a problem; Severity; Recommended action; Action timing.

**Finding 1 — Dual-tree split not documented in canonical spine**  
- **Why it is a problem:** No document in the canonical spine (MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, LAYER4_OBSERVATION_SPEC, observation/README.md, docs/OBSERVATION/README.md) states that observation/ is the Layer-4 boundary/CLI and runtime/observation/ is the runtime-consumed Layer-4 library. LAYER4_OBSERVATION_SPEC says “Directory: observation/” and lists ingest, baseline, drift, collapse, GREG; it does not mention runtime/observation/. A new contributor reading only the spine sees Layer-4 as “observation/” and does not see that trace, baseline store, collapse, reconciliation, GREG bundle, and runtime metrics live under runtime/observation/.  
- **Severity:** Medium (docs-placement gap; structure is coherent).  
- **Recommended action:** Add one canonical sentence (e.g. in LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER or observation/README): “Layer-4 has two code locations: observation/ (boundary and CLIs: ingest, baseline, judge_drift_suite) and runtime/observation/ (runtime-consumed library implementing M4.1–M4.6: trace, baseline, collapse, reconciliation, GREG, metrics).”  
- **Action timing:** `later`.

**Finding 2 — Dual observation index paths and case mismatch**  
- **Why it is a problem:** MASTER_SYSTEM_SPEC links to docs/OBSERVATION/README.md (uppercase). Root README and other docs link to observation/README.md (lowercase package). On case-sensitive systems these are different paths. docs/OBSERVATION/README and observation/README have overlapping content (ingest, baseline) but neither mentions runtime/observation/. Having two index locations without a single “source of truth” for “where is Layer-4” can cause link drift or confusion.  
- **Severity:** Medium (naming/link consistency).  
- **Recommended action:** Document the intended relationship (e.g. docs/OBSERVATION/README as docs index; observation/README as package index; both should reference the other and the dual-tree split). Optionally normalize case in links in a later remediation phase.  
- **Action timing:** `later`.

**Finding 3 — Milestone docs carry structural truth**  
- **Why it is a problem:** The only docs that list runtime/observation/ modules and file roles are M4_1_OBSERVABILITY_CLOSURE.md through M4_6_RUNTIME_METRICS.md and branch_execution_notes. These are milestone/implementation docs, not canonical architecture. If someone only reads the spine, they miss runtime/observation/. Architecture ownership should not depend on milestone docs.  
- **Severity:** Low (already addressed by Finding 1).  
- **Recommended action:** Same as Finding 1: add the dual-tree sentence to the spine so structural truth lives in LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER.  
- **Action timing:** `later`.

**Finding 4 — observation/ingest depends on runtime schema file paths**  
- **Why it is a problem:** observation/ingest/validate.py and ingest/cli.py use REPO / "runtime" / "schemas", REPO / "runtime" / "ide" / "schemas", REPO / "runtime" / "shadow" / "schemas" to load JSON schemas for validation. This is **disciplined** (read-only; no Python import of runtime packages; only file paths). If runtime schema paths are moved or renamed, observation/ingest will break until updated. Path contract is explicit and documented in observation/ingest/README.md.  
- **Severity:** Low (acceptable coupling; path contract exists).  
- **Recommended action:** None for this phase. If runtime schemas are ever moved, update observation/ingest/validate.py and ingest/cli.py and observation/ingest/README.md in lockstep.  
- **Action timing:** `never touch without dedicated plan` for runtime schema paths.

---

## 6. Layer-4 anchor clarity test

- **Is Layer-4 canonically anchored in one clear spine?** Partially. The **spec** is anchored (LAYER4_OBSERVATION_SPEC, docs/OBSERVATION/README, observation/README). The **code** is split across two trees; the spine describes only one (observation/). So “where Layer-4 truth lives” has two answers (observation/ and runtime/observation/), and only the first is in the spine.

- **Do observation/, runtime/observation/, and the docs agree?** Functionally yes: observation/ = boundary/CLI; runtime/observation/ = library. Docs do not contradict this; they **omit** runtime/observation/ from the Layer-4 description. So there is no disagreement, only **omission**.

- **Are there multiple apparent “sources of truth”?** No. There is one Layer-4 spec (LAYER4_OBSERVATION_SPEC). The two READMEs (docs/OBSERVATION, observation/README) are both indices pointing to observation/ingest and observation/baseline; they do not claim different ownership. The gap is that neither index mentions runtime/observation/.

- **Is the current structure understandable to a new contributor?** Only if they also read M4.x milestone docs or Phase 1/Phase 4 audit reports. From the spine alone, they would not learn that runtime/observation/ is Layer-4.

---

## 7. Dual-tree coherence test

- **Do the two trees form a coherent split?** Yes. **observation/** (top-level): operator/CLI boundary — ingest batches (validate, reconcile, report), baseline capture/compare, judge_drift_suite (runner, coverage, weekly report). **runtime/observation/**: library implementing M4.1–M4.6 — trace building, summary queries, explanation builder, drift baseline logic, baseline store, collapse tracking, reconciliation, GREG escalation/bundle, runtime metrics. No overlap in responsibility: root does not implement trace/baseline/collapse/reconciliation; those live only in runtime/observation/. Root uses runtime **schema files** (paths only); runtime/observation/ uses runtime **ledger/sandbox** (Python imports). So the split is “boundary/CLI vs runtime-consumed library.”

- **Do they overlap?** No duplicate logic. Root observation does not import runtime.observation. runtime/observation does not implement ingest CLI or baseline CLI (those are in root). The only “overlap” is the word “baseline”: observation/baseline (CLI for baseline report and drift compare) vs runtime/observation/drift_baseline.py and baseline_store.py (library for building/storing baselines from ledger evidence). Different concerns: root baseline = operator-facing baseline/drift reports; runtime baseline = building and persisting baseline snapshots from ledger data.

- **Is naming misleading?** In docs only. “observation” and “runtime/observation” are both Layer-4; the name “runtime/observation” correctly suggests “observation code under runtime.” What is misleading is that **canonical docs** say “Directory: observation/” and do not say “and runtime/observation/,” so readers may think Layer-4 is only observation/.

- **Is the split docs-clean or docs-ambiguous?** **Docs-ambiguous.** The split is clean in code; it is **under-documented** in the spine.

**Conclusion:** Dual-tree split is **clean in code but under-documented**; classify as **acceptable but naming/docs ambiguous** until one canonical sentence is added.

---

## 8. CLI/tool boundary vs library boundary test

- **Top-level observation tool boundary:** observation/ingest/cli (python -m observation.ingest.cli), observation/baseline/cli (python -m observation.baseline.cli), and observation/judge_drift_suite (run_suite, generate_weekly_report exported from __init__). These are the Layer-4 operator-facing entrypoints. They accept file paths, config, and options; they do not import runtime.observation. They depend on runtime only via **schema file paths** (observation/ingest/validate.py, ingest/cli.py). So the **tool boundary is clean**: top-level observation is the CLI/tool surface.

- **Runtime/observation library boundary:** runtime/observation/ is a Python package with __all__ exports (TraceBuilder, RuntimeSummaryQueries, ExplanationBuilder, BaselineBuilder, BaselineStore, CollapseClassifier, LedgerReconciliationService, GREG types, RuntimeMetricsService, etc.). It is consumed by runtime/tests and by runtime code (e.g. trace_builder, summary_queries, reconciliation, runtime_metrics). It also exposes one CLI: report_runtime_summary (python -m runtime.observation.report_runtime_summary). So the **library boundary is clear**: runtime/observation/ is the runtime-consumed implementation; the single CLI is a natural entrypoint for that library.

- **Are responsibilities actually clean?** Yes. Root observation = run ingest, baseline, judge_drift_suite as **tools**. Runtime observation = **library** used by runtime to build traces, summaries, baselines, collapse classification, reconciliation, GREG bundles, metrics from ledger/sandbox evidence. No Layer-3 enforcement code lives in observation; no root observation code imports runtime.observation.

**Conclusion:** CLI/tool boundary (observation/) and library boundary (runtime/observation/) are **clean**; responsibilities are clearly separated.

---

## 9. Public vs internal Layer-4 surface test

- **Operator-facing surfaces:** observation/ingest/cli, observation/baseline/cli, observation/judge_drift_suite (run_suite, generate_weekly_report), runtime/observation/report_runtime_summary (CLI). These are the public entrypoints. observation/README and docs/OBSERVATION/README point to ingest and baseline; they do not list report_runtime_summary (which is under runtime and documented in M4.1).

- **Library-facing surfaces:** runtime/observation/ __all__ — TraceBuilder, RuntimeSummaryQueries, ExplanationBuilder, BaselineBuilder, BaselineStore, CollapseClassifier, CollapseQueryService, LedgerReconciliationService, GREG types, BundleBuilder, RuntimeMetricsService, and models. These are the library API for runtime and tests.

- **Internal-only areas:** observation/ingest/validate, reconcile, report; observation/baseline/load, compare, metrics, report; observation/judge_drift_suite (coverage_metrics, verdict_normalizer, entropy_tracker, threshold_loader, weekly_report internals). runtime/observation/ internal modules (e.g. _row_to_trace_event in trace_builder) are implementation details. No internal path is named so as to look like the primary public API.

- **Milestone/report residue ambiguity:** M4.x milestone docs list runtime/observation/ files. They are not the canonical ownership source; they are implementation notes. No milestone doc is named so as to replace LAYER4_OBSERVATION_SPEC. So **milestone residue** carries structural truth but is not the intended spine; the ambiguity is “where do I learn about runtime/observation/?” — answer today is M4.x or audit reports, not the main spec.

**Conclusion:** Public (CLIs, library __all__) vs internal (validation, reconcile, load, metrics, etc.) is **clear**. The only ambiguity is that the **canonical spec** does not list runtime/observation/ as the second tree.

---

## 10. Runtime-schema coupling test

- **Is runtime schema dependence disciplined?** Yes. observation/ingest/validate.py and observation/ingest/cli.py use **file paths** only: REPO / "runtime" / "schemas", REPO / "runtime" / "ide" / "schemas", REPO / "runtime" / "shadow" / "schemas". They load JSON schema files for jsonschema validation. They do **not** import runtime.schemas or any runtime Python package. So Layer-4 boundary code depends on Layer-3 **schema artifacts** (files), not on Layer-3 **code**. This is **clean reference**: read-only, contract-bound (schema paths are documented in observation/ingest/README.md).

- **Does it create structural entanglement?** No. Moving runtime schemas would require updating observation/ingest paths; that is a path contract, not entanglement. Observation does not depend on runtime behavior or runtime code; it only depends on schema JSON files existing at known paths.

- **Do top-level observation paths remain meaningfully Layer-4?** Yes. observation/ owns the **semantics** of ingestion, validation rules (R1–R5, L1–L5, R-IDE1–3), reconciliation, baseline report, and drift compare. It uses runtime **schemas** only to validate structure of plan, ledger_row, decision_response, ingestion_batch. So Layer-4 remains the owner of observation logic; Layer-3 remains the owner of schema definitions.

**Conclusion:** Runtime-schema coupling is **clean reference** and **acceptable coupling**; no ambiguous overlap or structural concern.

---

## 11. Docs-placement clarity test

- **Dual index paths:** docs/OBSERVATION/README.md (Layer-4 index in docs) and observation/README.md (Layer-4 package README). Both describe ingest, baseline, drift, GREG. MASTER_SYSTEM_SPEC links to OBSERVATION/README (docs). Root README and SHADOW_MODE_PROTOCOL reference observation/ingest and observation/baseline. So there are **two** index locations; neither mentions runtime/observation/.

- **Case mismatch:** “OBSERVATION” (docs) vs “observation” (package). On case-sensitive systems these are different paths. CANONICAL_DOCS_PLACEMENT_AUDIT (Phase 1) already flagged this.

- **Absence of canonical explanation of split:** No document in the spine states that observation/ is boundary/CLI and runtime/observation/ is runtime-consumed library. So **docs-placement clarity** is lacking for the split.

- **Milestone docs carrying structural truth:** M4_1 through M4_6 (and branch_execution_notes) list runtime/observation/ modules. They are the only place a reader learns where TraceBuilder, BaselineStore, etc. live. So **milestone docs are doing architecture’s job** for the second tree; the spine should absorb that in one sentence.

**Conclusion:** Docs-placement is **partially clear** (indices exist; Layer-4 purpose is clear); **dual-tree split is not explained** in the spine; **case mismatch** and **dual indices** are medium-severity clarity issues.

---

## 12. Cross-layer leakage test

- **Layer-3 ↔ Layer-4:** **Acceptable coupling.** (1) observation/ (root) uses runtime/schemas, runtime/ide/schemas, runtime/shadow/schemas as **file paths** for validation; no Python import of runtime. (2) runtime/observation/ imports runtime.sandbox.sandbox_ledger_store and runtime.ledger.store — Layer-4 library consumes Layer-3 ledger/sandbox to build traces, summaries, reconciliation, metrics. This is by design (observation consumes runtime evidence). (3) No Layer-3 code imports root observation/. So Layer-4 does not leak into Layer-3 ownership; Layer-3 does not leak into Layer-4 ownership. Coupling is **acceptable**.

- **Layer-1 ↔ Layer-4:** **Clean reference.** Layer-4 produces evidence and may trigger GREG; it does not author doctrine. No observation code imports governance/. LAYER4_OBSERVATION_SPEC and ARCHITECTURE_4_LAYER state Layer-4 cannot author doctrine or relax boundaries. No structural concern.

- **Layer-2 ↔ Layer-4:** **Clean reference.** Layer-4 may consume freeze manifest or lineage for boundary hashes (spec mentions boundary_phrase_hash, corpus_hash); no inspection was done of observation code for ml/ or governance paths. From Phase 2/3, ml/ does not depend on observation. No evidence of Layer-2/Layer-4 entanglement.

**Conclusion:** Cross-layer leakage is **absent**; Layer-3 ↔ Layer-4 is **acceptable coupling** (schema paths and ledger/sandbox consumption).

---

## 13. Layer-4 Path Contract Register

| Path | Why path-sensitive | Referenced by | Risk if moved/renamed | Recommendation note |
|------|--------------------|---------------|------------------------|---------------------|
| observation/ | Layer-4 boundary root | README, SHADOW_MODE_PROTOCOL, plan_gate_stub README, MASTER_SYSTEM_SPEC (as observation) | High | Do not move |
| observation/ingest/ | Ingest CLI | docs/OBSERVATION/README, observation/README, ingest/README, SHADOW_MODE_PROTOCOL | High | Do not move |
| observation/baseline/ | Baseline CLI | docs/OBSERVATION/README, observation/README, baseline/README, SHADOW_MODE_PROTOCOL | High | Do not move |
| observation/judge_drift_suite/ | Judge drift suite | observation/README, observation/__init__, tests | Medium | Do not move |
| runtime/observation/ | Layer-4 library | runtime/tests, runtime code (trace_builder, summary_queries, reconciliation, runtime_metrics), M4.x docs | High | Do not move; document in spine |
| runtime/schemas/ | Schema files | observation/ingest/validate.py (RUNTIME_SCHEMAS) | High | Do not move; path contract |
| runtime/ide/schemas/ | IDE schema files | observation/ingest/validate.py (IDE_SCHEMAS) | High | Do not move; path contract |
| runtime/shadow/schemas/ | Shadow schema files | observation/ingest/validate.py, ingest/cli.py (SHADOW_SCHEMAS) | High | Do not move; path contract |
| docs/LAYER4_OBSERVATION_SPEC.md | Layer-4 spec | MASTER_SYSTEM_SPEC | High | Do not move |
| docs/OBSERVATION/README.md | Layer-4 index in docs | MASTER_SYSTEM_SPEC | Medium | Case-sensitive; do not move |
| observation/README.md | Layer-4 package README | Root README, SHADOW_MODE_PROTOCOL, plan_gate_stub | Medium | Do not move |

---

## 14. Preliminary keep / clarify / move-later / do-not-touch classification

| Item / cluster | Preliminary classification | Rationale |
|----------------|----------------------------|-----------|
| observation/ | do not touch without dedicated plan | Layer-4 boundary root; path contract |
| observation/ingest/, observation/baseline/, observation/judge_drift_suite/ | keep | Canonical CLI/tool surface |
| runtime/observation/ | keep; clarify later | Layer-4 library; add to spine |
| runtime/schemas/, runtime/ide/schemas/, runtime/shadow/schemas/ | do not touch without dedicated plan | Path contract from observation/ingest |
| docs/LAYER4_OBSERVATION_SPEC.md | keep; clarify later | Add dual-tree sentence |
| docs/OBSERVATION/README.md, observation/README.md | keep; clarify later | Add runtime/observation/ and dual-tree; fix case/links if needed |

---

## 15. Immediate conclusions

- **Does Layer-4 have a clean canonical structure?** Yes in code: two trees with clear roles (boundary/CLI vs runtime-consumed library). No in docs: the spine describes only observation/ and does not state the dual-tree split.

- **What are the biggest Layer-4 structural risks?** (1) Dual-tree split not in spine — add one canonical sentence. (2) Dual index paths and case mismatch (docs/OBSERVATION vs observation/README). (3) Milestone docs carrying structural truth for runtime/observation/.

- **Which Layer-4 items are dangerous to touch?** observation/ (root); observation/ingest (path contract to runtime schemas); observation/baseline, observation/judge_drift_suite; runtime/observation/ (consumed by runtime and tests); runtime/schemas, runtime/ide/schemas, runtime/shadow/schemas (referenced by observation/ingest); docs/LAYER4_OBSERVATION_SPEC.md, docs/OBSERVATION/README.md, observation/README.md.

- **What must be clarified later?** (1) Add canonical sentence: observation/ = boundary/CLI, runtime/observation/ = runtime-consumed library. (2) Document or normalize dual index (docs/OBSERVATION vs observation/README). (3) Ensure spine, not only M4.x, records runtime/observation/ as Layer-4.

- **What should the next audit phase be?** Phase 5 completes the layer-by-layer structural audit (Phase 0 root, Phase 1 docs, Phase 2 governance, Phase 3 Layer-2, Phase 4 Layer-3, Phase 5 Layer-4). The next phase could be **remediation planning** (prioritized actions from Phases 0–5) or **cross-cutting path-contract consolidation** (single register of all path-sensitive items across layers). No further “layer structure audit” phase is required unless the user defines Phase 6.

---

## 16. Non-goals

This phase did **not**:

- Move, rename, or edit any file under observation/, runtime/observation/, or docs.
- Change code, imports, or package structure.
- Merge the two observation trees or fix links.
- Clean up reports or archive anything.
- Propose repo-wide cleanup or remediation.
- Audit Layer-1, Layer-2, or Layer-3 internals beyond references needed to assess boundaries and path contracts.

---

## Phase 5 result summary

### 1. Artifact created
- **path:** `docs/audit/LAYER4_OBSERVATION_STRUCTURE_AUDIT.md`

### 2. Canonical Layer-4 spine assessment
- **primary anchor:** docs/LAYER4_OBSERVATION_SPEC.md and docs/OBSERVATION/README.md (and observation/README.md).
- **top-level observation tree:** observation/ — ingest, baseline, judge_drift_suite; operator/CLI boundary; uses runtime schema file paths only.
- **runtime/observation tree:** runtime/observation/ — M4.1–M4.6 library (trace, baseline, collapse, reconciliation, GREG, metrics); report_runtime_summary CLI; consumed by runtime and tests.
- **docs/indexes:** docs/LAYER4_OBSERVATION_SPEC.md, docs/OBSERVATION/README.md, observation/README.md; none mention runtime/observation/ in spine.
- **overall clarity:** **partially clear** — spine describes observation/ only; dual-tree split is clean in code but under-documented.

### 3. Major findings
- **finding 1:** Dual-tree split not documented in canonical spine — add one sentence that observation/ = boundary/CLI and runtime/observation/ = runtime-consumed library.
- **finding 2:** Dual observation index paths (docs/OBSERVATION/README vs observation/README) and case mismatch — document relationship and optionally normalize.
- **finding 3:** Milestone docs (M4.1–M4.6) carry structural truth for runtime/observation/ — move one sentence to spine.

### 4. Dual-tree coherence result
- **status:** Clean in code; under-documented in spine.
- **key evidence:** observation/ = ingest, baseline, judge_drift_suite (no import of runtime.observation); runtime/observation/ = trace, baseline store, collapse, reconciliation, GREG, metrics (imports runtime.sandbox, runtime.ledger); no duplicate responsibility.
- **conclusion:** Split is **clean and well-signaled in code**; **acceptable but naming/docs ambiguous** until spine is updated.

### 5. CLI/library boundary result
- **status:** Clean.
- **key evidence:** Top-level observation = CLIs (ingest, baseline, judge_drift_suite); runtime/observation = library with one CLI (report_runtime_summary); responsibilities separated; root does not import runtime.observation.
- **conclusion:** CLI/tool boundary (observation/) and library boundary (runtime/observation/) are clearly separated.

### 6. Docs-placement clarity result
- **status:** Partially clear; dual-tree split and runtime/observation/ missing from spine.
- **key evidence:** LAYER4_OBSERVATION_SPEC says “Directory: observation/” only; docs/OBSERVATION/README and observation/README do not mention runtime/observation/; M4.x docs list runtime/observation/ modules; case OBSERVATION vs observation.
- **conclusion:** Add one canonical sentence to spine; optionally document dual index and fix case/links.

### 7. Cross-layer leakage result
- **Layer-3:** Acceptable coupling — observation/ uses runtime schema paths (file paths only); runtime/observation/ uses runtime.sandbox and runtime.ledger.
- **Layer-1:** Clean reference — Layer-4 does not author doctrine.
- **Layer-2:** Clean reference — no entanglement observed.

### 8. Path-sensitive Layer-4 items identified
- **number:** 11 (paths in Path Contract Register).
- **notable examples:** observation/, observation/ingest/, observation/baseline/, runtime/observation/, runtime/schemas/, runtime/ide/schemas/, runtime/shadow/schemas/, docs/LAYER4_OBSERVATION_SPEC.md, docs/OBSERVATION/README.md, observation/README.md.

### 9. Final status
**PHASE 5 LAYER4 AUDIT READY**
