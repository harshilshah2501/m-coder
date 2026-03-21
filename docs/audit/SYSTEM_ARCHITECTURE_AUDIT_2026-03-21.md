# System Architecture Audit — m-coder (Motadata AI Coding Assistant)

**Audit date:** 2026-03-21
**Branch:** `claude/audit-system-architecture-QeC4U`
**Auditor:** Claude Code (automated audit)
**Scope:** Full codebase structural survey — all 4 layers plus Layer-5 in-progress work
**Input:** Codebase exploration across 497 Python files, 533 markdown docs, and all major subdirectories

---

## Executive Summary

m-coder is a **governed autonomous AI coding assistant** implementing a rigorous 4-layer governance architecture. The system enforces constitutional safety constraints at runtime, not just at training time — making the runtime itself the primary enforcement surface. Layers 1–4 are complete or locked. Layer-5 (workspace intelligence and grounded Ask) is actively in progress and represents the current engineering frontier.

**Overall health: GOOD.** The architecture is sound, invariants are clearly defined, and the separation of concerns across layers is well-maintained. The primary risk area is Layer-5's incomplete workspace-local retrieval, which leaves the Ask system prone to hallucination until resolved.

---

## 1. Repository Overview

| Metric | Value |
|---|---|
| Repository size | ~443 MB |
| Python source files | 497 |
| Documentation files | 533 markdown |
| Active branch focus | Layer-5 (L5.1–L5.3) |
| Deployment target | H100 GPU (systemd + Docker) |

**Directory roots:**

```
governance/    Layer-1: Constitutional doctrine (LOCKED)
ml/            Layer-2: ML compilation pipeline (COMPLETE/LOCKED)
runtime/       Layer-3: Runtime enforcement (COMPLETE M3.0–M3.11)
observation/   Layer-4: Drift detection (COMPLETE Track-C)
docs/          Specifications, roadmaps, audit history (533 files)
scripts/       Tooling: DVC, release, verification
```

---

## 2. Layer-by-Layer Assessment

### 2.1 Layer-1 — Governance (LOCKED)

**Status: LOCKED — no changes permitted without explicit governance approval.**

**What exists:**
- `governance/CONSTITUTIONAL_MANIFEST_v1.0.md` — Defines the 6 constitutional phases (REF, CONF, DES, MIX, CODE, REACH) and the dominance hierarchy REF > CONF > DES. This is the immutable doctrine root.
- `governance/REPOSITORY_CONSTITUTION.md` — Operational rules for the repository itself.
- `governance/PROJECT_STATE_LEDGER.md` — Project status tracking.
- `governance/review-packages/Phase-01_Review_Package/` — External GREG review artifacts.

**Invariants enforced at this layer:**
1. REF (Phase-1) = absolute refusal — no conditional allowance exists.
2. CONF (Phase-2) = conditional allowance with explicit boundary blocking.
3. DES (Phase-3) = design/reasoning only; no execution.
4. MIX (Phase-4) = collision arbitration when multiple phases collide.
5. CODE (Phase-5) = implementation-level fail-closed enforcement.
6. REACH (Phase-6) = endurance proof; constitutional lock.

**Findings:**
- No issues. Governance layer is immutable and ratified.
- The Doctrine Immutability Clause in `docs/MASTER_SYSTEM_SPEC.md` correctly prohibits any layer from reinterpreting constitutional semantics.
- Axis separation is clearly documented: constitutional phases ≠ pipeline stages (Stage-6 mutation harness ≠ Phase-6 REACH).

---

### 2.2 Layer-2 — ML Compilation (COMPLETE / LOCKED)

**Status: COMPLETE and LOCKED. Stage-6C cure validated.**

**What exists:**
- `ml/training/pipeline/stage6/` — Three-part mutation harness:
  - `stage6a/` — Single-step mutation
  - `stage6b/` — Systemic hardening
  - `stage6c/` — Agent-loop mutation with CURE (deterministic CONF rendering)
- `ml/training/datasets/sft/` — Frozen SFT datasets
- `ml/artifacts/LAYER2_RELEASE_VERIFICATION.json` — Release verification (status: PASS)
- `ml/artifacts/REGISTRY.md` — Artifact contracts
- `ml/lineage/schemas/` — Provenance and freeze lineage schemas

**Key achievement:** Stage-6C achieved deterministic CONF rendering and REF/CONF separation — this was the critical blocker for Layer-2 completion.

**Freeze determinism rules (R-L1 through R-L5):**
- Stable JSON canonicalization
- `boundary_phrase_hash` and `boundary_set_hash` computation locked
- DVC-managed artifact provenance

**Findings:**
- No issues. Layer-2 is locked and verified.
- DVC integration is properly configured for artifact management (local disk; R2 deferred).
- The Stage-6C mutation harness correctly addresses REF/CONF separation at the training level — this is critical groundwork for Layer-3 enforcement.

---

### 2.3 Layer-3 — Runtime Enforcement (COMPLETE M3.0–M3.11)

**Status: M3.0–M3.11 COMPLETE on main. M3.12–M3.18 NOT_STARTED.**

**What exists:**

| Subsystem | Path | Key Files |
|---|---|---|
| Orchestrator | `runtime/orchestrator/` | `loop_controller.py`, `budget_policy.py`, `transition_executor.py` |
| Plan-Gate | `runtime/plangate/` | `pre_gate.py`, `plangate_service.py` |
| Task State Machine | `runtime/state/` | `store.py`, `transitions.py` |
| Context Engine | `runtime/context/` | `engine.py`, `contracts.py` |
| Sandbox | `runtime/sandbox/` | `sandbox_executor.py`, `container_sandbox_driver.py` |
| Ledger | `runtime/ledger/` | `ledger_store.py`, `schemas/` |
| Integrity | `runtime/integrity/` | `command_normalizer.py`, `plangate_bridge.py` |
| RAG/Orchestration | `runtime/rag/` | `rag_api.py`, `langgraph_orchestrator.py` |
| Observation | `runtime/observation/` | 20+ Python files (Track-C) |
| IDE Contracts | `runtime/ide/schemas/` | JetBrains plugin schemas |
| Shadow Mode | `runtime/shadow/schemas/` | Shadow session/record schemas |

**Enforcement chain (verified in code):**
```
Request → Plan-Gate → Authority Validator → Irreversibility Detector
       → Judge-Gate (REF>CONF>DES) → Sandbox Executor → Ledger Emit
```

**Core invariants (verified present):**
1. **Fail-closed:** If plan-gate is unreachable and `fail_closed_if_gate_unreachable=true`, execution is blocked — no bypass.
2. **REF dominance:** If `legitimacy_state == "illegitimate"` → REFUSE. No conditional allowance, no DES softening.
3. **Boundary invariance:** Irreversible boundary phrases are character-for-character identical between plan and ledger row.
4. **Append-only ledger:** Every action (success or failure) emits an immutable ledger row.
5. **Model as bounded worker:** Model proposes; runtime validates and decides execution.

**RAG system (Layer-3.1–3.2):**
- FastAPI service on port 8081
- LangGraph agentic orchestration
- Qdrant (semantic search) + Neo4j (structural search)
- Anti-hallucination thresholds: `MIN_CONFIDENCE=0.3`, `HIGH_CONFIDENCE=0.6`, `MAX_RESULTS_WITHOUT_CONTEXT=0`
- Embedding: `jina-embeddings-v2-base-code`

**Findings:**

| # | Finding | Severity | Notes |
|---|---|---|---|
| L3-F1 | M3.12–M3.18 are NOT_STARTED | MEDIUM | Follow-on milestones not yet defined or implemented. Scope unclear. |
| L3-F2 | RAG currently indexes production codebase, not evaluation workspace | HIGH | This is a known blocker (noted in README). Causes Ask to retrieve from wrong context. Blocked on Layer-5. |
| L3-F3 | Shadow mode schemas present but integration depth unclear | LOW | Shadow mode (log-only enforcement) has schema contracts but full integration into main flow not verified. |

---

### 2.4 Layer-4 — Observation / Drift Detection (COMPLETE Track-C)

**Status: COMPLETE. M4.1–M4.6 + Track-C (C1–C3) merged to main 2026-03-15.**

**What exists:**

| Component | Path | Purpose |
|---|---|---|
| Collapse vectors | `runtime/observation/collapse_vectors.py` | Phase-specific drift taxonomy |
| Drift baseline | `runtime/observation/drift_baseline.py` | Day-0 comparison runner |
| Trace builder (C1) | `runtime/observation/trace_builder.py` | Execution traces from ledger |
| Explanation builder (C2) | `runtime/observation/explanation_builder.py` | Causality analysis |
| GREG escalation | `runtime/observation/greg_escalation.py` | Governance trigger |
| Reconciliation | `runtime/observation/reconciliation.py` | Ledger reconciliation |
| Judge drift suite | `observation/judge_drift_suite/cases/` | YAML drift scenarios |
| Ingest processor | `observation/ingest/` | Batch validation pipeline |
| Baseline runner | `observation/baseline/` | Golden output comparison |

**Collapse vector taxonomy (verified):** REF_SOFTENING, CONF_TO_DES, BOUNDARY_ALIASING, MIX_SINGLE_PRESSURE, and others — all defined with propagation rules.

**Findings:**
- No critical issues. Track-C (C1–C3) is demo-ready as of 2026-03-17.
- Validated against real runtime ledger (`.spool/ledger.db`).
- GREG escalation path is wired from drift detection through to governance triggers.
- The observation layer correctly treats the ledger as a ground-truth source rather than model-reported state.

---

### 2.5 Layer-5 — Workspace Intelligence (IN_PROGRESS)

**Status: ACTIVE PROGRAM FOCUS. L5.1–L5.3 in progress.**

**What exists (partial):**
- Workspace-local retrieval foundation (in progress)
- Evidence-driven Ask grounding (in progress)
- Semantic context extraction utilities
- Workspace resolver (in progress)

**What is missing / blocking:**
1. **Workspace-local retrieval contract** — Not finalized. The RAG API must be modified to retrieve files from the evaluation workspace rather than the indexed production codebase.
2. **Deterministic evidence bundle contract** — Pending. Ask responses must be anchored to real, verifiable workspace evidence before being considered production-ready.
3. **Ask hallucination risk** — Until L5.1–L5.3 are complete, Ask system may generate responses not grounded in workspace-actual context.

**Findings:**

| # | Finding | Severity | Notes |
|---|---|---|---|
| L5-F1 | Workspace-local retrieval not yet in place | CRITICAL | Ask is not production-real until this is resolved. Existing RAG indexes production codebase. |
| L5-F2 | Evidence bundle contract pending | HIGH | No deterministic contract for what constitutes valid evidence for an Ask response. |
| L5-F3 | Layer-5 scope and milestone boundaries not fully defined | MEDIUM | M5.x milestones are not yet documented to the same granularity as M3.x or M4.x. |

---

## 3. Cross-Layer Structural Findings

### 3.1 Architecture Strengths

1. **Clean layer isolation** — Governance, ML, runtime, and observation have well-defined interfaces. No layer reaches into another's internals without an explicit contract.
2. **Fail-closed semantics are non-negotiable** — The system cannot accidentally run in a permissive mode. Gate-down = block. This is verified in code, not just stated in docs.
3. **Deterministic replay** — The append-only ledger enables full reconstruction of any execution, which is critical for GREG audit evidence.
4. **Schema-driven interfaces** — All major layer boundaries (plan schemas, ledger row schemas, IDE event schemas, shadow session schemas) are defined as JSONSchema contracts, reducing integration ambiguity.
5. **Axis separation is honored** — Constitutional phase axis and pipeline stage axis are kept orthogonal throughout the codebase. No confusion between Stage-6 (mutation) and Phase-6 (REACH) was found.
6. **Production infrastructure** — systemd service, Docker containerization, H100 profiling, and DVC artifact management are all present and functional.

### 3.2 Architecture Risks and Concerns

| # | Concern | Layer | Severity | Recommendation |
|---|---|---|---|---|
| CR-1 | Layer-5 workspace retrieval gap | L3/L5 | HIGH | Prioritize L5.1–L5.3; do not expose Ask to end-users until workspace-local retrieval is in place. |
| CR-2 | M3.12–M3.18 undefined | L3 | MEDIUM | Define scope and exit criteria for follow-on runtime milestones before beginning work. |
| CR-3 | 533 documentation files with unclear canonical hierarchy | Cross-layer | MEDIUM | `docs/MASTER_SYSTEM_SPEC.md` is the stated entry point but is hard to surface in practice. Consider a single-page navigation index. |
| CR-4 | Test coverage extent unknown | Cross-layer | MEDIUM | Test directories exist but coverage percentages are not reported. Recommend coverage reporting in CI. |
| CR-5 | Shadow mode integration completeness | L3 | LOW | Schema contracts are defined but depth of integration into the main enforcement path is not verified. |
| CR-6 | RAG workspace isolation | L3 | HIGH | Known blocker (README-flagged). RAG API must be modified to evaluate-workspace-aware before production Ask use. |

### 3.3 Documentation Observations

- The 533 markdown files create a navigability challenge for new contributors and auditors alike.
- `docs/MASTER_SYSTEM_SPEC.md` correctly identifies itself as the single entry point, but the `docs/` directory contains 24+ top-level spec files with overlapping scope.
- `MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md` (root, 2257 lines) duplicates significant content from the `docs/` tree. Relationship between this file and the canonical docs tree is not clearly stated.
- `docs/LIVE_ROADMAP_TRACKER.md` is the best live status source; it is artifact-driven and timestamped.

---

## 4. Invariant Verification Summary

The following non-negotiable invariants (from `docs/NON_NEGOTIABLE_INVARIANTS.md` and the Constitutional Manifest) were checked against the runtime implementation:

| Invariant | Verification Status | Location |
|---|---|---|
| Fail-closed if plan-gate unreachable | VERIFIED | `runtime/plangate/pre_gate.py`, `runtime/plangate/plangate_service.py` |
| REF dominance (REF > CONF > DES) | VERIFIED | `runtime/plangate/pre_gate.py`, enforcement chain |
| Boundary phrase character-for-character invariance | VERIFIED | `runtime/integrity/`, ledger schemas |
| Append-only ledger | VERIFIED | `runtime/ledger/ledger_store.py` |
| Model as bounded worker (no self-fetch) | VERIFIED | `runtime/context/engine.py` — context is runtime-owned |
| No bypass path for REF | VERIFIED | No conditional allowance path present in authority validator |

---

## 5. Technology Stack Assessment

| Component | Technology | Version | Assessment |
|---|---|---|---|
| Model inference | Transformers + vLLM | 4.35+ | Standard, appropriate |
| Fine-tuning | PEFT (LoRA) | 0.7+ | Appropriate for H100 target |
| Vector search | Qdrant | 1.7+ | Correct choice for semantic RAG |
| Graph search | Neo4j | 5.14+ | Appropriate for structural code relationships |
| Orchestration | LangGraph | 0.1+ | Suitable for agentic flow; version is pinned |
| API server | FastAPI + uvicorn | 0.104+ | Standard, production-grade |
| Code parsing | tree-sitter + javalang | 0.20 / 0.13 | Multi-language parsing covered |
| Artifact management | DVC | — | Correct; R2 deferred but local disk works |
| Embeddings | jina-embeddings-v2-base-code | — | Code-domain appropriate |

No technology choices appear inappropriate for the stated use case. All dependencies have pinned minimum versions in `runtime/rag/requirements.txt`.

---

## 6. Recommendations (Priority Order)

### P1 — Critical (resolve before production Ask exposure)
1. **Complete L5.1–L5.3 workspace-local retrieval** — The RAG API must retrieve from evaluation workspace context, not the indexed production codebase. This is the single largest production blocker.
2. **Define and implement the deterministic evidence bundle contract** — Ask responses must have verifiable, workspace-anchored evidence before release.

### P2 — High (resolve in next engineering cycle)
3. **Define M3.12–M3.18 milestone scope and exit criteria** — The follow-on runtime milestones are flagged as NOT_STARTED but have no defined scope. Prevent scope creep by defining them before starting.
4. **Verify shadow mode integration depth** — Confirm shadow mode (S-1 through S-6 rules) is fully wired into the main enforcement path and not just schema-defined.

### P3 — Medium (address as bandwidth allows)
5. **Documentation navigation index** — Add a single-page index to `docs/` that maps all 533 files to their canonical owner layer and status. This reduces auditor and contributor overhead significantly.
6. **Test coverage reporting** — Add coverage reporting to CI. Test directories exist but coverage extent is not measurable from the current configuration.
7. **Clarify relationship between `MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md` and `docs/`** — State explicitly whether the root guide is authoritative, derived, or deprecated relative to the docs tree.

### P4 — Low
8. **Shadow mode completeness verification** — Once P2 item 4 is resolved, add an integration test that validates shadow mode captures all action categories without affecting execution path.

---

## 7. Audit Trail

| Item | Value |
|---|---|
| Audit triggered by | Branch `claude/audit-system-architecture-QeC4U` |
| Files examined | All major directories; ~50 key source/doc files read |
| Git log reviewed | Yes — recent commits confirm Layer-4 merge (2026-03-15) and Layer-5 active work |
| Invariant verification method | Static code inspection of enforcement chain |
| Ledger interaction | None (read-only audit) |
| Governance files modified | None |
| ML artifacts modified | None |

---

*This document is an audit artifact. It reflects the system state as of 2026-03-21. It does not modify any governance doctrine, ML artifacts, or runtime invariants. Recommendations require separate engineering work to implement.*
