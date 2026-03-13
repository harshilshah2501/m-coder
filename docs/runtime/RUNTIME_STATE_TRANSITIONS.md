# Runtime State Transitions — Deterministic Agent Control Contract

**Milestone**: M3.T0 — Deterministic Agent State Transition Table  
**Schema version**: state_enums.v0.1, transition_matrix.v0.1  
**Governance kernel**: M3.E0 emulator (VALIDATING)  
**Source of truth**: [LIVE_ROADMAP_TRACKER.md](../LIVE_ROADMAP_TRACKER.md)

---

## 1. Ownership Principle

**The runtime owns all control flow.** The model never mutates runtime state. The model produces proposals (code edits, plan steps, judgments); the runtime evaluates, decides, and transitions state. No model-controlled recursion or bypass.

---

## 2. State Definitions

### 2.1 All States (13)

| State | Class | Description |
|-------|-------|-------------|
| TASK_RECEIVED | intermediate | Raw event/request accepted; entry point |
| PLAN_EVALUATED | intermediate | Event normalized into plan structure; ready for governance evaluation |
| GOVERNANCE_CLASSIFIED | intermediate | PlanGate applied; authority + boundary evaluated; phase and decision determined |
| CONTEXT_FETCHED | intermediate | Repository context bundle assembled (future) |
| MODEL_PROPOSAL_READY | intermediate | Model produced a structured proposal; runtime validation pending |
| PROPOSAL_VALIDATED | intermediate | Proposal passed runtime checks; sandbox execution authorized |
| SANDBOX_EXECUTED | intermediate | Sandbox ran tools/tests; outputs captured |
| TESTS_EVALUATED | intermediate | Test results evaluated; pass/fail determined |
| REVIEW_DECIDED | intermediate | Runtime decided next step (complete, retry, or block) |
| COMPLETED | terminal | Task finished successfully; non-escaping |
| BLOCKED | terminal | Task blocked (e.g., validation failed, boundary block); non-escaping |
| FAILED | terminal | Task failed (sandbox error, test failure); non-escaping |
| ABORTED | terminal | Task aborted (user or system); non-escaping |

### 2.2 Terminal States (Non-Escaping)

**COMPLETED**, **BLOCKED**, **FAILED**, **ABORTED** have no outgoing transitions. Once reached, the task loop terminates.

---

## 3. Allowed Transitions

Only transitions defined in `runtime/state/schemas/transition_matrix.v0.1.json` are valid. All others are **invalid** and must be rejected.

### 3.1 Transition Summary

| From | To |
|------|-----|
| TASK_RECEIVED | PLAN_EVALUATED, ABORTED |
| PLAN_EVALUATED | GOVERNANCE_CLASSIFIED |
| GOVERNANCE_CLASSIFIED | COMPLETED, CONTEXT_FETCHED |
| CONTEXT_FETCHED | MODEL_PROPOSAL_READY |
| MODEL_PROPOSAL_READY | PROPOSAL_VALIDATED, BLOCKED |
| PROPOSAL_VALIDATED | SANDBOX_EXECUTED |
| SANDBOX_EXECUTED | TESTS_EVALUATED, FAILED |
| TESTS_EVALUATED | REVIEW_DECIDED, FAILED |
| REVIEW_DECIDED | COMPLETED, MODEL_PROPOSAL_READY |

---

## 4. Stop Reasons

Canonical stop reasons used when entering terminal states:

### Governance

| Reason | Description |
|--------|-------------|
| `explicit_refusal` | REF phase; authority fail or illegitimacy |
| `boundary_block` | Boundary present; execution blocked |
| `authority_fail` | Authority check failed |
| `boundary_crossed` | Irreversible boundary crossed (not in shadow) |

### Loop

| Reason | Description |
|--------|-------------|
| `budget_exhausted` | Token or cost limit reached |
| `iteration_limit` | Max loop iterations exceeded |
| `validation_failed` | Proposal failed runtime validation |
| `sandbox_error` | Sandbox execution error |
| `test_failure` | Tests failed |
| `user_abort` | User explicitly aborted |
| `timeout` | Time limit exceeded |

---

## 5. Abort Semantics

**user_abort** is allowed at these points:

| When | Allowed | Notes |
|------|---------|-------|
| Before plan normalization | Yes | TASK_RECEIVED → ABORTED; abort before event is parsed |
| After plan normalization | Yes | Implementers may allow ABORTED from PLAN_EVALUATED, CONTEXT_FETCHED, etc. if the runtime exposes abort at those states |
| During later loop states | Yes | MODEL_PROPOSAL_READY, REVIEW_DECIDED, etc. — abort on user request |

**Specification**: Abort is permitted from any **intermediate** state that has an outgoing transition to ABORTED. The transition matrix defines exactly which states allow abort. Implementers must not invent additional abort paths beyond those in the matrix. For the minimal M3.T0 slice, **TASK_RECEIVED → ABORTED** is required; other abort-from states may be added in future revisions.

---

## 6. Plan-Gate Checkpoints

PlanGate invokes AuthorityChecker, BoundaryDetector, and phase routing. Checkpoints aligned with M3.E0:

### 6.1 PLAN_EVALUATED → GOVERNANCE_CLASSIFIED

**Primary PlanGate checkpoint.** Matches M3.E0 `PlanGate.evaluate_plan()` exactly:

1. `AuthorityChecker.check(user_context, action_type)`
2. `BoundaryDetector.detect(action_type, boundary_phrase, mode)`
3. `_route_decision(authority_verdict, boundary_verdict)` → phase, decision
4. `_build_plan(event, phase, authority_verdict, boundary_verdict)`
5. `LedgerEmitter.emit(event, decision, plan)` — one row per evaluate_plan

Constitutional invariants (from M3.E0):

- `authority_fail` → never produces `safe_execute`
- `boundary_present` → never produces `defer`
- `shadow_mode` → never emits `boundary_verdict=crossed`

### 6.2 MODEL_PROPOSAL_READY → PROPOSAL_VALIDATED

Plan-gate re-check when the model's proposal touches irreversible surfaces. Authority and boundary re-validation if the proposal crosses a boundary.

### 6.3 PROPOSAL_VALIDATED → SANDBOX_EXECUTED

Authority and boundary checks before sandbox invocation.

---

## 7. Ledger Emission (Decision-Boundary Semantics)

Ledger emits at **decision boundaries**, not per transition. A decision boundary is a point where the runtime produces a governance-relevant verdict affecting outcome.

### 7.1 Default Rule: One Row per evaluate_plan

**Require exactly one `ledger_row.v0.1` per PlanGate `evaluate_plan` call.** This is the default for the governance decision boundary.

### 7.2 Avoiding Double-Ledger for REF

For a simple REF refusal flow:

```
PLAN_EVALUATED → GOVERNANCE_CLASSIFIED  (decision boundary; ledger row #1)
GOVERNANCE_CLASSIFIED → COMPLETED        (terminal outcome)
```

**Do not emit a second ledger row for GOVERNANCE_CLASSIFIED → COMPLETED** when the governance decision (REF refusal) and terminal outcome are the same event. One row per `evaluate_plan` is sufficient. The ledger row already records `terminal_posture=refuse` and `phase_emitted=REF`.

### 7.3 Optional Second Row (Distinct Terminal Outcome)

Emit an **optional** second row only when later runtime execution reaches a **distinct** terminal outcome beyond the initial governance decision. Example:

- Governance says CONF → bounded_allow; runtime proceeds to CONTEXT_FETCHED, MODEL_PROPOSAL_READY, etc.
- Later, runtime reaches COMPLETED (or BLOCKED/FAILED) after sandbox runs and tests pass.
- That second outcome is distinct from the governance decision; a second ledger row may capture the final outcome.

For the **current M3.E0 emulator slice**, one governance decision row is enough. No second row required.

---

## 8. DES Phase Semantics

**DES is explicitly a model-proposal phase only.** The model produces proposals (code edits, plan steps, judgments). The runtime evaluates and decides. DES does **not** authorize execution; authority and boundary checks remain runtime-owned.

`safe_execute` is a **runtime outcome** (terminal posture), not a DES semantic authorization. DES-classified requests may pass through to CONTEXT_FETCHED; the runtime still enforces authority and boundary at sandbox and proposal-validation checkpoints.

---

## 9. M3.E0 Mapping

| M3.E0 Flow | Spec State | Notes |
|------------|------------|-------|
| Event accepted | TASK_RECEIVED | Entry point |
| Event normalized into plan structure | PLAN_EVALUATED | Ready for governance |
| PlanGate.evaluate_plan (authority + boundary) | PLAN_EVALUATED → GOVERNANCE_CLASSIFIED | PlanGate checkpoint |
| REF → REFUSAL | GOVERNANCE_CLASSIFIED → COMPLETED | terminal_posture=refuse; one ledger row |
| CONF → BOUNDED_ALLOW | GOVERNANCE_CLASSIFIED → CONTEXT_FETCHED | decision_boundary; emulator scope ends |
| DES-classified pass-through | GOVERNANCE_CLASSIFIED → CONTEXT_FETCHED | safe_execute remains a runtime outcome, not a DES semantic authorization |
| LedgerEmitter.emit | At governance decision boundary | One row per evaluate_plan (default) |

---

## 10. Guard Conditions

Guards are evaluated by the runtime before allowing a transition. Key guards:

| Guard | Meaning |
|-------|---------|
| `event_valid` | Event parseable and well-formed |
| `phase` | Constitutional phase (REF, CONF, DES) — used to route GOVERNANCE_CLASSIFIED outcomes |
| `authority_pass` | Authority check passed |
| `boundary_pre` | Pre-boundary (no crossing) |
| `proposal_valid` | Model proposal passed runtime validation |
| `tests_pass` | Test evaluation passed |

---

## 11. Related Artifacts

- `runtime/state/schemas/state_enums.v0.1.json` — state and stop_reason enums
- `runtime/state/schemas/transition_matrix.v0.1.json` — transition matrix with transition_id, guards, plan_gate_required, decision_boundary
- `runtime/emulator/*` — M3.E0 governance kernel
- `runtime/schemas/ledger_row.v0.1.schema.json` — ledger row shape
