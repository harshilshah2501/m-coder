# Phase 4 — Layer-3 Runtime Structure Audit Report

**Repository:** m-coder  
**Audit phase:** Phase 4 only (Layer-3 runtime structural audit, read-only)  
**Date:** 2026-03-15  
**Scope:** Runtime layout, package boundaries, public/internal surfaces, demo/test/helper mixing, legacy scaffolding, path contracts, and explicit classification of `runtime/observation/`. No moves, renames, edits, or remediation performed.

---

## 1. Purpose and scope

This document is the deliverable for **Phase 4** of the m-coder structural audit. It is a **read-only structural audit** of **Layer-3 runtime** only. It does not move or rename files, edit code or docs, refactor, clean up tests/demos, or perform remediation. The audit inventories Layer-3 anchors, classifies subpackages and surfaces, assesses package-boundary coherence, public vs internal clarity, demo/test/helper mixing, legitimacy of `runtime/observation/`, cross-layer leakage, legacy/scaffolding persistence, and path-contract sensitivity.

---

## 2. Executive assessment

- **Overall Layer-3 structural health:** Good with gaps. Layer-3 is canonically anchored under `runtime/` with a clear doc spine (docs/LAYER3_RUNTIME_SPEC.md, docs/runtime/README.md, docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md, ARCHITECTURE_4_LAYER). The governed runtime architecture (plan-gate, judge-gate, authority, irreversibility, ledger, sandbox, state, orchestrator) is implemented and reflected in subpackages: **plangate** (canonical enforcement), **sandbox**, **ledger**, **state**, **orchestrator**, **execute_service**, **ask_service**, **context**, **ide**, **shadow**, **schemas**. Two parallel pathways exist by design: (1) **plangate** — used by orchestrator, execute_service, sandbox, ledger (real agent loop); (2) **plan_gate_stub** + **plan_gate_service** — protocol/IDE contract testing and HTTP daemon for plugin; stub is explicitly “not a real judge.” A separate **policies/** package provides validate/classify (authority + irreversibility) and is used only by dedicated unit tests; production enforcement uses **plangate** (class-based). **runtime/observation/** is a Layer-4 implementation library colocated under runtime (M4.1–M4.6: trace, baseline, collapse, reconciliation, GREG, metrics); it is consumed by runtime/tests and by runtime code (e.g. trace_builder uses sandbox_ledger_store). The split observation/ (root) vs runtime/observation/ is **not** documented in the canonical spine (Phase 1 finding); structurally it is acceptable (boundary/CLI vs runtime-consumed library) but naming/docs are ambiguous. **runtime/README.md** is incomplete: it lists only rag/, .config/, plan_gate_stub, ci_gate, plan_gate_service and schema locations; it omits plangate, observation, sandbox, ledger, state, orchestrator, ask_service, execute_service, context, ide, shadow, shadow_runner, integrity, emulator, replay.

- **Does Layer-3 have a clear canonical anchor?** Yes. Primary anchor is `runtime/` and docs/LAYER3_RUNTIME_SPEC.md; docs/runtime/README.md and RUNTIME_PLAN_AND_LEDGER_V0_1.md define plan/ledger and schema locations. MASTER_SYSTEM_SPEC and ARCHITECTURE_4_LAYER assign Layer-3 to runtime/ and list allowed/forbidden. The in-repo runtime/README.md is the only index that under-reports contents.

- **Biggest Layer-3 structural risks:** (1) **runtime/README.md incomplete** — new contributors may not discover plangate, sandbox, ledger, state, orchestrator, or runtime/observation/. (2) **observation split not in spine** — runtime/observation/ is Layer-4 library; no canonical sentence states this. (3) **Dual plan-gate pathway** — stub vs plangate is intentional but could be clarified in one sentence (stub for protocol/IDE; plangate for governed loop). (4) **policies/ vs plangate** — two authority/irreversibility surfaces (policies = function API; plangate = class API); only plangate is used in production; policies may be legacy or alternate surface.

---

## 3. Layer-3 canonical spine

For each major Layer-3 anchor we state: path; role; canonical / pointer / supporting; whether it competes; confidence.

| Anchor | Path | Role | Canonical / pointer / supporting | Competes? | Confidence |
|--------|------|------|----------------------------------|-----------|-------------|
| Layer-3 comprehensive spec | docs/LAYER3_RUNTIME_SPEC.md | Plan-gate, authority, irreversibility, judge, ledger, CI, IDE, shadow, invariants | canonical | No | **clear** |
| Runtime index (docs) | docs/runtime/README.md | Layer-3 index; state machine, agent architecture, schema locations, stub, service | canonical pointer | No | **clear** |
| Plan/ledger spec | docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md | Plan object, ledger row, R1–R5, L1–L5, canonicalization | canonical | No | **clear** |
| State machine | docs/runtime/RUNTIME_STATE_TRANSITIONS.md | M3.T0 state machine, transition matrix | canonical | No | **clear** |
| Agent architecture | docs/runtime/RUNTIME_AGENT_ARCHITECTURE.md | Runtime Governor, Task State Store, Model Worker Interface, Repository Context Engine, Sandbox | canonical | No | **clear** |
| Runtime namespace (in-repo) | runtime/README.md | Namespace index; lists rag, .config, plan_gate_stub, ci_gate, plan_gate_service, schema paths | canonical pointer | No (but incomplete) | **partially clear** |
| Plan-gate implementation | runtime/plangate/ | PlanGateService, AuthorityValidator, IrreversibilityDetector, JudgeGate; used by orchestrator, sandbox, execute_service | canonical | No | **clear** |
| Plan-gate stub | runtime/plan_gate_stub/ | CLI + stub_decide for protocol/IDE; “not a real judge”; golden_outputs, examples | canonical (stub surface) | No (different role) | **clear** |
| Plan-gate HTTP service | runtime/plan_gate_service/ | POST /v0/plan; reuses plan_gate_stub; for plugin/demo | canonical (service surface) | No | **clear** |
| Schemas (plan/ledger) | runtime/schemas/ | plan.v0.1, ledger_row.v0.1; protected in AGENT_EXECUTION_RULES | schema/contract asset | No | **clear** |
| IDE schemas | runtime/ide/schemas/ | plan_request, decision_response, boundary_hashing, execute_*, etc.; protected | schema/contract asset | No | **clear** |
| State schemas | runtime/state/schemas/ | state_enums.v0.1, transition_matrix.v0.1 | schema/contract asset | No | **clear** |
| Shadow schemas | runtime/shadow/schemas/ | ingestion_batch, shadow_run_record | schema/contract asset | No | **clear** |
| runtime/observation/ | runtime/observation/ | M4.1–M4.6 library (trace, baseline, collapse, reconciliation, GREG, metrics); Layer-4 implementation colocated in runtime | Layer-4 implementation colocated in runtime | No (different layer responsibility) | **partially clear** (docs) |

---

## 4. Layer-3 inventory by role

Structured inventory of major Layer-3 files/clusters. Classification and placement quality as defined in the task.

| Path | Role / topic | Classification | Canonical status | Placement quality | Notes |
|------|----------------|----------------|------------------|-------------------|-------|
| runtime/ | Layer-3 root | canonical | canonical | good | __init__ exports minimal (policies, RAG, orchestration) |
| runtime/plangate/ | Plan-gate service, authority, irreversibility, judge | canonical runtime implementation | canonical | good | Used by orchestrator, sandbox, execute_service, ledger |
| runtime/plan_gate_stub/ | Protocol stub CLI; stub_decide; golden_outputs, examples | demo/operator surface + test surface | canonical (stub) | good | “Not a real judge”; used by plan_gate_service |
| runtime/plan_gate_service/ | HTTP daemon POST /v0/plan | canonical runtime implementation | canonical | good | Reuses plan_gate_stub; plugin/demo |
| runtime/policies/ | validate, classify (authority + irreversibility) | internal runtime implementation or milestone residue | non-canonical (alternate API) | questionable | Only used by test_authority_validator, test_irreversibility_detector; not used by plangate |
| runtime/orchestrator/ | loop_controller, transition_executor, stop_conditions, replay, budget_policy | canonical runtime implementation | canonical | good | Uses plangate |
| runtime/sandbox/ | sandbox_executor, sandbox_ledger_store, drivers, demo_governed_execution | canonical runtime implementation + demo | canonical | good | Demo colocated; tests in runtime/tests |
| runtime/ledger/ | emitter, store, replay, contracts, demo_trace | canonical runtime implementation + demo | canonical | good | Uses plangate.plangate_decision |
| runtime/state/ | store, transitions, schemas | canonical runtime implementation | canonical | good | State machine contracts |
| runtime/context/ | engine, contracts | canonical runtime implementation | canonical | good | Used by ask_service |
| runtime/ask_service/ | handlers, planner | canonical runtime implementation | canonical | good | Uses context |
| runtime/execute_service/ | handlers | canonical runtime implementation | canonical | good | Uses plangate |
| runtime/ide/ | schemas, tests | plugin-facing/runtime-facing contract | canonical | good | IDE request/response schemas |
| runtime/shadow/ | ingestion_batch, runner, harness, baseline_scenarios | canonical runtime implementation | canonical | good | Shadow protocol |
| runtime/shadow_runner/ | run_demo | demo/operator surface | canonical (demo) | good | Demo only |
| runtime/schemas/ | plan, ledger_row, examples | schema/contract asset | canonical | good | Protected in AGENT_EXECUTION_RULES |
| runtime/observation/ | M4.1–M4.6 trace, baseline, collapse, reconciliation, GREG, metrics | Layer-4 implementation colocated in runtime | Layer-4 | good (placement); questionable (docs) | Consumed by runtime/tests and runtime code; __all__ exports; report_runtime_summary is CLI |
| archive/legacy_runtime_rag/ | RAG API, orchestrator, indexing, retrieval | canonical runtime implementation | canonical | good | Large subtree |
| runtime/ci_gate/ | CLI client for plan-gate; fails build on REFUSAL/CONDITIONAL_BLOCK | canonical runtime implementation | canonical | good | |
| runtime/integrity/ | canonical_intent, plangate_bridge, command_normalizer | internal runtime implementation | canonical | good | |
| runtime/emulator/ | ledger, boundary, authority | internal runtime implementation or test support | non-canonical | good | Emulator for testing |
| runtime/replay/ | execution_replay_service | canonical runtime implementation | canonical | good | |
| runtime/tests/ | Integration/unit tests for plangate, sandbox, observation, etc. | test-only surface | non-canonical | good | |
| runtime/plan_gate_service/tests/ | plan_gate_service v0.1 tests; references plan_gate_stub golden paths | test-only surface | non-canonical | good | |
| runtime/plan_gate_stub/golden_outputs/ | Golden JSON artifacts | test/demo fixture | non-canonical | good | |
| docs/LAYER3_RUNTIME_SPEC.md | Full Layer-3 spec | canonical | canonical | good | |
| docs/runtime/README.md | Layer-3 index in docs | canonical pointer | canonical | good | Does not list runtime/observation/ |
| docs/runtime/RUNTIME_AGENT_ARCHITECTURE.md | Governor, state machine, context engine, sandbox | canonical | canonical | good | |
| docs/runtime/RUNTIME_STATE_TRANSITIONS.md | State machine | canonical | canonical | good | |
| docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md | Plan/ledger rules | canonical | canonical | good | |

---

## 5. Layer-3 structural findings

Each finding uses: Finding; Why it is a problem; Severity; Recommended action; Action timing.

**Finding 1 — runtime/README.md omits most subpackages**  
- **Why it is a problem:** runtime/README.md lists only rag/, .config/, plan_gate_stub, ci_gate, plan_gate_service and schema locations. It does not list plangate, sandbox, ledger, state, orchestrator, ask_service, execute_service, context, ide, shadow, shadow_runner, integrity, emulator, replay, or runtime/observation/. A new contributor reading only runtime/README.md would not see the governed loop implementation (plangate, orchestrator, sandbox) or the observation library. docs/runtime/README.md is more complete but still does not mention runtime/observation/.  
- **Severity:** Medium (discovery/clarity).  
- **Recommended action:** Update runtime/README.md to list all major subpackages (plangate, sandbox, ledger, state, orchestrator, ask_service, execute_service, context, ide, shadow, observation) with one-line roles; or add a single line: “Full index: docs/runtime/README.md and docs/LAYER3_RUNTIME_SPEC.md.”  
- **Action timing:** `later`.

**Finding 2 — observation/ vs runtime/observation/ not in canonical spine**  
- **Why it is a problem:** Phase 1 (CANONICAL_DOCS_PLACEMENT_AUDIT) established that no document in the canonical spine states that observation/ is the Layer-4 boundary/CLI and runtime/observation/ is the runtime-consumed Layer-4 library. LAYER4_OBSERVATION_SPEC says “Directory: observation/” and does not mention runtime/observation/. ARCHITECTURE_4_LAYER says “Layer-4: observation/” without the split. Readers cannot infer the two-part structure from the spine.  
- **Severity:** Medium (docs ambiguity; structure is consistent).  
- **Recommended action:** Add one canonical sentence (e.g. in LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER): “Layer-4 boundary and CLIs live under observation/ (ingest, baseline, judge_drift_suite); the runtime-consumed observation library implementing M4.1–M4.6 (trace, baseline, collapse, reconciliation, GREG, metrics) lives under runtime/observation/.”  
- **Action timing:** `later`.

**Finding 3 — Dual plan-gate pathway (stub vs plangate)**  
- **Why it is a problem:** Two pathways exist: (1) plan_gate_stub (stub_decide) used by plan_gate_service HTTP daemon for plugin/IDE contract testing; (2) plangate (PlanGateService) used by orchestrator, execute_service, sandbox for the real governed loop. Both are documented (plan_gate_stub README: “not a real judge”; plan_gate_service README: “reuses stub decision logic”). The split is intentional but could confuse: which is “the” plan-gate?  
- **Severity:** Low (documented; intentional).  
- **Recommended action:** In runtime/README.md or LAYER3_RUNTIME_SPEC, one sentence: “Production governed loop uses runtime/plangate (PlanGateService); protocol and IDE contract testing use runtime/plan_gate_stub and runtime/plan_gate_service (HTTP).”  
- **Action timing:** `later`.

**Finding 4 — policies/ vs plangate authority/irreversibility**  
- **Why it is a problem:** runtime/policies/ exports validate (authority) and classify (irreversibility); runtime/plangate/ implements AuthorityValidator and IrreversibilityDetector (class-based). Production code (orchestrator, sandbox, execute_service) uses plangate only. Only test_authority_validator.py and test_irreversibility_detector.py use runtime.policies. This suggests policies/ may be an older or alternate API; no doc states the relationship.  
- **Severity:** Medium (unclear ownership; duplicate surface).  
- **Recommended action:** Document whether policies/ is legacy, alternate API, or test-only surface; if legacy, consider marking in README or deprecation note. Do not remove without a dedicated plan.  
- **Action timing:** `later` or `never touch without dedicated plan`.

**Finding 5 — runtime/__init__.py exports minimal set**  
- **Why it is a problem:** runtime/__init__.py currently exposes only “policies, RAG, orchestration” (from the codebase). It does not export plangate, observation, sandbox, ledger, etc. So the top-level package surface is understated; consumers may not expect to import from runtime.plangate or runtime.observation. This may be intentional (explicit subpackage imports) but could be clarified.  
- **Severity:** Low (cosmetic/clarity).  
- **Recommended action:** None required for this phase. Optionally document in runtime/README that “import from runtime.plangate, runtime.sandbox, runtime.observation, etc., as needed.”  
- **Action timing:** `later`.

---

## 6. Layer-3 anchor clarity test

- **Is Layer-3 canonically anchored in one clear spine?** Yes. The spine is: docs/LAYER3_RUNTIME_SPEC.md (full spec) → docs/runtime/README.md (index, state machine, agent architecture, schema locations) → docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md (plan/ledger); runtime/ (directory); runtime/README.md (in-repo index, incomplete). MASTER_SYSTEM_SPEC and ARCHITECTURE_4_LAYER point to runtime/ and Layer-3 specs.

- **Do runtime/, docs, schemas, and bridge docs agree?** Largely yes. LAYER3_RUNTIME_SPEC describes plan-gate, authority, irreversibility, judge, ledger, CI, IDE, shadow. docs/runtime/README lists schema locations (runtime/schemas, runtime/ide/schemas, runtime/state/schemas, runtime/shadow/schemas). RUNTIME_PLAN_AND_LEDGER and JETBRAINS_PLUGIN_FLOW, SHADOW_MODE_PROTOCOL align. The only disagreement is runtime/README.md omitting most subpackages and runtime/observation/.

- **Are there multiple apparent “sources of truth”?** No. One Layer-3 spec (LAYER3_RUNTIME_SPEC); one plan/ledger spec; one state machine doc. Stub vs plangate are two implementations for different purposes, not competing specs.

- **Is the current structure understandable to a new contributor?** Partially. If they start from MASTER_SYSTEM_SPEC → ARCHITECTURE_4_LAYER → docs/LAYER3_RUNTIME_SPEC or docs/runtime/README, they get the right picture. If they start from runtime/README.md only, they miss plangate, sandbox, ledger, orchestrator, and runtime/observation/.

---

## 7. Subpackage boundary coherence test

- **Subpackage visibility:** All major components are visible as top-level subpackages under runtime/: plangate, plan_gate_stub, plan_gate_service, policies, orchestrator, sandbox, ledger, state, context, ask_service, execute_service, ide, shadow, shadow_runner, schemas, observation, rag, ci_gate, integrity, emulator, replay. Naming is consistent (snake_case package names).

- **Naming coherence:** SYSTEM_NAMING_CONVENTION_AUDIT notes plan_gate_stub vs plan_gate_service (underscore) vs plangate (no underscore). Intentional: stub and service are “plan-gate” surfaces; plangate is the implementation package name. No conflict.

- **Responsibility matching:** plangate = plan-gate logic; sandbox = execution sandbox; ledger = ledger emission/store/replay; state = task state store; orchestrator = loop control; context = repository context engine; ask_service / execute_service = IDE/plugin endpoints; ide = IDE schemas; shadow = shadow protocol; observation = Layer-4 library. Responsibilities align with ARCHITECTURE_4_LAYER and RUNTIME_AGENT_ARCHITECTURE.

- **Duplicate pathway risk:** Two pathways exist and are documented: (1) stub + plan_gate_service for protocol/IDE; (2) plangate for governed loop. policies/ is a second authority/irreversibility surface (function API) used only by two test files; production uses plangate. Risk is confusion, not conflicting behavior.

- **Runtime tree reflects documented architecture:** Yes. Runtime Governor → plangate (plan-gate) + state + orchestrator; Execution Sandbox → sandbox; Ledger → ledger; Repository Context Engine → context; Model Worker Interface → ask_service/execute_service; IDE contracts → ide/schemas. observation/ is Layer-4 library consumed by runtime (trace_builder, etc.) and by tests.

**Conclusion:** Subpackage boundaries are **clear**; only **runtime/observation/** and **policies/** vs **plangate** need explicit clarification in docs.

---

## 8. Public vs internal runtime surface test

- **Contract surfaces:** Public contract surfaces are clearly defined by schema locations and specs: runtime/schemas/ (plan, ledger_row), runtime/ide/schemas/ (plan_request, decision_response, execute_*, boundary_hashing, etc.), runtime/state/schemas/, runtime/shadow/schemas/. These are protected in AGENT_EXECUTION_RULES §3. HTTP contract: plan_gate_service POST /v0/plan (PlanRequest → DecisionResponse). These are canonical runtime contract surfaces.

- **Internal-only surfaces:** plangate internals (authority_validator, irreversibility_detector, judge_gate, contracts, command_utils), sandbox internals (sandbox_executor, sandbox_ledger_store, drivers), ledger internals (emitter, store, replay), orchestrator internals (loop_controller, transition_executor, stop_conditions) are implementation details. They are not re-exported as top-level API in a way that would make them look like public contract.

- **Test/demo/helper ambiguity:** plan_gate_stub/golden_outputs and plan_gate_stub/examples are clearly under a “stub” package and README says “not a real judge.” sandbox/demo_governed_execution.py and ledger/demo_trace.py are demos colocated with production code; naming (demo_*) makes them distinguishable. shadow_runner/run_demo.py is demo-only. Tests live under runtime/tests/ or under */tests/ in subpackages. No test or demo file is named so as to look like the primary runtime API.

- **Internal items mistaken for public API:** Low risk. The only ambiguity is policies/ (validate, classify) which could be mistaken for “the” authority/irreversibility API; production uses plangate. Documenting policies/ as alternate or legacy would remove that risk.

**Conclusion:** Public vs internal is **clear** for schemas and HTTP/IDE contracts; **partially clear** for policies/ vs plangate (both export authority/irreversibility-related behavior).

---

## 9. Demo/test/helper mixing test

- **Where production/demo/test/helper mixing exists:** (1) runtime/plan_gate_stub/ — production-quality CLI and stub_decide used by plan_gate_service, but also golden_outputs/ and examples/ (fixtures/demos). (2) runtime/sandbox/ — sandbox_executor, sandbox_ledger_store (production) plus demo_governed_execution.py (demo). (3) runtime/ledger/ — emitter, store, replay (production) plus demo_trace.py (demo). (4) runtime/shadow_runner/ — run_demo only (demo). (5) runtime/plan_gate_service/tests/ — references plan_gate_stub golden paths. (6) runtime/observation/report_runtime_summary.py — CLI entrypoint (python -m runtime.observation.report_runtime_summary); rest of observation is library.

- **Assessment:** **Acceptable.** Demos are named (demo_*, run_demo) or live under a stub/demo package. Golden outputs are under plan_gate_stub and used for protocol determinism and tests. No production module is named like a test or demo. Fixtures (golden_outputs) are clearly under the stub package. The only borderline is report_runtime_summary being a CLI inside runtime/observation/ — it is a natural entrypoint for the observation library and is documented in M4.1; acceptable.

**Conclusion:** Demo/test/helper mixing is **acceptable**; no structurally risky co-location.

---

## 10. `runtime/observation/` legitimacy test

- **What kind of structure it appears to be:** runtime/observation/ is a **Python package** implementing M4.1 (Observability Closure), M4.2 (Drift Baseline), M4.3 (Collapse Vector Tracking), M4.4 (Ledger Reconciliation), M4.5 (GREG Escalation), and M4.6 (Runtime Metrics). It has a full __all__ and is imported by runtime/tests (test_trace_builder, test_drift_baseline, test_collapse_vectors, test_reconciliation, test_greg_escalation, test_explanation_builder, test_runtime_summary_queries, test_report_runtime_summary, test_runtime_metrics) and by runtime code: trace_builder and summary_queries use SandboxLedgerStore; reconciliation uses sandbox_ledger_store; runtime_metrics uses ledger.store and sandbox_ledger_store. So it is **library code** that reads runtime ledger/sandbox state and exposes trace, baseline, collapse, reconciliation, GREG, and metrics. It also provides a CLI: report_runtime_summary (python -m runtime.observation.report_runtime_summary). Top-level observation/ (root) contains ingest, baseline, judge_drift_suite — CLIs and suite runners that do **not** import runtime.observation in the inspected files; observation/ingest references runtime/schemas, runtime/ide/schemas, runtime/shadow/schemas as **file paths** for validation, not as Python imports of runtime.observation.

- **Whether the split is clean:** **Functionally clean.** observation/ (root) = Layer-4 boundary and CLIs (ingest, baseline, judge_drift_suite). runtime/observation/ = Layer-4 implementation library that consumes runtime ledger/sandbox and is used by runtime tests and by runtime code (e.g. trace building). The split is “boundary/CLI vs runtime-consumed library.” No duplicate logic was observed; root observation does not reimplement trace/baseline/collapse/reconciliation — those live in runtime/observation/.

- **Whether the naming is misleading:** **Yes, in docs only.** The name “runtime/observation” suggests “observation code that lives under runtime,” which is correct. What is misleading is that **canonical Layer-4 docs** (LAYER4_OBSERVATION_SPEC, ARCHITECTURE_4_LAYER, observation/README, docs/OBSERVATION/README) say “Directory: observation/” and do not mention runtime/observation/. So the **naming** is fine; the **documentation** makes it seem as if Layer-4 is only observation/ (root). A reader could infer that runtime/observation/ is “extra” or “part of runtime” rather than “Layer-4 library colocated in runtime for coupling.”

- **Primarily docs-placement ambiguity or deeper structural concern:** **Primarily docs-placement ambiguity.** The structure is consistent: Layer-4 has (1) boundary/CLI under observation/, (2) library under runtime/observation/ for tight coupling with ledger/sandbox. No evidence that runtime/observation/ should be moved to observation/ (that would require runtime to depend on observation package, or a separate repo). The fix is to **document** the split in the canonical spine. Deeper structural reconsideration (e.g. moving runtime/observation to observation/runtime_observation or similar) is out of scope for this audit.

**Conclusion:** runtime/observation/ is **legitimate Layer-4 implementation library colocated in the runtime package**. The split is **acceptable but naming/docs ambiguous** until a canonical sentence is added. **Not** a boundary violation; **not** a packaging smell beyond missing documentation.

---

## 11. Cross-layer leakage test

- **Layer-1 ↔ Layer-3:** **Clean reference.** Runtime implements doctrine (REF, CONF, DES, dominance) and does not read governance/ or AGENT_EXECUTION_RULES by path. Phase semantics are encoded in code and docs; no Layer-1 files are imported by runtime. Governance paths are protected; runtime does not write to them. LAYER1_GOVERNANCE_STRUCTURE_AUDIT already assessed this as acceptable coupling.

- **Layer-2 ↔ Layer-3:** **Clean reference.** Layer-2 (ml/) produces datasets, checkpoints, and artifacts; runtime does not import ml/ for enforcement. Runtime may consume model artifacts (adapters) at deployment time via configuration, not via importing ml/. No Layer-2 path is in runtime’s import tree. LAYER2_COMPILATION_STRUCTURE_AUDIT confirmed runtime overlap absent.

- **Layer-4 ↔ Layer-3:** **Acceptable coupling.** (1) observation/ (root) references runtime/schemas, runtime/ide/schemas, runtime/shadow/schemas as **file paths** (REPO / "runtime" / ...) for schema validation in ingest/validate.py and ingest/cli.py. So Layer-4 boundary code depends on Layer-3 schema paths; acceptable. (2) runtime/observation/ (Layer-4 library under runtime) imports runtime.sandbox.sandbox_ledger_store and runtime.ledger.store — i.e. Layer-4 observation library depends on Layer-3 ledger/sandbox. This is acceptable coupling (observation consumes runtime evidence). (3) No Layer-3 code imports root observation/ package. So Layer-4 ↔ Layer-3 is **acceptable coupling**; no ambiguous overlap or structural concern.

**Conclusion:** Cross-layer leakage is **absent**; relationships are **clean reference** or **acceptable coupling**.

---

## 12. Legacy / scaffolding persistence test

- **Stubs:** plan_gate_stub is an **explicit** stub (“NOT a real judge”; “protocol plumbing pressure-test”). It is still in use by plan_gate_service and by tests (plan_gate_service/tests reference stub golden paths). So it is **intentional scaffolding**, not dead legacy.

- **Temporary compatibility paths:** None identified. plan_gate_service “reuses stub decision logic” by design for IDE/plugin contract; no temporary compatibility layer was found.

- **Old milestone layout:** policies/ may be legacy: it provides validate/classify (authority + irreversibility) and is used only by two test files; plangate provides the same conceptual components (AuthorityValidator, IrreversibilityDetector) and is used everywhere else. This could be milestone-era separation (function API vs class API) that persisted. No duplicate pathways that break behavior; only duplicate **surfaces** for the same concern.

- **Duplicate pathways:** (1) Stub vs plangate — documented; stub for protocol/IDE, plangate for loop. (2) policies vs plangate — duplicate authority/irreversibility surface; production uses plangate only. Neither is “wrong”; clarifying policies/ role would reduce confusion.

**Conclusion:** No dangerous legacy; **plan_gate_stub** is intentional; **policies/** may be legacy or alternate API and should be clarified.

---

## 13. Layer-3 Path Contract Register

| Path | Why path-sensitive | Referenced by | Risk if moved/renamed | Recommendation note |
|------|--------------------|---------------|------------------------|---------------------|
| runtime/ | Layer-3 root | ARCHITECTURE_4_LAYER, MASTER_SYSTEM_SPEC, all runtime imports | High | Do not move |
| runtime/schemas/ | Plan/ledger schemas; AGENT_EXECUTION_RULES §3 | observation/ingest/validate.py (RUNTIME_SCHEMAS), docs, verification | High | Do not move; protected |
| runtime/ide/schemas/ | IDE contracts; AGENT_EXECUTION_RULES §3 | observation/ingest/validate.py (IDE_SCHEMAS), docs, verification | High | Do not move; protected |
| runtime/state/schemas/ | State machine | LAYER3_RUNTIME_SPEC, RUNTIME_STATE_TRANSITIONS, LIVE_ROADMAP | High | Do not move |
| runtime/shadow/schemas/ | Shadow protocol | observation/ingest (SHADOW_SCHEMAS), docs | High | Do not move |
| runtime/plangate/ | Plan-gate implementation | orchestrator, execute_service, sandbox, ledger, tests | High | Do not move |
| runtime/plan_gate_stub/ | Stub + golden_outputs, examples | plan_gate_service/handlers (stub_decide), plan_gate_service/tests | High | Do not move; golden paths in tests |
| runtime/plan_gate_service/ | HTTP daemon | runtime/README, docs, plugin docs | Medium | Do not move |
| runtime/sandbox/ | Sandbox executor, ledger store | orchestrator, observation (trace_builder, reconciliation, runtime_metrics), tests | High | Do not move |
| runtime/ledger/ | Ledger store, emitter | observation/runtime_metrics, ledger/emitter (plangate_decision), tests | High | Do not move |
| runtime/observation/ | Layer-4 library | runtime/tests, trace_builder/summary_queries/reconciliation/report_runtime_summary | High | Do not move; document in spine |
| runtime/orchestrator/ | Loop controller | LIVE_ROADMAP, tests | High | Do not move |
| runtime/state/ | Task state store | RUNTIME_AGENT_ARCHITECTURE, state machine docs | High | Do not move |
| runtime/context/ | Repository context engine | ask_service | Medium | Do not move |
| runtime/ask_service/ | Ask handlers | tests | Medium | Do not move |
| runtime/execute_service/ | Execute handlers | tests | Medium | Do not move |
| docs/LAYER3_RUNTIME_SPEC.md | Layer-3 spec | MASTER_SYSTEM_SPEC | High | Do not move |
| docs/runtime/README.md | Layer-3 index | MASTER_SYSTEM_SPEC | High | Do not move |
| docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md | Plan/ledger spec | runtime/README, docs | High | Do not move |

---

## 14. Preliminary keep / clarify / move-later / do-not-touch classification

| Item / cluster | Preliminary classification | Rationale |
|----------------|----------------------------|-----------|
| runtime/plangate/ | do not touch without dedicated plan | Canonical plan-gate implementation; used by orchestrator, sandbox, execute_service, ledger |
| runtime/sandbox/, runtime/ledger/, runtime/state/, runtime/orchestrator/ | do not touch without dedicated plan | Core governed loop |
| runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/ | do not touch without dedicated plan | Protected; path-contract and observation/ingest |
| runtime/plan_gate_stub/, runtime/plan_gate_service/ | keep | Stub and HTTP service for protocol/IDE |
| runtime/observation/ | keep; clarify later | Layer-4 library; document in spine |
| runtime/context/, runtime/ask_service/, runtime/execute_service/ | keep | Context engine and service endpoints |
| runtime/policies/ | clarify later | Relationship to plangate (legacy vs alternate API) |
| runtime/README.md | clarify later | Add missing subpackages or pointer to docs |
| docs/runtime/README.md | keep | Add one line on runtime/observation/ if desired |
| runtime/emulator/, runtime/replay/, runtime/integrity/, archive/legacy_runtime_rag/, runtime/ci_gate/ | keep | Supporting components |

---

## 15. Immediate conclusions

- **Does Layer-3 have a clean canonical structure?** Yes. Layer-3 is anchored under runtime/ with a clear doc spine. Subpackages match the governed runtime architecture (plan-gate, sandbox, ledger, state, orchestrator, context, IDE, shadow). Dual pathway (stub vs plangate) is intentional and documented. runtime/observation/ is Layer-4 library colocated in runtime; structure is acceptable; only docs are missing a canonical sentence.

- **What are the biggest Layer-3 structural risks?** (1) runtime/README.md incomplete — contributors may miss plangate, sandbox, ledger, orchestrator, observation. (2) observation/ vs runtime/observation/ not in spine — Phase 1 finding; add one sentence. (3) policies/ vs plangate — two authority/irreversibility surfaces; clarify role.

- **Which Layer-3 items are dangerous to touch?** runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/ (protected in AGENT_EXECUTION_RULES; referenced by observation/ingest). runtime/plangate/, runtime/sandbox/, runtime/ledger/, runtime/orchestrator/, runtime/state/ (core loop). runtime/plan_gate_stub/ (golden paths in plan_gate_service tests). runtime/observation/ (consumed by runtime and tests).

- **What must be clarified later?** (1) runtime/README.md — list all major subpackages or point to docs. (2) LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER — state observation/ vs runtime/observation/ split. (3) Stub vs plangate — one sentence in runtime or LAYER3 spec. (4) policies/ — legacy, alternate, or test-only.

- **What should the next audit phase be?** Per the approved plan, **Phase 5 — Layer-4 observation structure audit** (observation/ layout, runtime/observation/ vs observation/ boundary, ingest/baseline/judge_drift_suite, path contracts, and canonical documentation of the split).

---

## 16. Non-goals

This phase did **not**:

- Move, rename, or edit any file under runtime/ or docs.
- Change code, imports, or package structure.
- Refactor stub vs plangate or policies vs plangate.
- Delete or archive demos, tests, or helpers.
- Propose repo-wide cleanup or remediation.
- Audit Layer-1, Layer-2, or Layer-4 internals beyond references needed to assess boundaries and path contracts.

---

## Phase 4 result summary

### 1. Artifact created
- **path:** `docs/audit/LAYER3_RUNTIME_STRUCTURE_AUDIT.md`

### 2. Canonical Layer-3 spine assessment
- **primary anchor:** runtime/ (directory) and docs/LAYER3_RUNTIME_SPEC.md.
- **main Layer-3 directory:** runtime/ — plangate, plan_gate_stub, plan_gate_service, sandbox, ledger, state, orchestrator, context, ask_service, execute_service, ide, shadow, schemas, observation, rag, ci_gate, policies, integrity, emulator, replay.
- **runtime docs/specs:** docs/LAYER3_RUNTIME_SPEC.md, docs/runtime/README.md, docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md, docs/runtime/RUNTIME_AGENT_ARCHITECTURE.md, docs/runtime/RUNTIME_STATE_TRANSITIONS.md.
- **schemas/contracts:** runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/ (protected in AGENT_EXECUTION_RULES §3).
- **overall clarity:** **clear** — one spine; runtime/README.md incomplete; runtime/observation/ and stub vs plangate need one-sentence clarification in docs.

### 3. Major findings
- **finding 1:** runtime/README.md omits plangate, sandbox, ledger, state, orchestrator, observation, and other subpackages — add list or pointer to docs.
- **finding 2:** observation/ vs runtime/observation/ not documented in canonical spine — add one sentence in LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER.
- **finding 3:** Dual plan-gate pathway (stub for protocol/IDE, plangate for governed loop) — document in one sentence.

### 4. Subpackage coherence result
- **status:** Clear; subpackages match documented architecture; stub vs plangate and policies vs plangate need explicit clarification.
- **key evidence:** plangate used by orchestrator, sandbox, execute_service, ledger; plan_gate_stub used by plan_gate_service; policies used only by two test files; runtime/observation/ is Layer-4 library with full __all__.
- **conclusion:** Boundaries are coherent; naming and responsibility match; duplicate surfaces (stub/plangate, policies/plangate) are documented or should be clarified.

### 5. Public/internal surface result
- **status:** Clear for schemas and HTTP/IDE contracts; partially clear for policies/ vs plangate.
- **key evidence:** Schemas and IDE/plan contracts are protected and documented; production uses plangate; policies exports validate/classify and is test-only in usage.
- **conclusion:** No internal/test/demo path is likely to be mistaken for the primary runtime API; policies/ role should be documented.

### 6. `runtime/observation/` result
- **status:** Legitimate Layer-4 implementation library colocated in runtime; acceptable but naming/docs ambiguous until spine is updated.
- **key evidence:** M4.1–M4.6 implementation; consumed by runtime/tests and by runtime code (trace_builder, summary_queries, reconciliation, runtime_metrics); observation/ (root) does not import it; root observation references runtime schema paths only; no canonical doc states the split.
- **conclusion:** Not a boundary violation; not a packaging smell; primarily docs-placement ambiguity. Add canonical sentence to spine.

### 7. Cross-layer leakage result
- **Layer-1:** Clean reference — runtime implements doctrine; no governance path reads.
- **Layer-2:** Clean reference — no ml/ imports in runtime.
- **Layer-4:** Acceptable coupling — observation/ (root) uses runtime schema paths; runtime/observation/ uses runtime.sandbox and runtime.ledger.

### 8. Path-sensitive Layer-3 items identified
- **number:** 19 (paths in Path Contract Register).
- **notable examples:** runtime/, runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/, runtime/plangate/, runtime/plan_gate_stub/, runtime/sandbox/, runtime/ledger/, runtime/observation/, docs/LAYER3_RUNTIME_SPEC.md, docs/runtime/README.md.

### 9. Final status
**PHASE 4 LAYER3 AUDIT READY**
