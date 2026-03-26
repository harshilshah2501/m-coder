# LIVE ROADMAP TRACKER — Motadata AI Coding Assistant

**Doc status:** canonical-current. Live progress dashboard; status is artifact-driven.

## 1. Header

- **Project**: Motadata AI Coding Assistant — 4-Layer Governed Architecture  
- **Last updated**: 2026-03-26  
- **Program state**: **Retrieval baseline locked → validation and system hardening phase**
- **Current active layer**: **Layer-5 — Workspace Intelligence**  
- **Current integration branch (local consolidated line)**: `**feature/l5-context-layer-v1-ask-packaging`** — merges **M3.12** (manifest/doc_selector), `**integration/m3.12-context-demo`**, **M3.17** (task slice + C1 doc sign-off) into the L5 packaging line; push when ready to replace prior scattered branches.  
- **Current active milestone focus**: **L5.8 — Grounded Ask Validation + Metrics**. Parallel hard gates: **L5-OBS-1 — Observability & Tracing** and **Plugin Truthfulness Alignment**. **L5.9** is explicitly downstream after grounded-input validation stability; **M3.18** remains downstream task-level evaluation after L5.8. **Backend HTTP** chain remains: **WSL Context Layer wheel** (`motadata-context-layer`) → GPU **m-coder** Plan-Gate → `POST /v1/ask` (provable with `**docs/Backend Production Validation Sheet.md`**). North star: `**docs/PRODUCT_SLICE_CHARTER.md`**. Operator paths: `**docs/MOTADATA_DEMO_SETUP_RUNBOOK.md**` + `**docs/MOTADATA_DEMO_SCENARIOS.md**` + `**docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md**`.  
- **Overall status summary**:  
  - Layer-1 governance doctrine is **LOCKED**.  
  - Layer-2 ML compilation is **COMPLETE / LOCKED** (Stage-6C cure, deterministic CONF, release verification PASS).  
  - **Layer-3 M3.0–M3.11 are COMPLETE on main.** **M3.12** narrow repo-aware manifest slice **merged on L5 branch** (not necessarily on `main`). **M3.13–M3.18** follow-on. **Governed execute** (`POST /v0/execute`) exists on Plan-Gate; **Ask → Plan → Execute** continuum is not fully reflected in L5 tracker rows until plugin + execute UX are explicitly gated together.  
  - **Layer-4 M4.1–M4.6 are COMPLETE on main** (merged 2026-03-15; see docs/reports/M4X_MAIN_MERGE_COMPLETION.md).
  - **Layer-5 — Wave-1 (A1/A2/A3) COMPLETE**; **Wave-2 (A4/A5/A6) COMPLETE** — deterministic index, lexical retrieval, evidence `layer5.evidence_bundle.v1` frozen. **Wave-3 (A7/A8) COMPLETE** — plugin evidence-first + Plan-Gate `**POST /v1/ask`**. **Packaging slice COMPLETE** — installable `**packaging/motadata-context-layer`** wheel + `**runtime/context_layer_service**` HTTP API (**no m-coder checkout required on WSL**). **Next:** **production slice readiness** — plugin truthfulness, observability, retrieval generalization/validation gates (**L5.8** / **§1.4** tracks); not only deployment smoke.

### 1.1 Known system realities (do not skip)

- **Dual Ask path:** JetBrains may call `**POST /v0/ask`** unless **evidence-first** is ON (`motadata.ask.evidence_first` / `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST`). Backend validation scripts for `**POST /v1/ask`** are **not** the same default path as the IDE — this is a **known system condition**, not operator error.
- **Evidence-first default:** **OFF** in plugin — alignment with `**layer5.evidence_bundle.v1`** + `/v1/ask` is **opt-in**.
- **Observability gap:** Plan-Gate HTTP does **not** log each request by default; **no unified trace** (Context Layer ↔ Plan-Gate ↔ vLLM) without further work — see **§1.4 Track OBS**.
- **Retrieval:** PR-6 true-positive debug retrieval baseline is **COMPLETE / LOCKED** (deterministic, workspace-local). Active risk is **generalization + validation thresholds** under **L5.8** and **§1.4 Track RET**.
- **Host profiles:** **Windows+WSL+GPU** and **native Linux** are charter targets; plugin **Plan-Gate URL is hardcoded** `127.0.0.1:8089` today — config externalization is backlog, not done.

### 1.2 Current truth state (honest)


| Surface                                                                     | State                                                                                                                                    |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Backend** (Context Layer + Plan-Gate + vLLM stack when started)           | **Functional** for HTTP contracts per validation sheet                                                                                   |
| **JetBrains plugin**                                                        | **Primary user surface** — path/rendering/metadata alignment **in progress**; treat as **critical component**, not a Wave-3 afterthought |
| **True end-to-end** (IDE → evidence → `/v1/ask` → honest UI + traceability) | **Not** production-complete until **§1.3** gates and **Track OBS** are satisfied                                                         |


### 1.3 Hard production gates (updated checklist)

Treat as **release blockers** for claiming production-grade slice (iterate in charter + validation sheets):

- **Plugin** can reach `**POST /v1/ask`** **deterministically** when product intent is evidence-first (or product explicitly documents v0-only mode).
- **Evidence bundle** visible in UI when backend returned it; **insufficiency** visible when weak — no “silent theater.”
- `**ask_path` / path class** surfaced to operator (UI or logs).
- `**plan_summary.notes`** shown when backend sends them (known gap: UI may omit).
- `**POST /v0/execute**` outcomes **truthful** (executed vs blocked vs refused) — no fake success.
- **Request tracing**: `request_id` (or equivalent) **correlatable** across Context Layer, Plan-Gate, and (for Explain) vLLM — **Track OBS**.

### 1.4 Explicit follow-on tracks (named in tracker)


| Track                    | ID                                     | Scope                                                                                                                                                                                                                     |
| ------------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Observability**        | **L5-OBS-1**                           | `request_id` propagation; Plan-Gate access/structured logging; path visibility in UI; automation friendly with `**docs/Backend Production Validation Sheet.md`** / `**docs/JetBrains Plugin Defect Isolation Sheet.md**`. |
| **Retrieval validation** | **L5-RET-VALIDATION** (feeds **L5.8**) | Query → expected file mapping; `top_k` correctness; false positive/negative classification; lexical limits explicit.                                                                                                      |


**Related audit artifacts:** `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md`, `docs/audit/SURGICAL_NEXT_STEPS_PLAN.md`.

## CURRENT SYSTEM REALITY (POST VALIDATION)

### Backend
- Context Layer + Plan-Gate + vLLM path is **contract-correct and governed**
- `/v1/ask` evidence-first path validated
- execution path (`/v0/execute`) is honest and deterministic

### Retrieval
- Deterministic lexical + symbol retrieval foundation is materially strengthened
- **PR-6 true-positive debug retrieval baseline is COMPLETE / LOCKED** on real Motadata repo:
  - Top-1 accuracy: **10/10**
  - Top-3 anchor hit: **10/10**
  - Mean first relevant rank: **1.00**
  - Mean top-5 noise dominance: **0.00**
- Remaining retrieval risk is **generalization beyond the locked debug fixture set**, not raw noise-dominance rescue

### Plugin
- Plugin path may diverge (`/v0/ask` vs `/v1/ask`)
- Evidence rendering incomplete
- plan_summary.notes not shown
- UI can misrepresent grounded context

### System Status
- Backend: FUNCTIONAL
- Retrieval: BASELINE LOCKED (PR-6), GENERALIZATION PENDING (L5.8)
- Plugin: PARTIALLY MISALIGNED
- End-to-end: NOT YET PRODUCTION-GRADE (plugin truthfulness + observability + validation gates pending)

## CRITICAL BLOCKERS FOR PRODUCTION CLOSURE

### B1 — Retrieval Generalization & Validation (NON-NEGOTIABLE)
- Preserve PR-6 locked baseline policy and deterministic behavior
- Expand beyond fixed debug closure set with controlled golden suites
- Build query → expected owner/anchor mappings across Ask / Debug / Plan / Code
- Add perturbation variants and adversarial packs
- Track false positives / false negatives / no-match honesty precision
- Detect owner drift / anchor drift / noise regression with deterministic thresholds

### B2 — Grounded Ask Validation (L5.8)
- Query → expected files mapping
- top-k correctness validation
- false positive / false negative tracking
- no-match honesty enforcement

### B3 — Plugin Truthfulness
- Show evidence_bundle entries
- Show ask_path
- Show plan_summary.notes
- Fix "(no files selected)" misleading cases
- Correct execute outcome UX

### B4 — Observability (L5-OBS-1)
- request_id propagation across:
  - Context Layer
  - Plan-Gate
  - vLLM
- Plan-Gate request logging
- endpoint path visibility
- traceability for Ask / Debug / Execute

### B5 — Host Profile Readiness
- Windows + WSL + GPU validated
- Native Linux + JetBrains validated
- Config externalization (no hardcoded localhost assumptions)

### B6 — Compatibility Path Hardening (L5.9)
- Define canonical repo_root behavior
- Control fallback paths explicitly
- Remove ambiguity between old/new paths

## L5-RET — RETRIEVAL POLICY BASELINE + VALIDATION TRACK

Objective:
Keep retrieval deterministic and baseline-protected while validating generalization.

L5-RET is now a **baseline preservation and regression-protection layer**, not an active improvement track.

### R1 — Baseline Policy Maintenance (LOCKED)
- PR-6 established deterministic owner-first retrieval baseline (`retrieval_policy.v5`)
- Baseline is frozen as canonical for true-positive debug grounding
- Any ranking logic change requires PR-6 audit re-validation on real repo before merge

### R2 — L5-RET-VALIDATION (feeds L5.8)
- Query → expected owner / anchor mapping
- Golden suites:
  - Ask-understanding
  - Debug-root-cause
  - Plan/change-impact
  - Code-targeting
  - No-match / ambiguity
  - Adversarial noise
- Perturbation suite:
  - abbreviated symbol
  - package omitted
  - CamelCase split
  - error text only
  - active-file bias
  - typo-light wording
  - subsystem alias wording
  - why/where/fix phrasing shifts

### R3 — Metrics Gates
- top-1 owner accuracy
- top-3 anchor hit
- mean first relevant rank
- noise dominance
- code ratio
- weak-evidence precision
- no-match honesty precision
- drift detection

### Done Criteria
- PR-6 baseline preserved
- L5.8 validation thresholds published and passing for expanded suites
- Regression detection active for owner/noise drift

## PR-6 Baseline Invariants (NON-NEGOTIABLE)
- Deterministic retrieval only (no embeddings, no semantic ranking)
- Workspace-local retrieval (WSL), not GPU
- Production code dominance over logs/tests/vendor
- Noise dominance must remain ~0.00
- Owner-file accuracy must not regress
- Any retrieval change must pass regression suite before merge

## L5-OBS — OBSERVABILITY TRACK

Objective:
Make system fully traceable and debuggable

### O1 — Request Propagation
- request_id across all services

### O2 — Endpoint Logging
- log:
  - /v1/export_evidence
  - /v1/ask
  - /v0/execute
  - vLLM calls

### O3 — Path Visibility
- surface ask_path in logs/UI

### O4 — Trace Reconstruction
- map request → evidence → plan → execution

### Done Criteria
- full trace available for any request
- no blind debugging required

## PRODUCTION CLOSURE GATES

System is considered production-grade only if:

[ ] Retrieval produces AIOps-dominant evidence
[ ] Ask/Debug/Plan/Code scenarios pass
[ ] Plugin reflects backend truth
[ ] Observability fully implemented
[ ] Host profiles validated
[ ] Compatibility path resolved
[ ] Documentation aligned and canonical

---

## Tracking Principle

- **Milestones are governed by artifacts, not intention.**
  - A milestone is only meaningful when its contract/spec, implementation surface, and validation evidence exist together.
- **Status changes must be artifact-driven.**
  - Moving a milestone beyond `IN_PROGRESS` requires concrete, inspectable artifacts and evidence; “started coding” is not sufficient.
- **Dependencies and unblockers must be explicit.**
  - Each milestone must name what it depends on and what the next unblocker is, so progress can be sequenced and debugged.
- **Tracking is execution-governed.**
  - This tracker reflects what is actually built and validated, not aspirational design; doctrine remains defined in Layer-1.

---

## 2. Status Legend

### 2.1 Status markers

**Color coding** (in tables below): **green** = done (COMPLETE / LOCKED) · **orange** = active (IN_PROGRESS / VALIDATING) · **gray** = not started (NOT_STARTED) · **red** = blocked (BLOCKED). Renders in GitHub and most Markdown viewers.


| Status          | Meaning                                                              |
| --------------- | -------------------------------------------------------------------- |
| **NOT_STARTED** | Milestone defined, no substantive work begun                         |
| **IN_PROGRESS** | Active engineering work underway                                     |
| **BLOCKED**     | Work paused due to dependency or risk                                |
| **VALIDATING**  | Implementation complete; in testing / verification / hardening phase |
| **COMPLETE**    | Implementation done; exit criteria met, but not doctrinally locked   |
| **LOCKED**      | Completed and ratified; further changes require explicit governance  |


### 2.2 Priority markers


| Priority     | Meaning                       |
| ------------ | ----------------------------- |
| **CRITICAL** | Must be addressed immediately |
| **HIGH**     | Near-term priority            |
| **MEDIUM**   | Important but not urgent      |
| **LOW**      | Nice-to-have or long-term     |


Status and priority should be used together, e.g. `IN_PROGRESS (CRITICAL)`.

---

## 3. Executive Progress Snapshot


| Layer  | Scope                                  | Status                    | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------ | -------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **L1** | Governance (Constitution)              | **LOCKED**                | Constitutional manifest, phase doctrine, dominance rules locked.                                                                                                                                                                                                                                                                                                                                                                                                      |
| **L2** | ML Compilation (Stages 1–8)            | **COMPLETE / LOCKED**     | Stage-6C cure validated; deterministic CONF rendering adopted; release verification PASS.                                                                                                                                                                                                                                                                                                                                                                             |
| **L3** | Runtime Enforcement / Execution        | **COMPLETE** (M3.0–M3.11) | M3.0–M3.11 complete on main; M3.12–M3.18 follow-on.                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **L4** | Observation / Drift Detection          | **COMPLETE** (Track-C)    | M4.1–M4.6 + Track-C (C1–C3) complete. Validated against real runtime ledger (.spool/ledger.db). C1–C3 demo-ready (2026-03-17).                                                                                                                                                                                                                                                                                                                                        |
| **L5** | Workspace Intelligence / Ask Grounding | **VALIDATING**            | **L5.5/L5.6 + Context Layer wheel** on branch; contracts frozen. **Active work:** backend HTTP validation ✅ operator path; **plugin alignment + observability + retrieval generalization/validation** (§1.3–§1.4) — **not** “full e2e” until those gates pass. **Deployment/validation:** runbook + `**docs/Backend Production Validation Sheet.md`** / `**docs/JetBrains Plugin Defect Isolation Sheet.md**`. Deferred: **Caveat-F1**, **Caveat-F2**; JetBrains `:test` sandbox quirk. |


---

## 4. Layer-by-Layer Milestone Tracker

### 4.1 Layer-1 — Governance

**Purpose**: Define constitutional judgment semantics (REF, CONF, DES, MIX, CODE, REACH), dominance hierarchy, irreversible boundary doctrine, collapse taxonomy, and governance protocols. Layer-1 defines *what* judgment means; lower layers implement without reinterpretation.

**Current status**: **LOCKED**


| ID   | Milestone                                    | Status | Dependencies | Exit criteria                                                                |
| ---- | -------------------------------------------- | ------ | ------------ | ---------------------------------------------------------------------------- |
| L1.1 | Constitutional Manifest v1.0 locked          | LOCKED | —            | Manifest ratified by GREG; phase semantics and dominance hierarchy explicit. |
| L1.2 | Boundary Doctrine locked                     | LOCKED | L1.1         | Irreversible boundary definitions and phrase equality rules finalized.       |
| L1.3 | Collapse Taxonomy locked                     | LOCKED | L1.1         | Collapse types (REF_SOFTENING, CONF_TO_DES, etc.) defined and immutable.     |
| L1.4 | Golden Exemplars corpus locked               | LOCKED | L1.1–L1.3    | Governance exemplars set finalized; D.N.A validation protocol enforced.      |
| L1.5 | Governance escalation (GREG) protocol locked | LOCKED | L1.1–L1.4    | Process for constitutional change defined; versioning rules in force.        |


**Dependencies**: None for new runtime work (Layer-1 is already locked).  
**Layer exit criteria**: All governance artifacts locked with version IDs; changes require formal GREG escalation and ratification.

---

### 4.2 Layer-2 — ML Compilation

**Purpose**: Compile constitutional judgment into a mutation-stable, deterministic, training-grade dataset and SFT model **without altering semantics**. Covers Stage-1–Stage-8: base mapping → variants → mutation harness → freeze → SFT.

**Current status**: **COMPLETE / LOCKED**

#### 4.2.1 Stages and Status


| Stage | Name                        | Status | Dependencies | Exit criteria                                                                 |
| ----- | --------------------------- | ------ | ------------ | ----------------------------------------------------------------------------- |
| S1    | Structural mapping          | LOCKED | L1.*         | Governance exemplars mapped to product surfaces; no new semantics introduced. |
| S2    | Artifact extraction         | LOCKED | S1           | Instructions, context, reasoning, boundaries, postures extracted losslessly.  |
| S3    | Base stabilization          | LOCKED | S2           | Bases pass D.N.A; boundaries and phases stable; REF dominance preserved.      |
| S4    | Variant generation          | LOCKED | S3           | 4 variants per base; same boundary, phase, posture; single mutation axis.     |
| S5    | Variant stability gate      | LOCKED | S4           | All variants pass POST-DRAFT D.N.A; no optimism drift or boundary aliasing.   |
| S6    | Mutation harness (6A/6B/6C) | LOCKED | S5           | Stage-6C PASS; collapse vectors fully classified; freeze unblocked.           |
| S7    | Dataset freeze              | LOCKED | S6           | Freeze manifest locked; corpus hash, variant counts, phase distribution set.  |
| S8    | SFT training                | LOCKED | S7           | SFT / adapter training complete; invariance audit PASS; release approved.     |


#### 4.2.2 Layer-2 Closure Evidence (Summary)

- **Stage-6C cure validated**:
  - Deterministic CONF runtime rendering adopted in Stage-6C mutation harness.
  - CONF→DES drift eliminated under adversarial loops.
- **CONF drift results**:
  - `S0 = 80`  
  - `conf_to_des = 0`  
  - `s2_s3 = 0`
- **Release verification**:
  - `LAYER2_RELEASE_VERIFICATION.json = PASS`
  - Dataset freeze and SFT artifacts promoted under governance-approved criteria.

**Dependencies**: Layer-1 doctrine and exemplars.  
**Layer exit criteria**: All stages S1–S8 **LOCKED**; invariance audits PASS; adapters frozen and handed off to Layer-3.

---

### 4.3 Layer-3 — Runtime Enforcement / Execution

**Purpose**: Enforce constitutional judgment at runtime. REF and CONF are governed runtime phases; DES and CODE remain model-expressive but are orchestrated by the runtime. Layer-3 owns control flow, state transitions, authority and boundary enforcement, and completion criteria. The model proposes; the runtime decides.

**Current status**: **M3.0–M3.11 COMPLETE on main.** M3.12–M3.18 are follow-on milestones.  
**Priority**: **CRITICAL**

**Canonical Layer-3 numbering:** This document uses a single canonical model M3.0–M3.18. No alternate naming (e.g. M3.E0, M3X.*) is used in live roadmap tables.

#### 4.3.1 Layer-3 Milestones (canonical M3.0–M3.18)


| ID    | Milestone                                  | Status                       | Dependencies       | Deliverable / exit criteria summary                                                                                                                                                                                                                                       |
| ----- | ------------------------------------------ | ---------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M3.0  | Deterministic Runtime Emulator             | COMPLETE                     | L2.*               | Plan-gate emulator + shadow runner + invariant tests. see §6.2.                                                                                                                                                                                                           |
| M3.1  | Deterministic Agent State Transition Table | COMPLETE                     | Plan-Gate contract | State enum, terminal states, stop reasons, transition matrix. see §6.3.                                                                                                                                                                                                   |
| M3.2  | Repository Context Engine                  | COMPLETE                     | L2.*               | Context bundles, versioned and reproducible. see §4.3.2 (M3.2).                                                                                                                                                                                                           |
| M3.3  | Agent Loop Orchestrator                    | COMPLETE                     | M3.2, M3.1         | Loop controller, transition executor, no model-controlled recursion. see §6.4, §6.12.                                                                                                                                                                                     |
| M3.4  | Execution Sandbox                          | COMPLETE                     | M3.2–M3.3          | Isolated executor, REFUSED/BLOCKED/EXECUTED, ledger. see §6.8.                                                                                                                                                                                                            |
| M3.5  | Plan-Gate Integration                      | COMPLETE                     | M3.2–M3.4          | All paths through Plan-Gate; four postures; decisions ledgered. see §6.9.                                                                                                                                                                                                 |
| M3.6  | Internal Plan-Gate Decomposition           | COMPLETE                     | M3.5               | AuthorityValidator, IrreversibilityDetector, JudgeGate. see §6.10.                                                                                                                                                                                                        |
| M3.7  | IDE Plugin Integration                     | COMPLETE                     | M3.5               | Plugin → Plan-Gate → ledger; /v0/execute; 30 tests. see §6.7.                                                                                                                                                                                                             |
| M3.8  | Ledger Emission / Replay                   | COMPLETE                     | M3.5               | Ledger completeness, replay, join contract. see §6.12.                                                                                                                                                                                                                    |
| M3.9  | Shadow Mode Validation                     | COMPLETE                     | M3.0–M3.8          | Shadow runner, no boundary crossed; plan and ledger per run. see §6.12.                                                                                                                                                                                                   |
| M3.10 | Sandbox driver abstraction                 | COMPLETE                     | M3.4               | Abstraction layer for sandbox execution drivers. see §6.13.                                                                                                                                                                                                               |
| M3.11 | Container sandbox runtime                  | COMPLETE                     | M3.10              | Container-based sandbox implementing driver abstraction. see §6.14.                                                                                                                                                                                                       |
| M3.12 | Documentation ingestion                    | **VALIDATING** (integration) | M3.0–M3.9          | Narrow repo-aware manifest / `**doc_selector`** path merged on `**feature/l5-context-layer-v1-ask-packaging**` (see **§6.16**); prior report: `docs/reports/M3_12_INTEGRATION_VERIFICATION_REPORT.md`. **Merge to `main`** still pending when integration owners promote. |
| M3.13 | Jira ingestion                             | NOT_STARTED                  | M3.0–M3.9          | Pipeline to ingest Jira data.                                                                                                                                                                                                                                             |
| M3.14 | PR ingestion                               | NOT_STARTED                  | M3.0–M3.9          | Pipeline to ingest PR data.                                                                                                                                                                                                                                               |
| M3.15 | Jira cleaning pipeline                     | NOT_STARTED                  | M3.13              | Clean and normalize Jira data.                                                                                                                                                                                                                                            |
| M3.16 | PR signal extraction                       | NOT_STARTED                  | M3.14              | Extract signals from PR data.                                                                                                                                                                                                                                             |
| M3.17 | Task schema                                | **COMPLETE** (L5 branch)     | M3.0–M3.9          | Initial task-model slice + C1 trace alignment merged on `**feature/l5-context-layer-v1-ask-packaging`** (see **§6.16**). **M3.18** harness / broader evaluation scope still open.                                                                                         |
| M3.18 | Task evaluation harness                    | NOT_STARTED                  | M3.17              | Harness to evaluate tasks against governance and runtime contracts.                                                                                                                                                                                                       |


> Note: These Layer-3 milestones are **execution milestones** and do not redefine doctrine. They implement the runtime-governed agent architecture described in the Layer-3 specs.

> Follow-on relationship note: M3.12–M3.16 remain valid downstream ingestion/enrichment milestones. They are not substitutes for workspace-local code grounding and are not the immediate blocker for grounded Ask validity.

#### 4.3.2 Artifact-Driven Milestone Details

##### M3.0 — Deterministic Runtime Emulator

**Required Artifacts**

- `runtime/plan_gate_stub/plan_gate.py`
- `runtime/emulator/authority.py`
- `runtime/emulator/boundary.py`
- `runtime/emulator/ledger.py`
- `runtime/shadow_runner/run_demo.py`
- `runtime/tests/test_emulator_invariants.py`

**Exit Criteria**

- REF path emits refusal and never `safe_execute`.
- CONF path emits `bounded_allow` and never `defer`.
- Safe approval does not default to CODE; unresolved/emulator-safe phase handling documented.
- Shadow mode never emits `boundary_verdict=crossed`.
- Deterministic `plan_hash` and `boundary_phrase_hash` behavior verified for representative cases.
- Sample IDE event fixtures (commit_prod_change, merge_without_approval, safe_commit) execute end-to-end through the emulator with consistent Plan, Decision, and Ledger outputs.

**Evidence**

- All 6 required artifacts implemented and verified.
- Shadow runner demo executed successfully with all 3 scenarios passing:
  - `merge_without_approval` → REF → refuse (PASS)
  - `commit_prod_change` → CONF → bounded_allow (PASS)
  - `safe_commit` → DES → safe_execute (PASS)
- Invariant tests (28 tests) all passing:
  - `authority_fail never produces safe_execute` (PASS)
  - `boundary_present never produces defer` (PASS)
  - `shadow mode never emits boundary_verdict=crossed` (PASS)
- Deterministic hashing verified (same event → same plan_hash).
- Ledger emission with schema_version `ledger_row.v0.1` verified.

##### M3.1 — Deterministic Agent State Transition Table

**Required Artifacts**

- `docs/runtime/RUNTIME_STATE_TRANSITIONS.md`
- `runtime/state/schemas/state_enums.v0.1.json`
- `runtime/state/schemas/transition_matrix.v0.1.json`

**Exit Criteria**

- State enum finalized (including governed runtime phases and execution states).
- Terminal states (e.g., `Completed`, `Aborted`, `Refused`) finalized.
- Stop reasons finalized and documented (e.g., budget_exhausted, explicit_refusal, boundary_block).
- Invalid transitions explicitly rejected in the transition matrix.
- Runtime-only ownership of the state machine documented (model cannot add states or transitions).

**Evidence**

- none yet

##### M3.2 — Repository Context Engine

**Required Artifacts**

- Repository context architecture note (Layer-3 doc describing responsibilities and interfaces).
- Symbol search abstraction (API and contract for code symbol lookups).
- Dependency graph abstraction (API and contract for dependency relationships between files/modules).
- Context ranking policy (rules for how context snippets are ranked and selected).

**Exit Criteria**

- Deterministic retrieval path defined (given repo revision and request, same context bundle produced).
- Repository context bundle shape documented (fields, limits, provenance).
- At least one end-to-end retrieval example captured and documented.

**Evidence**

- **Artifacts**:
  - `docs/runtime/REPOSITORY_CONTEXT_ENGINE.md` — repository context engine responsibilities, contracts, determinism rules, and out-of-scope guarantees.
  - `runtime/context/contracts.py` — `ContextRequest`, `SelectedContextRef`, `ContextItem`, `ContextBundle` contracts.
  - `runtime/context/selectors.py` — deterministic direct/sibling/import/symbol selectors (selection-only, no content).
  - `runtime/context/engine.py` — `ContextEngine.build_context_bundle()` with selection vs materialization split, caps, and fail-closed behavior.
  - `runtime/tests/test_context_engine.py` — determinism, caps, missing-file, symbol-hint, and provenance tests.
- **Determinism & caps**:
  - Same `ContextRequest` + same repo contents at a given revision → same `ContextBundle.items` ordering and `selection_reason` values (ignoring `created_at_utc`).
  - `max_files` and `max_bytes` caps enforced with `limits.truncated` set when caps are hit.
- **Fail-closed behavior**:
  - Explicitly requested missing files cause `MissingExplicitFilesError` (no silent partial bundles).
  - Selected-but-missing files during materialization raise `ContextEngineError`.
- **Tests**:
  - pytest (`python3 -m pytest runtime/tests/test_context_engine.py -v`): 6 passed

##### M3.3 — Agent Loop Orchestrator

**Required Artifacts**

- Loop controller spec (document describing the agent loop sequence and responsibilities).
- Transition executor design (how state transitions invoke Model Worker, Sandbox, and Plan-Gate).
- Retry / iteration budget rules (limits on loop depth and retries).
- Stop condition rules (conditions under which the loop terminates or escalates).

**Exit Criteria**

- Happy-path loop defined (from initial plan to completed decision).
- Invalid loop patterns rejected (e.g., uncontrolled recursion, circular transitions).
- Deterministic replay path defined using Task State Store + ledger.

**Evidence**

- see §6.12

##### M3.4 — Execution Sandbox

**Required Artifacts**

- Sandbox contract doc (document describing isolation guarantees and interfaces).
- Runner interface (API for executing commands/tests/tools inside the sandbox).
- Artifact capture spec (what logs, outputs, and artifacts are persisted).
- Isolation / cleanup policy (how environments are cleaned/reset between runs).

**Exit Criteria**

- Isolated execution flow defined end-to-end.
- Test outputs and artifacts capturable in a reproducible way.
- Cleanup semantics documented for success and failure cases.

**Evidence**

- none yet

##### M3.5 — Plan-Gate Integration

**Required Artifacts**

- `runtime/plangate/plangate_decision.py` — PlanGateDecision (posture: refuse | defer | bounded_allow | safe_execute; authority_ok, boundary_detected, irreversible, reason).
- `runtime/plangate/plangate_service.py` — PlanGateService.evaluate(request) → PlanGateDecision (deterministic, rule-based; no LLM).
- LoopController integration: Plan-Gate evaluated before validated_to_sandbox; only safe_execute may reach sandbox.
- Ledger event types: plangate_refused, plangate_deferred, plangate_bounded_allow, plangate_safe_execute (request_id, plan_hash, decision_posture, reason).
- Demo extension: SAFE_EXECUTE → execution, REFUSE → refusal, DEFER → deferred, BOUNDED_ALLOW → bounded_allow; decision + outcome printed.
- `runtime/tests/test_plangate_integration.py` — refusal/defer/bounded_allow prevent sandbox; safe_execute allows; bounded_allow distinct from defer; decision persists.
- `docs/runtime/milestones/M3.3_PLAN_GATE_INTEGRATION.md` — milestone doc.

**Exit Criteria**

- Every sandbox execution requires Plan-Gate approval; no path may bypass Plan-Gate.
- All four postures (refuse, defer, bounded_allow, safe_execute) are first-class: refuse/defer/bounded_allow prevent sandbox; only safe_execute allows transition to sandbox; bounded_allow distinct from defer (stop_reason, plangate_bounded_allow).
- Plan-Gate decisions are ledgered (plangate_refused, plangate_deferred, plangate_bounded_allow, plangate_safe_execute); linkage via request_id.
- CLI demo shows five cases (SAFE_EXECUTE, REFUSE, REFUSED no gate, DEFER, BOUNDED_ALLOW); tests verify refusal, defer, and bounded_allow paths.

**Evidence**

- see §6.9

##### M3.6 — Internal Plan-Gate Decomposition

**Required Artifacts**

- AuthorityValidator, IrreversibilityDetector, JudgeGate; PlanGateService unchanged.

**Exit Criteria**

- Plan-Gate internally decomposed; external contract unchanged.

**Evidence**

- see §6.10

##### M3.7 — IDE Plugin Integration

**Required Artifacts**

- Plugin bridge doc (how IDE plugin interacts with runtime services).
- Intercepted action map (which IDE actions are governed and how they map to Plan-Gate calls).
- Local runtime invocation path (how the plugin locates and calls the runtime gate).

**Exit Criteria**

- Plugin request path defined (from IDE action to runtime Plan-Gate invocation).
- Blocked action UX defined (how refusals and conditional blocks are surfaced).
- Runtime response display path defined (how decisions and guidance are rendered in IDE).

**Evidence**

- none yet

##### M3.8 — Ledger Emission / Replay

**Required Artifacts**

- Transition-to-ledger mapping (how state transitions and decisions map to ledger_row.v0.1 fields).
- Append-only write policy (rules and mechanisms ensuring ledger immutability).
- Replay/join contract note (how to join plan, decision, and ledger rows for audits).

**Exit Criteria**

- Join key documented (e.g., `request_id`, `plan_hash`, `event_id`).
- Append-only semantics documented (no in-place mutation, only new rows).
- Deterministic sample ledger flow defined from a traced runtime session.

**Evidence**

- see §6.12

##### M3.9 — Shadow Mode Validation

**Required Artifacts**

- Shadow protocol note (how shadow mode runs in parallel with live behavior).
- Baseline scenario list (set of representative workflows used for shadow evaluation).
- Shadow replay harness plan (how to replay shadow runs for debugging and audits).

**Exit Criteria**

- No-crossed-boundary rule documented for shadow (shadow may plan but must not cross irreversible boundaries).
- REF shadow cases listed and validated (illegitimacy and missing authority behave as expected in shadow).
- Baseline capture path defined (how shadow data is stored and exposed to Layer-4).

**Evidence**

- see §6.12

**Dependencies**:  

- Upstream: Layer-1 and Layer-2 must remain locked; no changes to doctrine or compilation while runtime is being implemented.  
- Lateral: IDE plugin and CI systems for integration; infrastructure for sandboxing and ledger storage.

**Relationship between emulator and broader runtime architecture**:

- **M3.0** is the first executable governance-enforcement slice: deterministic runtime emulator for Plan-Gate + ledger, authority validation, boundary detection, decision contracts, ledger emission, shadow runner.
- **M3.1–M3.9** define the broader runtime-governed agent architecture (state machine, context engine, orchestrator, sandbox, Plan-Gate, IDE integration, ledger, shadow) that builds on top of the emulator.
- The emulator is not replaced; it remains the governance-aligned kernel for Layer-3.

**Layer exit criteria**:

- **M3.0–M3.11** are **COMPLETE** on main; tag `layer3-runtime-governed-v1`. M3.12–M3.18 are follow-on milestones.
- No fail-open paths: when enforcement infrastructure is unavailable, default posture is REF/REFUSAL.
- Observation layer (L4) has sufficient ledger data to begin drift tracking.

---

### 4.4 Layer-4 — Observation / Drift Detection

**Purpose**: Observe and validate that runtime behavior continues to match doctrine. Layer-4 detects drift, boundary relocation, and collapse vectors in production, providing structured evidence to governance (GREG). It does not author doctrine or enforce directly.

**Current status**: **M4.1–M4.6 COMPLETE on main** (merged 2026-03-15). **Track-C (C1–C3) COMPLETE** (2026-03-17): runtime observation query layer validated and demo-ready.  
**Priority note:** Layer-3 runtime MVP is **complete on main**; Track-C closure is **done** — ongoing work is maintenance and Layer-5 integration touchpoints, not “unblocking L4.”

**Track-C (Runtime Observation Query Layer)**  

- **C1** Execution Trace Builder: deterministic trace reconstruction by request_id / canonical_hash (latest request group).  
- **C2** Execution Explanation Builder: deterministic explanation from trace.  
- **C3** Runtime Query Surface: CLI for summary, request trace/explanation, canonical_hash trace/explanation.  
- Validated against real runtime ledger (`.spool/ledger.db`; request_id `demo-runtime`; canonical_hash `4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837`).  
- Closure: `docs/runtime/TRACK_C_FINAL_CLOSURE.md`.

#### 4.4.1 Milestones

*M4.1–M4.6 merged to main 2026-03-15. See `docs/reports/M4X_MAIN_MERGE_COMPLETION.md`. Track-C final closure 2026-03-17.*


| ID   | Milestone                   | Status              | Dependencies | Deliverable                                                              | Exit criteria                                                                               |
| ---- | --------------------------- | ------------------- | ------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| M4.1 | Ledger Ingestion            | **COMPLETE** (main) | M3.8         | Service/pipeline ingesting runtime ledger rows into observation storage. | All ledger_row.v0.1 events of interest are reliably ingested and queryable.                 |
| M4.2 | Drift Baseline              | **COMPLETE** (main) | M4.1         | Baseline distributions of phases, boundaries, and collapse vectors.      | Baselines established for key metrics; thresholds approved by governance stakeholders.      |
| M4.3 | Collapse Vector Tracking    | **COMPLETE** (main) | M4.1–M4.2    | Online classification of collapse vectors in runtime behavior.           | All detected collapses are classified; unclassified collapses trigger alerts.               |
| M4.4 | Ledger Reconciliation       | **COMPLETE** (main) | M4.1         | Tools to reconcile pre-SFT, post-SFT, and runtime ledgers.               | Ability to trace changes in behavior across releases and runtime environments.              |
| M4.5 | GREG Governance Escalation  | **COMPLETE** (main) | M4.1–M4.4    | Automated pathways for generating evidence packages and triggering GREG. | Drift above threshold results in deterministic escalation with complete evidence bundles.   |
| M4.6 | Runtime Performance Metrics | **COMPLETE** (main) | M4.1–M4.4    | Metrics and dashboards for runtime performance and invariance.           | Key runtime and invariance metrics available to stakeholders; alerts wired into operations. |


**Dependencies**: Layer-3 ledger emission and runtime invariants; Layer-1 doctrine for drift definitions; Layer-2 for pre-SFT invariance baselines.  
**Layer exit criteria**: Drift detection and escalation loop closed: anomalies go from detection → evidence → GREG escalation in a repeatable, auditable way.

---

### LAYER 5 — CONTEXT LAYER & ASK SYSTEM

Status: INTEGRATION COMPLETE, QUALITY GATES PENDING

#### Completed
- L5.1 → L5.6: Indexing, retrieval, evidence schema, Ask path integration

#### In Progress / Not Started
- L5.7: Dirty buffer overlay
- L5.8: Grounded Ask validation
- L5.9: Compatibility path hardening

#### New Required Tracks
- L5-RET: Retrieval Baseline Preservation + Validation Generalization
- L5-OBS: Observability & Tracing
- L5-UX: Plugin Truthfulness Alignment

**Purpose**: Establish a workspace intelligence layer in WSL that performs workspace-local retrieval and deterministic evidence assembly before Plan-Gate evaluation. Layer-5 defines the structured evidence-bundle contract into Plan-Gate, reduces dependence on remote repo-path assumptions (`repo_root`, `ASK_DEFAULT_REPO_ROOT`) to compatibility-only behavior, and does not redesign Layer-1 governance semantics or Layer-3 execution authority.

**Priority**: **CRITICAL**


| ID   | Milestone                                  | Status      | Dependencies    | Deliverable / exit criteria summary                                                                                                                                                                                                               |
| ---- | ------------------------------------------ | ----------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| L5.0 | Grounded Ask Spike (Wave-1 / A1)           | COMPLETE    | —               | Provisional workspace-local retrieval spike; grounded evidence output proven (`workspace_intelligence/spikes/`). Not final L5.2/L5.3 architecture.                                                                                                |
| L5.1 | Workspace Resolver baseline (Wave-1 / A2)  | COMPLETE    | M3.7            | Resolver + local API skeleton (`runtime/layer5/`). Canonical workspace identity + path normalization contract.                                                                                                                                    |
| L5.2 | Deterministic Index MVP (Wave-2 / A4)      | COMPLETE    | L5.1, M3.2      | **A4:** deterministic file-level index (`runtime/layer5/index/`), `canonical_json` lifecycle, full rebuild; excludes graph/symbol/AST.                                                                                                            |
| L5.3 | Retrieval Foundation (Wave-2 / A5)         | COMPLETE    | L5.2            | **A5:** lexical deterministic retrieval (`runtime/layer5/retrieval/`), `(-score, relative_path)` ranking, breakdown; not graph/symbol lanes.                                                                                                      |
| L5.4 | Snippet + Evidence Builder (Wave-2 / A6)   | COMPLETE    | L5.3            | **A6:** bounded snippets + bundle assembly (`runtime/layer5/evidence/`). Evidence contract freeze — see **§4.5.1a** below.                                                                                                                        |
| L5.5 | Plugin Evidence Bridge (A7)                | COMPLETE    | L5.1–L5.4, M3.7 | Evidence-first: **WSL HTTP** `POST /v1/export_evidence` (wheel) or CLI / dev script → `ask_request.v1.0` → `POST /v1/ask`; controlled v0 fallback only when Context Layer **unreachable**; UI treats `evidence_bundle` as primary. See **§6.15**. |
| L5.6 | Plan-Gate Evidence Ingestion (A8)          | COMPLETE    | L5.4–L5.5, M3.5 | Plan-Gate `POST /v1/ask` validates/consumes `layer5.evidence_bundle.v1`; reasoning from bundle only (no repo ContextEngine on v1 path). See **§6.15**.                                                                                            |
| L5.7 | Dirty Buffer / Live File Overlay           | NOT_STARTED | L5.5            | Retrieval and snippet extraction can include unsaved editor buffers via deterministic overlay rules without mutating on-disk index truth.                                                                                                         |
| L5.8 | Grounded Ask Validation + Metrics          | NOT_STARTED | L5.6, L4        | Validation harness + metrics for grounded Ask validity, invalid-empty detection, no-match explainability coverage, and retrieval/Ask latency SLO tracking. **Note:** L5.7 (Dirty Buffer) is not a blocking dependency for L5.8; L5.8 validation runs on on-disk repository state, while dirty-buffer support is a correctness extension. |
| L5.9 | Compatibility Path Deprecation / Hardening | NOT_STARTED | L5.6–L5.8       | Compatibility transition with feature flags, controlled fallback path, and telemetry comparison between compatibility and workspace-local evidence paths before hardening default.                                                                |


#### 4.5.1a L5.4 — Evidence contract (freeze)

- **Schema:** `layer5.evidence_bundle.v1` (`runtime/layer5/evidence/evidence_bundle.v1.schema.json`, `evidence_bundle.v1.md`).
- **Status:** **FROZEN** (Wave-2.5 freeze-fix).
- **Golden fixture + hash:** `runtime/layer5/evidence/golden/` (`evidence_bundle.v1.masked.json`, `evidence_bundle.v1.fingerprint.sha256`); CI tests assert fingerprint stability.
- **Enforcement:** strict JSON Schema (`additionalProperties: false`), frozen `selection_reason` enum, normative byte-offset semantics, `IdentityMismatchError` policy + `require_identity_match` flag (`runtime/layer5/evidence/identity_policy.py`).

**Wave-1 closure (A1/A2/A3):** Grounded Ask proven via L5.0 spike; resolver/API skeleton established (L5.1; test env follow-up **Caveat-F1**); baseline Ask validation harness in `runtime/ask_validation/` (Wave-1 gate; latency path vs spine **Caveat-F2**). Milestone **L5.8** row below remains NOT_STARTED until full metrics/SLO and downstream scope are met.

#### 4.5.1 Ask validity criteria (grounded Ask contract)

- For repo-grounded Ask queries, at least one relevant file must be selected, **or** an explicit no-match outcome must be returned with deterministic justification.
- Evidence bundle must include: file paths, snippet spans/selectors, and per-selection reason fields.
- Empty `context_bundle.files` is invalid for grounded Ask unless accompanied by explicit no-match or scope-invalid justification.
- Plan-Gate and downstream reasoning surfaces must consume the provided bundle as evidence input, not infer hidden repository state.

#### 4.5.2 vLLM dependency boundary

- Retrieval, indexing, workspace resolution, and evidence bundling are deterministic infrastructure concerns and do not require vLLM availability.
- vLLM remains applicable for deeper reasoning/explanation synthesis over supplied evidence bundles.

#### 4.5.3 Layer-5 MVP contract-tightening checklist

- **Wave-2 shipped (A4–A6):** file-level index + lexical retrieval + evidence v1 frozen; items below that assumed broader scope (symbol/graph/watchers) remain **forward** tightening for later waves unless rescoped.
- L5.2 must lock index granularity decisions explicitly (file-level baseline, symbol-level coverage, AST-assisted parsing scope, and incremental watcher/update behavior).
- L5.3 must define retrieval lanes and ranking behavior explicitly (lexical/path lane, symbol lane, graph-expansion lane, recency/open-file bias, deterministic merge/rank output).
- L5.8 must define baseline latency/SLA targets for retrieval and end-to-end Ask to prevent correctness-only but unusable behavior.
- L5.4/L5.6 must lock evidence bundle contract versioning and determinism fields (schema version, bundle hash, revision/provenance linkage, replay/debug reproducibility).
- L5.9 must operationalize migration from compatibility path via feature flags, fallback semantics, and telemetry-based comparison gates.

**Dependencies**:  

- Upstream: existing Layer-3 runtime and plugin bridge remain stable.  
- New: Workspace Intelligence Layer contract and evidence bundle schema.
- Compatibility note: GPU-side direct repo access behavior (`repo_root`, `ASK_DEFAULT_REPO_ROOT`) is compatibility-only during migration, not the primary architecture.

**Layer exit criteria**:  

- Workspace-local retrieval produces deterministic grounded evidence bundles.  
- Ask path consumes evidence bundles and returns internally consistent files/selectors/plan surfaces.

---

## Backlog / Deferred (Layer-5)

**Caveat-F1 — Resolver test environment robustness**  
Problem: resolver tests assume `/workspace/...` in places; fails on typical local roots. Timing: late Wave-2 or early Wave-3 unless A4/A5 blocked sooner. Goal: pass on Cursor/CI `/workspace/...` and normal local checkouts. Trigger: `/workspace` assumptions block Wave-2. Success: stable green resolver tests in both layouts.

**Caveat-F2 — A3 latency path upgrade**  
Problem: A3 harness latency is truthful but not yet tied to final Wave-2 index/retrieval/evidence spine. Timing: after A4/A5/A6 deliver enough of that spine. Goal: re-instrument A3 on real index + retrieval + snippet/evidence paths. Trigger: harness latency misleading vs production path. Success: A3 reflects actual Layer-5 execution path latency.

---

## 5. Current Sprint / Current Focus

- **Current objective**: **L5.8 grounded validation execution** while preserving the locked PR-6 retrieval baseline; close **L5-OBS-1** and **plugin truthfulness** in parallel as hard production gates.
- **Active tasks**:
  - Run deployment/validation flow using `**docs/MOTADATA_DEMO_SETUP_RUNBOOK.md`** (order: **GPU → WSL → Windows**): **GPU** = m-coder + Plan-Gate + vLLM; **WSL** = wheel + indexed repo path; **Windows** = plugin + tunnels as documented. Treat `**docs/MOTADATA_DEMO_SCENARIOS.md`** as **acceptance scenarios**, not “demo-only.”
  - Verify **Deployment Success Criteria** (`docs/MOTADATA_DEMO_SCENARIOS.md` §4) where applicable; **plugin** must have **evidence-first ON** for apples-to-apples comparison with backend `/v1/ask` scripts.
  - Plan-Gate `/version` must show `**ask_request_v1`**. **Full Explain/Debug stack** requires vLLM + `**MOTADATA_EXPLAIN_VLLM_URL`** (see runbook). *Exception:* local automated smoke (§6.15) may unset vLLM env for pytest-only Plan-Gate — not the production validation path.
  - **B1 control-layer note (historical):** query `Which files implement topology anomaly scoring pipeline?` classification correction remains valid (`CODE_INTENT` vs prior `GENERIC_INTENT`). PR-6 now closes baseline retrieval dominance for the locked debug set; active work is generalized validation in L5.8.
- **Next execution order**:
  1. **L5.8** Grounded Ask Validation + Metrics (active)
  2. **L5-OBS-1** Observability & Tracing (parallel hard gate)
  3. **Plugin Truthfulness Alignment** (parallel hard gate)
  4. **M3.18** task-level Ask/Debug/Plan/Code evaluation (downstream)
  5. **L5.9** compatibility path hardening (downstream after grounded-input stability)
  6. Host readiness / acceptance / release sign-off
- **Related (M3.12):** Manifest + `doc_selector` repo-aware slice **merged** into `feature/l5-context-layer-v1-ask-packaging`. **M3.13** (Jira) / **M3.14** (PR) ingestion — NOT_STARTED.
- **Current blockers**:
  - None for **contract coherence** (A7/A8 done). Operational: Gradle JetBrains `:test` task **Index: 1, Size: 1** (separate infra debt); local exporter requires Python + script discoverability.
  - Resolver test env fragility (**Caveat-F1**); harness latency vs spine (**Caveat-F2**).
- **Immediate next action**:
  - Push `**feature/l5-context-layer-v1-ask-packaging*`* after review; delete **local** merged topic branches (`feature/m3.12-narrow-context-engine`, `cursor/m3.12-narrow-context-engine`, `integration/m3.12-context-demo`, `feature/m3.17-task-schema`, `feature/jetbrains-plugin-golden-demo-path`) to reduce clutter — **do not** delete `integration/l5-wave1-foundation` until integration owners confirm.
  - Execute validation path from runbook + validation sheets; file environment breakages as tickets (not contract redesign).

---

## 6. Completed Evidence Log

This section records **evidence of completed milestones**. Entries should be **append-only** and reference concrete artifacts (files, logs, reports).

### 6.1 Layer-2 Closure

- **Milestone**: Layer-2 ML Compilation complete and locked.  
- **Evidence**:
  - Stage-6C agent-loop mutation harness PASS with deterministic CONF runtime rendering.  
  - `conf_drift_result`:
    - `S0 = 80`
    - `conf_to_des = 0`
    - `s2_s3 = 0`
  - Deterministic CONF runtime rendering adopted as part of governance-aligned runtime enforcement.
  - `LAYER2_RELEASE_VERIFICATION.json = PASS` (location documented in Layer-2 artifacts).

### 6.2 M3.0 — Deterministic Runtime Emulator

- **Milestone**: M3.0 Deterministic Runtime Emulator — COMPLETE (2026-03-09)
- **Artifacts** (6/6):
  - `runtime/plan_gate_stub/plan_gate.py` — PlanGate class with `evaluate_plan()` method
  - `runtime/emulator/authority.py` — AuthorityChecker with deterministic rule-based validation
  - `runtime/emulator/boundary.py` — BoundaryDetector with irreversible boundary detection
  - `runtime/emulator/ledger.py` — LedgerEmitter producing `ledger_row.v0.1` records
  - `runtime/shadow_runner/run_demo.py` — Shadow runner with 3 demo scenarios
  - `runtime/tests/test_emulator_invariants.py` — 28 invariant tests
- **Evidence**:
  - Shadow runner demo (`python3 -m runtime.shadow_runner.run_demo`): ALL PASS
    - `merge_without_approval` → Phase: REF, Decision: REFUSAL, Posture: refuse
    - `commit_prod_change` → Phase: CONF, Decision: BOUNDED_ALLOW, Posture: bounded_allow
    - `safe_commit` → Phase: DES, Decision: SAFE_EXECUTE, Posture: safe_execute
  - Invariant validation: ALL PASS
    - `authority_fail never produces safe_execute`
    - `boundary_present never produces defer`
    - `shadow mode never emits boundary_verdict=crossed`
  - pytest (`python3 -m pytest runtime/tests/test_emulator_invariants.py`): 28 passed
  - Deterministic hashing verified: same event produces identical `plan_hash` and `boundary_phrase_hash`
  - Ledger rows emitted with `schema_version: ledger_row.v0.1`

### 6.3 M3.1 — Deterministic Agent State Transition Table

- **Milestone**: M3.1 Deterministic Agent State Transition Table — COMPLETE (2026-03-10)
- **Artifacts** (3/3):
  - `docs/runtime/RUNTIME_STATE_TRANSITIONS.md` — deterministic runtime state transition contract (runtime-owned control, terminal states, stop reasons, plan-gate checkpoints, decision-boundary ledger semantics)
  - `runtime/state/schemas/state_enums.v0.1.json` — state + stop_reason enums (13 states including `PLAN_EVALUATED`)
  - `runtime/state/schemas/transition_matrix.v0.1.json` — allowed transitions only, terminal non-escaping states, `transition_id`, plan-gate checkpoints, decision-boundary ledger semantics (anti-double-ledger guidance)
- **Evidence**:
  - Terminal states documented as non-escaping; invalid transitions defined as reject-by-default
  - Ledger semantics are **decision-boundary based** with explicit anti-double-ledger rule for simple REF refusal flows
  - DES explicitly constrained to **model-proposal semantics only**; execution remains runtime-owned

### 6.4 M3.3 — Agent Loop Orchestrator (Scaffold)

- **Milestone**: M3.3 Agent Loop Orchestrator — COMPLETE (2026-03-13); **final integration via §6.12.**
- **Artifacts (scaffold)**:
  - `runtime/state/store.py` — Task state store (in-memory + optional JSON persistence)
  - `runtime/state/transitions.py` — transition validator enforcing `transition_matrix.v0.1.json`
  - `runtime/orchestrator/loop_controller.py` — deterministic transition executor (load → validate → apply → persist → journal), wired to `ContextEngine` at `governance_to_context` (CONTEXT_FETCHED)
  - `runtime/tests/test_transition_executor.py` — transition executor tests (valid transitions succeed; invalid transitions refused; terminal non-escaping enforced; iteration/repetition/no-op guards; context wiring at CONTEXT_FETCHED)
- **Evidence**:
  - Store load refreshes in-memory view when reading from disk (prevents subtle divergence in long-lived processes)
  - Loop safety guards enforced:
    - retry-path iteration cap (currently applies to `review_to_proposal` only)
    - excessive consecutive repetition of the same `transition_id` is rejected
    - no-op transitions are rejected unless explicitly defined in the matrix
    - guard blocks return explicit `stop_reason` (e.g., `iteration_limit`) without forcing terminal state yet (future evolution: explicit terminal transition like `REVIEW_DECIDED -> BLOCKED`)
  - Context wiring at `CONTEXT_FETCHED`:
    - `LoopController` now constructs a `ContextRequest` from `TaskState.metadata` and calls `ContextEngine.build_context_bundle()` on the `governance_to_context` path
    - Minimal context metadata persisted in `TaskState.metadata['context_bundle']` (bundle_id, revision, paths, truncated)
    - Engine errors (`MissingExplicitFilesError` / `ContextEngineError`) are fail-closed: transition is refused with `stop_reason=\"validation_failed\"` and state remains `GOVERNANCE_CLASSIFIED`
  - pytest (`python3 -m pytest runtime/tests/test_transition_executor.py -v`): 23 passed
  - **Final integration evidence**: see §6.12 (Layer-3 governed runtime merge; 346 runtime tests; tag `layer3-runtime-governed-v1`).

### 6.7 M3.7 — IDE Plugin Integration (RuntimeBridge + Governed Actions)

- **Milestone**: M3.7 IDE Plugin Integration — COMPLETE (2026-03-12); **MVP scope: commit interception, ask flow, /v0/execute with decision ledgering and production governance.**
- **Artifacts** (11+):
  - **Plugin RuntimeBridge abstraction**:
    - `jetbrains-plugin/.../bridge/RuntimeBridge.kt` — Single integration point for all runtime calls.
    - `jetbrains-plugin/.../bridge/RuntimeOutcome.kt` — 7 distinct outcomes. No collapsing.
    - `jetbrains-plugin/.../bridge/RuntimeRequest.kt` — Unified request envelope.
    - `jetbrains-plugin/.../bridge/RuntimeResponse.kt` — Response contract with outcome, ui, reason, wasExecuted, ledgerRowId.
  - **Governed actions**:
    - `jetbrains-plugin/.../vcs/MotadataCheckinHandler.kt` — Shadow/enforcing; fail-closed.
    - `jetbrains-plugin/.../ask/AskMotadataAiAction.kt` — PLAN ONLY semantics.
    - `jetbrains-plugin/.../actions/SubmitToRuntimeAction.kt` — Explicit execution action.
  - **Runtime execute endpoint**:
    - `runtime/execute_service/handlers.py` — `/v0/execute`: Plan-Gate → ledger decision → sandbox (if safe_execute) → ledger outcome. Governance from PlanGateService only; explicit request fields (plan_gate_refuse, plan_gate_defer, plan_gate_bounded_allow) for test/demo; command parsed with shlex.split(); decision_ledger_row_id and ledger_row_id in response.
    - `runtime/ide/schemas/execute_request.v0.1.schema.json` — Optional ledger_path, plan_gate_* (test/demo).
    - `runtime/ide/schemas/execute_response.v0.1.schema.json` — decision_ledger_row_id, ledger_row_id.
  - **Tests**: `runtime/tests/test_execute_service.py` — 30 tests (validation, explicit flags, decision ledgering, shlex parsing).
  - **Documentation**: `docs/runtime/milestones/M3.4_IDE_PLUGIN_INTEGRATION.md`, `docs/runtime/JETBRAINS_PLUGIN_RUNTIME_BRIDGE.md`.
- **Evidence**:
  - **Plan-Gate decision ledgering in /v0/execute:** When ledger_path (request or MOTADATA_EXECUTE_LEDGER_PATH) is set, Plan-Gate decision is persisted (plangate_refused, plangate_deferred, plangate_bounded_allow, plangate_safe_execute) before sandbox or return. Response includes decision_ledger_row_id; ledger_row_id when executed. Decision and execution evidence are separate.
  - **Production governance:** No command-string keyword heuristics. Posture from PlanGateService.evaluate(request) only; test/demo control via explicit plan_gate_refuse, plan_gate_defer, plan_gate_bounded_allow.
  - **Command parsing:** shlex.split() for quoted args; invalid/empty command rejected; shell=False downstream.
  - **RuntimeBridge:** Single integration point; 7 distinct outcomes; fail-closed; 3 governed actions (commit, ask, submit to runtime).
  - **Tests:** pytest `runtime/tests/test_execute_service.py` — 30 passed (decision ledgering, explicit flags, shlex, no keyword path).
- **Scope (MVP):** Commit interception, ask flow, explicit runtime execution, fail-closed bridge. Not in MVP: push interception, full IDE coverage, plugin E2E in running IDE.

### 6.8 M3.4 — Execution Sandbox (CODE Phase)

- **Milestone**: M3.4 Execution Sandbox — COMPLETE (2026-03-12); **closed for MVP; demo closure and local evidence complete.**
- **Artifacts** (6/6):
  - `runtime/sandbox/sandbox_runner.py` — SandboxRunner with subprocess execution, timeout enforcement, artifact capture
  - `runtime/sandbox/sandbox_policy.py` — SandboxPolicy with command allowlist, time limits, env filtering
  - `runtime/sandbox/sandbox_result.py` — SandboxResult + **GovernedExecutionResult** (unified REFUSED/BLOCKED/EXECUTED contract)
  - `runtime/sandbox/sandbox_errors.py` — SandboxPolicyViolation, SandboxTimeout, SandboxExecutionError
  - `runtime/sandbox/sandbox_executor.py` — Returns GovernedExecutionResult; BLOCKED/EXECUTED with optional ledger_store
  - `runtime/sandbox/sandbox_ledger.py` — SandboxLedgerEmitter (in-memory)
  - `runtime/sandbox/sandbox_ledger_store.py` — **SandboxLedgerStore** (SQLite WAL, append-only) for all three outcomes
  - `runtime/sandbox/demo_governed_execution.py` — **Canonical CLI/test-harness demo** (EXECUTED, BLOCKED, REFUSED)
  - `runtime/tests/test_sandbox_runner.py`, `runtime/tests/test_sandbox_demo_e2e.py`, `runtime/tests/test_sandbox_ledger_store.py`
  - `docs/demo/M3.2_PROOF_PACK.md` — Proof pack for MVP walkthrough
- **Evidence**:
  - **Three canonical outcomes:** REFUSED (runtime denies before sandbox; refusal ledger row persisted), BLOCKED (policy blocks; blocked row persisted), EXECUTED (command runs; execution row persisted).
  - Refusal events produce ledger rows (LoopController + ledger_store when validated_to_sandbox refused).
  - Unified contract: GovernedExecutionResult with outcome_type, request_id, plan_hash, sandbox_id, ledger_row_id, refusal_reason, blocked_reason, commands_executed/blocked, artifacts, duration_ms, exit_code, stdout_summary, stderr_summary.
  - Local ledger: SQLite append-only; get_by_request_id, get_by_ledger_row_id; persistence failure raises LedgerStoreError (fail-closed).
  - Demo: `python3 -m runtime.sandbox.demo_governed_execution` runs all three cases; pytest `runtime/tests/test_sandbox_demo_e2e.py` (7 tests) + `runtime/tests/test_sandbox_ledger_store.py` (8 tests).
  - LoopController wiring: validated_to_sandbox uses result.success and result.ledger_row_id (GovernedExecutionResult); optional ledger_store for refusal rows.
  - pytest (`python3 -m pytest runtime/tests/test_sandbox_runner.py runtime/tests/test_sandbox_demo_e2e.py runtime/tests/test_sandbox_ledger_store.py runtime/tests/test_transition_executor.py -v`): 77 passed
- **M3.4 vs M3.8:** M3.4 covers sandbox execution evidence and **local deterministic persistence** sufficient for MVP demo. M3.8 covers broader ledger completeness, replay/join contract, and observation-bridge (Layer-4).
- **Architecture**:
  - DES → propose; CONF → authorize; CODE → execute (sandboxed) ← M3.4
  - Execution must never happen outside the sandbox; no bypass path.

### 6.9 M3.5 — Plan-Gate Integration

- **Milestone**: M3.5 Plan-Gate Integration — COMPLETE (2026-03-12); **all execution paths flow through Plan-Gate before sandbox; posture-complete (refuse, defer, bounded_allow, safe_execute).**
- **Artifacts** (6/6):
  - `runtime/plangate/plangate_decision.py` — PlanGateDecision (posture: refuse | defer | bounded_allow | safe_execute; authority_ok, boundary_detected, irreversible, reason); to_dict/from_dict.
  - `runtime/plangate/plangate_service.py` — PlanGateService.evaluate(request) → PlanGateDecision; deterministic rule-based (REFUSED_COMMANDS, plan_gate_defer, plan_gate_refuse, plan_gate_bounded_allow); no LLM.
  - `runtime/orchestrator/loop_controller.py` — Plan-Gate evaluated before validated_to_sandbox; refuse → REFUSED + ledger; defer → valid=False, stop_reason=deferred + plangate_deferred; bounded_allow → valid=False, stop_reason=bounded_allow + plangate_bounded_allow (distinct branch); safe_execute → sandbox; Plan-Gate not configured → refuse.
  - `runtime/sandbox/sandbox_ledger_store.py` — EVENT_PLANGATE_REFUSED, EVENT_PLANGATE_DEFERRED, EVENT_PLANGATE_BOUNDED_ALLOW, EVENT_PLANGATE_SAFE_EXECUTE; same store persists plangate_* and sandbox_*; linkage via request_id.
  - `runtime/sandbox/demo_governed_execution.py` — PlanGateService() in controller; five cases: SAFE_EXECUTE → EXECUTED, REFUSE (curl), REFUSED (no gate), DEFER → deferred, BOUNDED_ALLOW → bounded_allow; decision + outcome printed.
  - `runtime/tests/test_plangate_integration.py` — PlanGateDecision/PlanGateService (incl. force_bounded_allow, bounded_allow distinct from defer); LoopController: refusal/defer/bounded_allow prevent sandbox, safe_execute allows; decision persists; plangate_bounded_allow ledger row.
  - `docs/runtime/milestones/M3.3_PLAN_GATE_INTEGRATION.md` — milestone document; bounded_allow MVP meaning; future follow-up note (no bounded sandbox profile yet).
- **Evidence**:
  - **Execution chain:** request → Plan-Gate → runtime decision → LoopController transition → sandbox (if allowed) → ledger evidence. No execution path may bypass Plan-Gate.
  - **Postures (all four exercised):** refuse → REFUSED + plangate_refused + sandbox_refused; defer → valid=False, stop_reason=deferred + plangate_deferred; bounded_allow → valid=False, stop_reason=bounded_allow + plangate_bounded_allow (no sandbox); safe_execute → _run_sandbox_and_persist + plangate_safe_execute + sandbox_executed. Only safe_execute reaches sandbox in MVP.
  - **Governance:** DES → reasoning only; CONF → bounded safe action; CODE → execution via sandbox only. bounded_allow is first-class, non-sandbox, distinct from defer; richer bounded execution (e.g. read-only sandbox profile) is future work.
  - **Demo:** `python3 -m runtime.sandbox.demo_governed_execution` prints five outcomes including BOUNDED_ALLOW with ledger_row_id; 7 ledger rows (plangate_safe_execute, sandbox_executed, plangate_refused, sandbox_refused, sandbox_refused, plangate_deferred, plangate_bounded_allow).
  - **Tests:** pytest `runtime/tests/test_plangate_integration.py` (14 tests), `runtime/tests/test_sandbox_demo_e2e.py` (12 tests): bounded_allow proved end-to-end; distinct from defer (stop_reason, event_type).

### 6.10 M3.6 — Internal Plan-Gate Decomposition

- **Milestone**: M3.6 Internal Plan-Gate Decomposition — COMPLETE (2026-03-12); **Plan-Gate internally decomposed into explicit first-class subcomponents; external contract unchanged.**
- **Artifacts** (7/7):
  - `runtime/plangate/contracts.py` — AuthorityResult, IrreversibilityResult, JudgeInput dataclasses.
  - `runtime/plangate/authority_validator.py` — AuthorityValidator component; validates requester authority.
  - `runtime/plangate/irreversibility_detector.py` — IrreversibilityDetector component; classifies boundaries and irreversibility.
  - `runtime/plangate/judge_gate.py` — JudgeGate posture-decider; combines authority + irreversibility + hints → PlanGateDecision.
  - `runtime/tests/test_plangate_authority_validator.py` — AuthorityValidator unit tests (16 tests).
  - `runtime/tests/test_plangate_irreversibility_detector.py` — IrreversibilityDetector unit tests (18 tests).
  - `runtime/tests/test_plangate_judge_gate.py` — JudgeGate unit tests (15 tests).
- **Evidence**:
  - **Internal architecture:**
    ```
    PlanGateService
     ├─ AuthorityValidator  → AuthorityResult
     ├─ IrreversibilityDetector → IrreversibilityResult
     └─ JudgeGate → PlanGateDecision
    ```
  - **Flow:** request → AuthorityValidator → IrreversibilityDetector → JudgeGate → PlanGateDecision.
  - **External contract unchanged:** `PlanGateService.evaluate(request) → PlanGateDecision`.
  - **Fields now explicit:**
    - `authority_ok` backed by `AuthorityResult` from `AuthorityValidator`.
    - `boundary_detected` / `irreversible` backed by `IrreversibilityResult` from `IrreversibilityDetector`.
  - **Tests:** 49 new subcomponent tests (all pass); 14 integration tests (all pass); 12 E2E demo tests (all pass); demo unchanged.
  - **Nature:** Architectural hardening / decomposition, not a doctrine change. Not yet full enterprise RBAC or production-grade boundary policy.

### 6.12 Layer-3 Integration (M3.3, M3.8, M3.9)

- **Milestone**: M3.3 Agent Loop Orchestrator, M3.8 Ledger Emission/Replay, M3.9 Shadow Mode Validation — COMPLETE (2026-03-13). This section documents the final integration of these milestones on main (tag `layer3-runtime-governed-v1`).
- **Merge**:
  - Branch merged: `integration/layer3-next-verification` (merged into `main` with `--no-ff`)
  - Merge commit: `23395b60bb72d70d01fbb6750c1ffb70760c3dcd`
- **Validation evidence**:
  - **Runtime tests**: `python3 -m pytest runtime/tests` — **346 passed**
  - **Ledger demo**: `python3 -m runtime.ledger.demo_trace` — passed (all invariants satisfied)
  - **Shadow demo**: `python3 -m runtime.shadow_runner.run_demo` — passed (all scenarios, invariants held)
- **Tag**: `layer3-runtime-governed-v1` (created and pushed to origin)
- **Artifacts (summary)**: M3.3 — stop_conditions, budget_policy, transition_executor, replay, orchestrator_test_suite; M3.8 — runtime/ledger/* (contracts, emitter, store, replay, demo_trace), test_ledger_completeness; M3.9 — runtime/shadow/* (runner, harness, ingestion_batch, baseline_scenarios), shadow_runner_test, shadow_harness_test, test_emulator_invariants updates.

### 6.13 M3.10 — Sandbox Driver Abstraction

- **Milestone**: M3.10 Sandbox Driver Abstraction — COMPLETE (merged to main).
- **Artifacts**:
  - `runtime/sandbox/sandbox_driver.py` — SandboxDriver protocol, BaseSandboxDriver(ABC), LocalProcessSandboxDriver; driver_name for observability.
  - `runtime/sandbox/sandbox_executor.py` — Optional `driver` parameter; delegates to `_driver.run` / `_driver.validate_only`; default LocalProcessSandboxDriver.
  - `runtime/tests/test_sandbox_driver.py` — Driver and executor-through-driver tests.
  - `docs/runtime/milestones/M3.10_SANDBOX_DRIVER_ABSTRACTION.md`, `docs/runtime/branch_execution_notes/` (M3.10 note).
- **Evidence**:
  - Pluggable driver seam: executor owns governance and ledger; driver only runs/validates.
  - Default `SandboxExecutor()` uses LocalProcessSandboxDriver; backward compatible.
  - driver_name exposed for observability (e.g. sandbox_driver=local_process).

### 6.14 M3.11 — Container Sandbox Runtime

- **Milestone**: M3.11 Container Sandbox Runtime — COMPLETE (merged to main).
- **Container driver file**: `runtime/sandbox/container_sandbox_driver.py` — ContainerSandboxDriver(BaseSandboxDriver), driver_name = "container"; run/validate_only via podman/docker; workspace mount, exec form, timeout, --rm.
- **Tests passed**: pytest `runtime/tests/test_sandbox_runner.py` (37), `runtime/tests/test_sandbox_driver.py` (12), `runtime/tests/test_transition_executor.py` (26), `runtime/tests/test_sandbox_demo_e2e.py` (12), `runtime/tests/test_container_sandbox_driver.py` (17 passed, 1 skipped when no runtime). **Total: 105 passed, 1 skipped.**
- **Demo result**: `python3 -m runtime.sandbox.demo_governed_execution` — 7 ledger rows; refused / blocked / executed semantics preserved; DES → CODE execution and governance unchanged.
- **Fail-closed note**: Missing container runtime (podman/docker), invalid runtime path, or container run failure → SandboxExecutionError; executor returns EXECUTED (failed). No silent fallback to host or local process.
- **Opt-in backend selection**: Container backend only active when explicitly configured (e.g. `SandboxExecutor(driver=ContainerSandboxDriver())` or `create_sandbox_driver("container")`). Default remains LocalProcessSandboxDriver.
- **Commit / merge summary**:
  - **Branch name**: feature/m3.10-m3.11-execution-isolation
  - **Merge commit SHA**: 302fae2681fbfd07c732445674c988b957f170c6 (short: 302fae2)
  - **Tests run**: 105 passed, 1 skipped (test_container_sandbox_driver live test when no podman/docker).
  - **Demo result**: 7 ledger rows; refused / blocked / executed semantics preserved.

### 6.15 L5.5 / L5.6 — Wave-3 integration (A7 Plugin + A8 Plan-Gate `/v1/ask`)

- **Milestones**: **L5.5 (A7)** Plugin Evidence Bridge — COMPLETE (2026-03-21); **L5.6 (A8)** Plan-Gate Evidence Ingestion — COMPLETE (2026-03-21).
- **Artifacts (summary)**:
  - **Runtime / Plan-Gate:** `runtime/plan_gate_service/app.py` — `POST /v1/ask`; `runtime/ask_service/v1_ingest.py`; `runtime/ide/schemas/ask_request.v1.0.schema.json`; `runtime/ask_service/evidence_bridge.py` — `context_bundle_from_evidence_dict`; `runtime/tests/test_ask_v1_ingest.py`.
  - **WSL export (primary):** `packaging/motadata-context-layer/` wheel; `runtime/context_layer_service/` — `GET /healthz`, `POST /v1/export_evidence`; dev fallback `runtime/scripts/layer5_export_evidence.py`.
  - **Plugin:** `jetbrains-plugin/.../bridge/RuntimeBridge.kt`, `Layer5EvidenceExporter.kt`, `EvidenceExportOutcome.kt`, `AskV1Contract.kt`; default Context Layer URL `http://127.0.0.1:8091`; Plan-Gate default `http://127.0.0.1:8089` (see runbook for remote GPU).
- **Contract outcomes**:
  - Evidence-first uses real `**ask_request.v1.0`** and `**POST /v1/ask**` (not v0 `evidence_first` bolt-on for the primary path).
  - Listed v1 contract failures (`evidence_schema_invalid`, `identity_mismatch`, `empty_evidence_bundle`, `ask_envelope_invalid`) **do not** silently fall back to legacy.
  - Controlled fallback only: export/script failure, v1 **404/405**, or legacy mode (flag off).
- **Evidence (automated)**:
  - `python3 -m pytest runtime/tests/test_ask_v1_ingest.py` — PASS (v1 ingest + HTTP Plan-Gate slice).
- **Evidence (automated e2e smoke — Linux host, 2026-03-21)**:
  - Start Plan-Gate (`python3 -m runtime.plan_gate_service.app`, unset `MOTADATA_EXPLAIN_VLLM_URL`); `GET /healthz` OK.
  - `printf '<query>' | python3 runtime/scripts/layer5_export_evidence.py <repo_root>` → JSON evidence bundle.
  - `POST /v1/ask` with `ask_request.v1.0` + bundle (+ `expected_workspace_identity_hash` when hash non-empty) → `plan_only_response.v0.1`, `governance_posture=PLAN_ONLY`, `execution=false`, `evidence_first_meta.ask_path=v1_evidence`, non-empty `plan_summary.steps` (sample: 4 steps, 8 evidence entries).
- **Evidence (pending — operational e2e)**:
  - First full **Windows IDE + WSL Context Layer wheel + GPU Plan-Gate** run recorded by humans/CI when available; amend this subsection with transcript or run ID (checklist: `**docs/MOTADATA_DEMO_SCENARIOS.md`** §4).

### 6.16 Branch consolidation + M3.12 on L5 line (2026-03-21)

- **Unified branch:** `feature/l5-context-layer-v1-ask-packaging` now **merge-parent** for:
  - `feature/m3.12-narrow-context-engine` — `runtime/ask_service/handlers.py` gains **ManifestBuilder** + `**select_from_manifest`** (repo-aware file hints) while preserving **evidence_first**, `**ASK_DEFAULT_REPO_ROOT`**, **EXPLAIN_DEBUG**, and default **ContextEngine** selectors; `runtime/tests/test_ask_service.py` extended with M3.12 determinism tests.
  - `integration/m3.12-context-demo` — demo runbook / verification artifacts as merged.
  - `feature/m3.17-task-schema` — task-model slice + `**docs/runtime/C1_EXECUTION_TRACE_BUILDER_RESULT.md`** unified (M3.17 pre-merge sign-off appended).
- **Operator docs (in-repo):** `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md` (architecture); `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md` (setup); `docs/MOTADATA_DEMO_SCENARIOS.md` (demo + success criteria).
- **Local cleanup:** After push, safe to `**git branch -d`** the merged topic branches listed in **§5 Immediate next action** (local only unless coordinated for `origin`).

> Future entries should follow this style: **Milestone**, then bullet list of concrete evidence files / metrics / reports.

---

## 7. How to Update This Tracker

This file is the **single live progress dashboard** for the Motadata AI Coding Assistant roadmap. Future updates (including by automated tools such as Cursor) must follow these rules:

1. **Only update statuses when evidence exists**
  - Do not mark a milestone as `COMPLETE` or `LOCKED` without a corresponding evidence entry in **Section 6**.
  - Prefer moving milestones through `IN_PROGRESS → VALIDATING → COMPLETE → LOCKED` explicitly.
2. **Do not advance milestones without required artifacts and evidence**
  - A milestone may **not** be marked `VALIDATING`, `COMPLETE`, or `LOCKED` unless:
    - Its **required artifacts exist** (as listed in the milestone detail sections), and
    - Its **Evidence** section contains at least one concrete validation entry (file, metric, or report).
  - “Started coding” or partial implementation without artifacts and validation does **not** qualify.
3. **Append to the evidence log instead of rewriting history**
  - When a milestone completes, add a new subsection under **Section 6** with:
    - Milestone ID and name.
    - Bullet list of concrete evidence artifacts (files, metrics, reports).
  - Do **not** remove or rewrite prior evidence entries.
4. **Update current focus when the active milestone changes**
  - Keep **Section 5 (Current Sprint / Current Focus)** aligned with the actual active work.
  - Update:
    - `Current objective`
    - `Active tasks`
    - `Next execution order`
    - `Current blockers`
    - `Immediate next action`
5. **Do not alter constitutional doctrine**
  - Do **not** change phase semantics (REF, CONF, DES, MIX, CODE, REACH).
  - Do **not** change dominance hierarchy or irreversible boundary definitions.
  - Do **not** rename or reinterpret pipeline stages (Stage-1 through Stage-8).
  - If a documentation change appears to affect doctrine, it must be made in governance documents via a separate GREG process, **not** here.
6. **Preserve milestone IDs and naming**
  - Do not change milestone IDs (e.g., `M3.0`, `M4.1`) once created.
  - If a milestone is superseded, mark it as such in the **Notes** or **Exit criteria**, but keep the row for historical context.
7. **Keep tables and structure intact**
  - Maintain the section ordering and table structures defined in this file.
  - When adding new milestones (if ever necessary), place them in the appropriate layer section with a clear ID and description.
8. **Be concise but operational**
  - Avoid marketing language.
  - Focus on concrete status, dependencies, exit criteria, and evidence.

Following this protocol ensures that this tracker remains a durable, engineering-grade artifact that Cursor and humans can rely on for roadmap execution reviews.

---

