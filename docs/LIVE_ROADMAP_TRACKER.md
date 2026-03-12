# LIVE ROADMAP TRACKER — Motadata AI Coding Assistant

## 1. Header

- **Project**: Motadata AI Coding Assistant — 4-Layer Governed Architecture  
- **Last updated**: 2026-03-10  
- **Current active layer**: **Layer-3 — Runtime Enforcement / Execution**  
- **Current active milestone focus**: **Layer-3 architecture and runtime MVP buildout (Repository Context Engine, Agent Loop Orchestrator, Execution Sandbox)**  
- **Overall status summary**:  
  - Layer-1 governance doctrine is **LOCKED**.  
  - Layer-2 ML compilation is **COMPLETE / LOCKED** (Stage-6C cure, deterministic CONF, release verification PASS).  
  - Layer-3 runtime is the **next active execution layer**.  
  - Layer-4 observation is **PARTIAL / PENDING EXPANSION**.

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

**Color coding** (in tables below): <span style="color:#2e7d32">**green** = done</span> (COMPLETE / LOCKED) · <span style="color:#e65100">**orange** = active</span> (IN_PROGRESS / VALIDATING) · <span style="color:#757575">**gray** = not started</span> (NOT_STARTED) · <span style="color:#c62828">**red** = blocked</span> (BLOCKED). Renders in GitHub and most Markdown viewers.

| Status          | Meaning                                                              |
| --------------- | -------------------------------------------------------------------- |
| <span style="color:#757575">**NOT_STARTED**</span> | Milestone defined, no substantive work begun                         |
| <span style="color:#e65100">**IN_PROGRESS**</span> | Active engineering work underway                                     |
| <span style="color:#c62828">**BLOCKED**</span>     | Work paused due to dependency or risk                                |
| <span style="color:#e65100">**VALIDATING**</span>  | Implementation complete; in testing / verification / hardening phase |
| <span style="color:#2e7d32">**COMPLETE**</span>    | Implementation done; exit criteria met, but not doctrinally locked   |
| <span style="color:#2e7d32">**LOCKED**</span>      | Completed and ratified; further changes require explicit governance  |


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


| Layer  | Scope                           | Status                | Notes                                                                                     |
| ------ | ------------------------------- | --------------------- | ----------------------------------------------------------------------------------------- |
| **L1** | Governance (Constitution)       | <span style="color:#2e7d32">**LOCKED**</span>            | Constitutional manifest, phase doctrine, dominance rules locked.                          |
| **L2** | ML Compilation (Stages 1–8)     | <span style="color:#2e7d32">**COMPLETE / LOCKED**</span> | Stage-6C cure validated; deterministic CONF rendering adopted; release verification PASS. |
| **L3** | Runtime Enforcement / Execution | <span style="color:#e65100">**IN_PROGRESS**</span>       | Architecture and runtime MVP buildout next; IDE integration later.                        |
| **L4** | Observation / Drift Detection   | **PARTIAL**           | Governance-level drift suite exists; production wiring pending.                           |


---

## 4. Layer-by-Layer Milestone Tracker

### 4.1 Layer-1 — Governance

**Purpose**: Define constitutional judgment semantics (REF, CONF, DES, MIX, CODE, REACH), dominance hierarchy, irreversible boundary doctrine, collapse taxonomy, and governance protocols. Layer-1 defines *what* judgment means; lower layers implement without reinterpretation.

**Current status**: <span style="color:#2e7d32">**LOCKED**</span>


| ID   | Milestone                                    | Status | Dependencies | Exit criteria                                                                |
| ---- | -------------------------------------------- | ------ | ------------ | ---------------------------------------------------------------------------- |
| L1.1 | Constitutional Manifest v1.0 locked          | <span style="color:#2e7d32">LOCKED</span> | —            | Manifest ratified by GREG; phase semantics and dominance hierarchy explicit. |
| L1.2 | Boundary Doctrine locked                     | <span style="color:#2e7d32">LOCKED</span> | L1.1         | Irreversible boundary definitions and phrase equality rules finalized.       |
| L1.3 | Collapse Taxonomy locked                     | <span style="color:#2e7d32">LOCKED</span> | L1.1         | Collapse types (REF_SOFTENING, CONF_TO_DES, etc.) defined and immutable.     |
| L1.4 | Golden Exemplars corpus locked               | <span style="color:#2e7d32">LOCKED</span> | L1.1–L1.3    | Governance exemplars set finalized; D.N.A validation protocol enforced.      |
| L1.5 | Governance escalation (GREG) protocol locked | <span style="color:#2e7d32">LOCKED</span> | L1.1–L1.4    | Process for constitutional change defined; versioning rules in force.        |


**Dependencies**: None for new runtime work (Layer-1 is already locked).  
**Layer exit criteria**: All governance artifacts locked with version IDs; changes require formal GREG escalation and ratification.

---

### 4.2 Layer-2 — ML Compilation

**Purpose**: Compile constitutional judgment into a mutation-stable, deterministic, training-grade dataset and SFT model **without altering semantics**. Covers Stage-1–Stage-8: base mapping → variants → mutation harness → freeze → SFT.

**Current status**: <span style="color:#2e7d32">**COMPLETE / LOCKED**</span>

#### 4.2.1 Stages and Status


| Stage | Name                        | Status | Dependencies | Exit criteria                                                                 |
| ----- | --------------------------- | ------ | ------------ | ----------------------------------------------------------------------------- |
| S1    | Structural mapping          | <span style="color:#2e7d32">LOCKED</span> | L1.*         | Governance exemplars mapped to product surfaces; no new semantics introduced. |
| S2    | Artifact extraction         | <span style="color:#2e7d32">LOCKED</span> | S1           | Instructions, context, reasoning, boundaries, postures extracted losslessly.  |
| S3    | Base stabilization          | <span style="color:#2e7d32">LOCKED</span> | S2           | Bases pass D.N.A; boundaries and phases stable; REF dominance preserved.      |
| S4    | Variant generation          | <span style="color:#2e7d32">LOCKED</span> | S3           | 4 variants per base; same boundary, phase, posture; single mutation axis.     |
| S5    | Variant stability gate      | <span style="color:#2e7d32">LOCKED</span> | S4           | All variants pass POST-DRAFT D.N.A; no optimism drift or boundary aliasing.   |
| S6    | Mutation harness (6A/6B/6C) | <span style="color:#2e7d32">LOCKED</span> | S5           | Stage-6C PASS; collapse vectors fully classified; freeze unblocked.           |
| S7    | Dataset freeze              | <span style="color:#2e7d32">LOCKED</span> | S6           | Freeze manifest locked; corpus hash, variant counts, phase distribution set.  |
| S8    | SFT training                | <span style="color:#2e7d32">LOCKED</span> | S7           | SFT / adapter training complete; invariance audit PASS; release approved.     |


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

**Current status**: <span style="color:#e65100">**IN_PROGRESS**</span> (architecture and MVP runtime)  
**Priority**: **CRITICAL**

#### 4.3.1 Milestones


| ID    | Milestone                                             | Status      | Owner      | Dependencies                                 | Deliverable                                                                          | Artifacts | Evidence | Next unblocker                      | Exit criteria                                                                                                                      |
| ----- | ----------------------------------------------------- | ----------- | ---------- | -------------------------------------------- | ------------------------------------------------------------------------------------ | --------- | -------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| M3.E0 | Deterministic Runtime Emulator                        | <span style="color:#e65100">VALIDATING</span>  | Shared     | L2.* (LOCKED), existing L3 runtime contracts | Deterministic plan-gate runtime emulator + shadow runner + invariant tests.          | 6/6       | see §6.2 | —                                   | REF/CONF/approval invariants enforced in emulator; sample IDE events execute end-to-end with deterministic hashes and ledger rows. |
| M3.T0 | Deterministic Agent State Transition Table (Contract) | <span style="color:#2e7d32">COMPLETE</span>    | Architect  | Plan-Gate runtime contract                   | Deterministic runtime transition spec + schemas for agent state machine.             | 3/3       | see §6.3 | —                                   | State enum, terminal states, stop reasons, and invalid transitions finalized; runtime-only state ownership documented.             |
| M3.0  | Repository Context Engine                             | <span style="color:#e65100">VALIDATING</span>  | Shared     | L2.*                                         | Runtime-owned service for repo/code/RAG context bundles, versioned and reproducible. | 4/4       | see §6.5 | wire LoopController → ContextEngine | Context for runtime decisions is deterministic, revision-tied, and independently auditable.                                        |
| M3.1  | Agent Loop Orchestrator                               | <span style="color:#e65100">IN_PROGRESS</span> | Architect  | M3.0, M3.T0                                  | Deterministic agent loop controller (Runtime Governor + loop control semantics).     | 0/4       | see §6.4 | write M3.1 spec artifacts           | All runtime flows pass through orchestrator; no model-controlled recursion or bypass; deterministic replay path defined.           |
| M3.2  | Execution Sandbox                                     | <span style="color:#e65100">IN_PROGRESS</span> | Architect  | M3.0–M3.1                                    | Isolated executor for tools/tests/commands under runtime control.                    | 4/4       | see §6.8 | orchestrator full integration       | Irreversible effects can only occur through the sandbox with authority/boundary checks and ledger emission.                        |
| M3.3  | Plan-Gate Integration                                 | <span style="color:#757575">NOT_STARTED</span> | Shared     | M3.0–M3.2                                    | Wiring between Plan objects, decision contracts, and runtime agent loop.             | 0/3       | none     | integration contract doc            | All relevant requests flow through Plan-Gate before execution; fail-closed behavior enforced.                                      |
| M3.4  | IDE Plugin Integration                                | <span style="color:#e65100">IN_PROGRESS</span> | Cursor/IDE | M3.3                                         | IDE plugins that route developer actions through Plan-Gate and agent loop.           | 1/3       | see §6.7 | plugin bridge doc                   | No IDE action of interest can bypass runtime enforcement; consistent UX for block/allow/bound.                                     |
| M3.5  | Ledger Emission                                       | <span style="color:#757575">NOT_STARTED</span> | Architect  | M3.3                                         | Reliable ledger_row.v0.1 emission for every runtime decision.                        | 0/3       | none     | transition-to-ledger map            | Every decision that affects execution has a corresponding ledger row linking to plan_hash; append-only semantics defined.          |
| M3.6  | Shadow Mode Validation                                | <span style="color:#757575">NOT_STARTED</span> | Shared     | M3.0–M3.5                                    | Full runtime-governed agent loop running in shadow mode.                             | 0/3       | none     | shadow protocol note                | REF/CONF invariants hold in shadow; deviations detected and explained; coverage across key workflows.                              |


> Note: These Layer-3 milestones are **execution milestones** and do not redefine doctrine. They implement the runtime-governed agent architecture described in the Layer-3 specs.

#### 4.3.2 Artifact-Driven Milestone Details

##### M3.E0 — Deterministic Runtime Emulator

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

##### M3.T0 — Deterministic Agent State Transition Table

**Required Artifacts**

- `docs/RUNTIME/RUNTIME_STATE_TRANSITIONS.md`
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

##### M3.0 — Repository Context Engine

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
  - `docs/RUNTIME/REPOSITORY_CONTEXT_ENGINE.md` — repository context engine responsibilities, contracts, determinism rules, and out-of-scope guarantees.
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

##### M3.1 — Agent Loop Orchestrator

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

- none yet

##### M3.2 — Execution Sandbox

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

##### M3.3 — Plan-Gate Integration

**Required Artifacts**

- Integration contract doc (mapping between runtime agent loop and Plan-Gate service).
- Runtime-to-plan-gate request mapping (how runtime constructs plan_request/plan objects).
- Authority / boundary handoff spec (how authority and irreversibility results feed into runtime decisions).

**Exit Criteria**

- REF path defined (illegitimacy and missing authority lead to refusal).
- CONF boundary-block path defined (conditional allowance up to boundary; block at irreversible crossing).
- Request/response mapping documented for Plan, DecisionResponse, and ledger linkage.

**Evidence**

- none yet

##### M3.4 — IDE Plugin Integration

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

##### M3.5 — Ledger Emission

**Required Artifacts**

- Transition-to-ledger mapping (how state transitions and decisions map to ledger_row.v0.1 fields).
- Append-only write policy (rules and mechanisms ensuring ledger immutability).
- Replay/join contract note (how to join plan, decision, and ledger rows for audits).

**Exit Criteria**

- Join key documented (e.g., `request_id`, `plan_hash`, `event_id`).
- Append-only semantics documented (no in-place mutation, only new rows).
- Deterministic sample ledger flow defined from a traced runtime session.

**Evidence**

- none yet

##### M3.6 — Shadow Mode Validation

**Required Artifacts**

- Shadow protocol note (how shadow mode runs in parallel with live behavior).
- Baseline scenario list (set of representative workflows used for shadow evaluation).
- Shadow replay harness plan (how to replay shadow runs for debugging and audits).

**Exit Criteria**

- No-crossed-boundary rule documented for shadow (shadow may plan but must not cross irreversible boundaries).
- REF shadow cases listed and validated (illegitimacy and missing authority behave as expected in shadow).
- Baseline capture path defined (how shadow data is stored and exposed to Layer-4).

**Evidence**

- none yet

**Dependencies**:  

- Upstream: Layer-1 and Layer-2 must remain locked; no changes to doctrine or compilation while runtime is being implemented.  
- Lateral: IDE plugin and CI systems for integration; infrastructure for sandboxing and ledger storage.

**Relationship between emulator and broader runtime architecture**:

- **M3.E0** is the first executable governance-enforcement slice for Layer-3: a deterministic runtime emulator for Plan-Gate + ledger, including authority validation, boundary detection, decision contracts, ledger emission, and shadow runner with IDE event simulation.
- **M3.T0 and M3.0+** define the broader runtime-governed agent architecture (state machine, context engine, orchestrator, sandbox, IDE integration, full shadow mode) that builds on top of the emulator.
- The deterministic runtime emulator is **not** replaced by the later architecture; it becomes the governance-aligned kernel and precursor for subsequent Layer-3 work.

**Layer exit criteria**:

- All M3.0–M3.6 milestones at least **COMPLETE**, with M3.5 (Ledger Emission) and M3.6 (Shadow Mode Validation) **VALIDATING** or **LOCKED**.
- No fail-open paths: when enforcement infrastructure is unavailable, default posture is REF/REFUSAL.
- Observation layer (L4) has sufficient ledger data to begin drift tracking.

---

### 4.4 Layer-4 — Observation / Drift Detection

**Purpose**: Observe and validate that runtime behavior continues to match doctrine. Layer-4 detects drift, boundary relocation, and collapse vectors in production, providing structured evidence to governance (GREG). It does not author doctrine or enforce directly.

**Current status**: **PARTIAL / PENDING EXPANSION**  
**Priority**: **HIGH** once Layer-3 MVP is stable.

#### 4.4.1 Milestones


| ID   | Milestone                   | Status      | Dependencies | Deliverable                                                              | Exit criteria                                                                               |
| ---- | --------------------------- | ----------- | ------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| M4.1 | Ledger Ingestion            | <span style="color:#757575">NOT_STARTED</span> | M3.5         | Service/pipeline ingesting runtime ledger rows into observation storage. | All ledger_row.v0.1 events of interest are reliably ingested and queryable.                 |
| M4.2 | Drift Baseline              | <span style="color:#757575">NOT_STARTED</span> | M4.1         | Baseline distributions of phases, boundaries, and collapse vectors.      | Baselines established for key metrics; thresholds approved by governance stakeholders.      |
| M4.3 | Collapse Vector Tracking    | <span style="color:#757575">NOT_STARTED</span> | M4.1–M4.2    | Online classification of collapse vectors in runtime behavior.           | All detected collapses are classified; unclassified collapses trigger alerts.               |
| M4.4 | Ledger Reconciliation       | <span style="color:#757575">NOT_STARTED</span> | M4.1         | Tools to reconcile pre-SFT, post-SFT, and runtime ledgers.               | Ability to trace changes in behavior across releases and runtime environments.              |
| M4.5 | GREG Governance Escalation  | <span style="color:#757575">NOT_STARTED</span> | M4.1–M4.4    | Automated pathways for generating evidence packages and triggering GREG. | Drift above threshold results in deterministic escalation with complete evidence bundles.   |
| M4.6 | Runtime Performance Metrics | <span style="color:#757575">NOT_STARTED</span> | M4.1–M4.4    | Metrics and dashboards for runtime performance and invariance.           | Key runtime and invariance metrics available to stakeholders; alerts wired into operations. |


**Dependencies**: Layer-3 ledger emission and runtime invariants; Layer-1 doctrine for drift definitions; Layer-2 for pre-SFT invariance baselines.  
**Layer exit criteria**: Drift detection and escalation loop closed: anomalies go from detection → evidence → GREG escalation in a repeatable, auditable way.

---

## 5. Current Sprint / Current Focus

- **Current objective**: **Layer-3 architecture and runtime MVP buildout**  
  - Define and stabilize Runtime Governor and Deterministic Agent Loop.  
  - Stand up Repository Context Engine and Execution Sandbox scaffolding.
- **Active tasks**:
  - Implement **M3.E0 Deterministic Runtime Emulator**: plan_gate stub, authority/boundary/ledger helpers, shadow runner CLI, and invariant tests.
  - Deliver **M3.T0 Deterministic Agent State Transition Table**: runtime-owned control contract + state enums + transition matrix (see §6.3).
  - Begin **M3.1 Agent Loop Orchestrator** spec + deterministic transition-executor scaffold: task state store + transition validation + loop controller (see §6.4).
  - Finalize high-level architecture docs for Runtime Governor, Task State Store, Deterministic Agent Loop, Repository Context Engine, Execution Sandbox, Model Worker Interface.
- **Next 3 milestones**:
  1. **M3.E0 Deterministic Runtime Emulator** — <span style="color:#e65100">VALIDATING</span> (all artifacts implemented, invariant tests passing)
  2. **M3.0 Repository Context Engine** — <span style="color:#e65100">VALIDATING</span> (deterministic context engine implemented; tests passing)
  3. **M3.2 Execution Sandbox** — <span style="color:#e65100">IN_PROGRESS</span> (sandbox runner, policy, ledger integration implemented; tests passing)
- **Current blockers**:
  - Final decision on sandboxing strategy (e.g., process isolation, containerization) and resource constraints.
  - Tooling and infra selection for ledger storage and replay (shared with Layer-4 needs).
- **Immediate next action**:
  - **M3.2 sandbox ↔ LoopController wiring done:** transition `validated_to_sandbox` (PROPOSAL_VALIDATED → SANDBOX_EXECUTED) now invokes SandboxExecutor when guard_inputs provide `command` and `working_dir`; result persisted in state metadata for downstream guards. Next: JetBrains plugin CommitContext resolution so plugin compiles and runs for demos; ledger storage/replay tooling (Layer-4).

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

### 6.2 M3.E0 — Deterministic Runtime Emulator

- **Milestone**: M3.E0 Deterministic Runtime Emulator — <span style="color:#e65100">VALIDATING</span> (2026-03-09)
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

### 6.3 M3.T0 — Deterministic Agent State Transition Table

- **Milestone**: M3.T0 Deterministic Agent State Transition Table — <span style="color:#2e7d32">COMPLETE</span> (2026-03-10)
- **Artifacts** (3/3):
  - `docs/RUNTIME/RUNTIME_STATE_TRANSITIONS.md` — deterministic runtime state transition contract (runtime-owned control, terminal states, stop reasons, plan-gate checkpoints, decision-boundary ledger semantics)
  - `runtime/state/schemas/state_enums.v0.1.json` — state + stop_reason enums (13 states including `PLAN_EVALUATED`)
  - `runtime/state/schemas/transition_matrix.v0.1.json` — allowed transitions only, terminal non-escaping states, `transition_id`, plan-gate checkpoints, decision-boundary ledger semantics (anti-double-ledger guidance)
- **Evidence**:
  - Terminal states documented as non-escaping; invalid transitions defined as reject-by-default
  - Ledger semantics are **decision-boundary based** with explicit anti-double-ledger rule for simple REF refusal flows
  - DES explicitly constrained to **model-proposal semantics only**; execution remains runtime-owned

### 6.4 M3.1 — Agent Loop Orchestrator (Scaffold)

- **Milestone**: M3.1 Agent Loop Orchestrator — <span style="color:#e65100">IN_PROGRESS</span> (2026-03-10)
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

### 6.7 M3.4 — IDE Plugin Integration (MVP Shadow-Mode + Repo-Aware Ask)

- **Milestone**: M3.4 IDE Plugin Integration — <span style="color:#e65100">IN_PROGRESS</span> (2026-03-10)
- **Artifacts**:
  - `jetbrains-plugin/` — IntelliJ Platform plugin module with:
    - Commit interception (shadow-mode): `PlanGateClient`, `MotadataCheckinHandler`, `DecisionLogger`, `PlanGateClientTest`.
    - Repo-aware Ask (PLAN ONLY): `AskClient`, `AskMotadataAiAction` (Tools → “Ask Motadata AI”), Ask UI surface showing PLAN ONLY badge, context bundle, selectors used, and plan summary.
  - Runtime ask path:
    - `runtime/ide/schemas/ask_request.v0.1.schema.json` — AskRequest schema.
    - `runtime/ide/schemas/plan_only_response.v0.1.schema.json` — PlanOnlyResponse schema (execution=false, governance_posture=PLAN_ONLY).
    - `runtime/ask_service/handlers.py` — `/v0/ask` handler (AskRequest → ContextRequest → `ContextEngine.build_context_bundle()` → PlanOnlyResponse).
    - `runtime/ask_service/planner.py` — `PlanOnlyPlanner` (deterministic, bounded 3–6 read/inspect-only steps; no execution, no tool calls, no model autonomy).
    - `runtime/tests/test_ask_service.py` — unit test asserting `execution is False`, `governance_posture == \"PLAN_ONLY\"`, and 3–6 steps.
  - Documentation:
    - `docs/RUNTIME/JETBRAINS_PLUGIN_MVP_SPIKE.md` — extended with “Repo-Aware Ask / Safe Planning (PLAN ONLY)” section (architecture flow, runtime interaction, context bundle explanation, demo steps).
- **Evidence**:
  - Manual verification that `/v0/ask` accepts AskRequest v0.1, calls `ContextEngine`, returns PlanOnlyResponse v0.1 with deterministic `context_bundle.files[].selection_reason`, `governance_posture=PLAN_ONLY`, and `execution=false`.
  - Sandbox IDE flow:
    - Tools → “Ask Motadata AI” sends AskRequest with repo_root + revision + query.
    - Response dialog shows PLAN ONLY badge, context bundle file list with selection reasons, selectors used, and 3–6 deterministic plan steps.
    - No execution, sandboxing, or code edits are performed; failure cases are surfaced as non-blocking warnings without client-side fallback planning.

### 6.8 M3.2 — Execution Sandbox (CODE Phase)

- **Milestone**: M3.2 Execution Sandbox — <span style="color:#e65100">IN_PROGRESS</span> (2026-03-11)
- **Artifacts** (4/4):
  - `runtime/sandbox/sandbox_runner.py` — SandboxRunner with subprocess execution, timeout enforcement, artifact capture
  - `runtime/sandbox/sandbox_policy.py` — SandboxPolicy with command allowlist, time limits, env filtering
  - `runtime/sandbox/sandbox_result.py` — SandboxResult dataclass for execution outputs
  - `runtime/sandbox/sandbox_errors.py` — SandboxPolicyViolation, SandboxTimeout, SandboxExecutionError
  - `runtime/sandbox/sandbox_executor.py` — Orchestrator integration with SandboxAction and SandboxExecutionResult
  - `runtime/sandbox/sandbox_ledger.py` — SandboxLedgerEmitter for ledger_row.v0.1 emission
  - `runtime/tests/test_sandbox_runner.py` — 37 tests covering runner, policy, result, ledger, executor
- **Evidence**:
  - Sandbox runner validates commands against policy before execution (fail-closed)
  - Allowed commands include: pytest, python, ruff, black, mypy, npm, go, cargo, etc.
  - Timeout enforcement via subprocess with configurable limits (default 30s)
  - stdout/stderr captured with size limits (default 1MB)
  - Artifact detection via pre/post file scanning
  - Environment filtering: blocklist strips secrets (AWS_*, GITHUB_TOKEN, etc.)
  - Ledger emission with deterministic event_id (sha256-based)
  - Orchestrator integration via `execute_sandbox_action()` convenience function
  - **LoopController wiring:** transition `validated_to_sandbox` (PROPOSAL_VALIDATED → SANDBOX_EXECUTED) invokes SandboxExecutor when `guard_inputs` provide `command` and `working_dir`; result (`last_sandbox_success`, `last_sandbox_ledger_id`) persisted in task state for downstream guards (`sandbox_to_tests` / `sandbox_to_failed`). Tests in `runtime/tests/test_transition_executor.py::TestLoopControllerSandboxIntegration`.
  - pytest (`python3 -m pytest runtime/tests/test_sandbox_runner.py -v`): 37 passed
- **Architecture**:
  - DES → propose
  - CONF → authorize
  - CODE → execute (sandboxed) ← M3.2
  - Execution must never happen outside the sandbox

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
    - `Next 3 milestones`
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