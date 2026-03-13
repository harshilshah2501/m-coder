# Transition-to-Ledger Mapping — M3.5

## Overview

This document specifies how runtime state transitions and decisions map to ledger_row.v0.1 records. Every governed runtime decision produces a deterministic ledger record.

## Mapping Principle

```
State Transition / Decision → Ledger Row
         ↓
  (request_id, plan_hash)
         ↓
    Audit Trail
```

## Decision Types and Ledger Events

### Constitutional Phase Decisions

| Phase | Posture | Event Type | Ledger Fields |
|-------|---------|------------|---------------|
| REF | refuse | `decision_emitted` | `phase_emitted=REF`, `terminal_posture=refuse`, `ref_enforced=true` |
| CONF | bounded_allow | `decision_emitted` | `phase_emitted=CONF`, `terminal_posture=bounded_allow`, `boundary_verdict=allowed_pre_boundary_only` |
| CONF | defer | `decision_emitted` | `phase_emitted=CONF`, `terminal_posture=defer` |
| DES | safe_execute | `decision_emitted` | `phase_emitted=DES`, `terminal_posture=safe_execute` |
| CODE | safe_execute | `execution_completed` | `phase_emitted=CODE`, `terminal_posture=safe_execute` |

### Plan-Gate Decisions

| Posture | Event Type | Ledger Fields |
|---------|------------|---------------|
| refuse | `plangate_refused` | `terminal_posture=refuse`, `authority_verdict=fail` |
| defer | `plangate_deferred` | `terminal_posture=defer` |
| bounded_allow | `plangate_bounded_allow` | `terminal_posture=bounded_allow`, `boundary_verdict=allowed_pre_boundary_only` |
| safe_execute | `plangate_safe_execute` | `terminal_posture=safe_execute`, `authority_verdict=pass` |

### Execution Outcomes

| Outcome | Event Type | Ledger Fields |
|---------|------------|---------------|
| executed | `execution_completed` | `phase_emitted=CODE`, `terminal_posture=safe_execute`, `authority_verdict=pass` |
| blocked | `execution_blocked` | `terminal_posture=bounded_allow`, `boundary_verdict=blocked` |
| refused | `execution_refused` | `terminal_posture=refuse`, `ref_enforced=true` |

## State Transition → Ledger Mapping

### Orchestrator Transitions

| Transition ID | From State | To State | Ledger Event |
|---------------|------------|----------|--------------|
| `receive_to_classify` | TASK_RECEIVED | GOVERNANCE_CLASSIFIED | - |
| `governance_to_context` | GOVERNANCE_CLASSIFIED | CONTEXT_FETCHED | - |
| `context_to_proposal` | CONTEXT_FETCHED | PROPOSAL_GENERATED | - |
| `proposal_to_validation` | PROPOSAL_GENERATED | PROPOSAL_VALIDATED | - |
| `validated_to_sandbox` | PROPOSAL_VALIDATED | SANDBOX_EXECUTED | `execution_completed` (if allowed) |
| `review_to_proposal` | REVIEW_DECIDED | PROPOSAL_GENERATED | - |

### Decision Boundaries

State transitions that cross decision boundaries emit ledger rows:

1. **Plan-Gate Evaluation** (before `validated_to_sandbox`)
   - Always emits `plangate_*` event
   - Links to plan via `plan_hash`

2. **Sandbox Execution** (during `validated_to_sandbox`)
   - Emits `execution_*` event if sandbox executes
   - Links to decision via `request_id`

3. **Terminal States**
   - COMPLETED → final decision ledger row
   - REFUSED → `decision_emitted` with `refuse`
   - BLOCKED → `decision_emitted` with boundary verdict

## Field Derivation Rules

### event_id

Derived deterministically from:
```python
content = canonical_json({
    "request_id": request_id,
    "session_id": session_id,
    "plan_hash": plan_hash,
    "timestamp": timestamp_utc,
})
event_id = f"ldg-{sha256(content)[:32]}"
```

### plan_hash

Derived from canonical JSON of plan object:
```python
plan_hash = sha256(canonical_json(plan))
```

### boundary_phrase_hash

Derived from boundary phrase:
```python
boundary_phrase_hash = sha256(boundary_phrase.encode("utf-8"))
```

## Reason Code Mapping

| Condition | Reason Code |
|-----------|-------------|
| Missing authority | `MISSING_AUTHORITY` |
| Unknown authority | `AUTHORITY_UNKNOWN` |
| Boundary blocked | `BOUNDARY_BLOCKED` |
| Boundary relocated | `BOUNDARY_RELOCATED_DETECTED` |
| Phase mismatch | `PHASE_MISMATCH_PREVENTED` |
| REF enforced | `REF_ENFORCED` |
| Insufficient evidence | `INSUFFICIENT_EVIDENCE` |
| Tool not permitted | `TOOL_NOT_PERMITTED` |
| Safe pre-boundary only | `SAFE_PREBOUNDARY_ONLY` |

## Anti-Double-Ledger Rule

A simple REF refusal path should produce exactly one ledger row:

1. Plan-Gate evaluates request
2. Decision is `refuse` due to authority failure
3. **Single** `plangate_refused` or `decision_emitted` row emitted
4. No duplicate rows for the same decision

Detection:
```python
errors = replay.validate_no_duplicate_emissions(request_id)
```

## Trace Example

### REF Refusal Path

```
Request: merge_without_approval
User: developer (no approval_chain)

1. Plan created
   plan_hash = "abc123..."

2. Plan-Gate evaluation
   authority_verdict = fail
   decision = refuse

3. Ledger emission (single row):
   event_id: ldg-xyz789...
   event_type: plangate_refused
   request_id: req-001
   plan_hash: abc123...
   phase_emitted: REF
   terminal_posture: refuse
   authority_verdict: fail
   boundary_verdict: blocked
   ref_enforced: true
   reason_codes: [MISSING_AUTHORITY, REF_ENFORCED]
```

### Safe Execution Path

```
Request: safe_commit
User: developer

1. Plan created
   plan_hash = "def456..."

2. Plan-Gate evaluation
   authority_verdict = pass
   decision = safe_execute

3. Ledger emission (Plan-Gate):
   event_id: ldg-pg-001
   event_type: plangate_safe_execute
   ...

4. Sandbox execution
   command: ["echo", "hello"]
   exit_code: 0

5. Ledger emission (Execution):
   event_id: exec-002
   event_type: execution_completed
   phase_emitted: CODE
   terminal_posture: safe_execute
   ...
```

## Integration Points

### LoopController Integration

The `LoopController` emits ledger rows at:

1. `validated_to_sandbox` transition (Plan-Gate decision)
2. Sandbox execution result (if executed)
3. Refusal/block paths

### Emitter Integration

```python
from runtime.ledger.emitter import LedgerEmitterV1

emitter = LedgerEmitterV1(store=ledger_store)

# Plan-Gate decision
emitter.emit_plangate_decision(
    request_id=request_id,
    session_id=session_id,
    plan_hash=plan_hash,
    decision=plangate_decision,
)

# Execution
emitter.emit_execution(
    request_id=request_id,
    session_id=session_id,
    plan_hash=plan_hash,
    sandbox_id=sandbox_id,
    outcome="executed",
    ...
)
```

## Validation

Ledger rows are validated for invariants at emission time:

```python
violations = row.validate_invariants()
if violations:
    raise ValueError(f"Invariant violations: {violations}")
```

Invalid combinations are rejected before persistence, ensuring ledger integrity.
