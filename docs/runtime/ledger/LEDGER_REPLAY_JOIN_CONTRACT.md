# Ledger Replay and Join Contract — M3.5

## Overview

This document specifies the contract for ledger replay and join operations in the Motadata AI Coding Assistant runtime. The ledger provides append-only evidence for all runtime decisions, enabling deterministic replay and audit reconciliation.

## Key Invariants

### Append-Only Semantics

1. **No mutation**: Once a ledger row is emitted, it cannot be modified
2. **No deletion**: Ledger rows cannot be removed
3. **Deterministic emission**: Same inputs produce identical outputs

### Join Key Contract

The primary join key is `(request_id, plan_hash)`:

```
request_id: Unique identifier for the request
plan_hash: SHA-256 hash of the canonical JSON plan object
```

All ledger rows for a given runtime session share the same `request_id` and can be linked to their originating plan via `plan_hash`.

### Boundary Phrase Invariance

- `irreversible_boundary_phrase` must match exactly between plan and ledger
- Boundary phrase hash provides verification of exact match
- Mismatch indicates ledger integrity violation

## Schema: ledger_row.v0.1

All ledger rows conform to `ledger_row.v0.1` schema with required sections:

```json
{
  "schema_version": "ledger_row.v0.1",
  "event": {
    "event_id": "ldg-<32-char-hash>",
    "timestamp_utc": "ISO-8601",
    "request_id": "req-...",
    "session_id": "sess-...",
    "mode": "shadow|live",
    "runtime_version": "0.1.0"
  },
  "plan_link": {
    "plan_hash": "<64-char-sha256>",
    "plan_schema_version": "plan.v0.1"
  },
  "verdicts": {
    "phase_emitted": "REF|CONF|DES|MIX|CODE",
    "terminal_posture": "refuse|defer|bounded_allow|safe_execute",
    "authority_verdict": "pass|fail|unknown",
    "boundary_verdict": "blocked|not_reached|allowed_pre_boundary_only|crossed",
    "ref_enforced": true|false
  },
  "boundary": {
    "irreversible_boundary_phrase": "exact phrase",
    "boundary_cross_attempted": true|false,
    "boundary_crossed": true|false
  },
  "actions": {
    "tool_calls_attempted": [...],
    "execution_intents": [...]
  },
  "reason_codes": [...]
}
```

## Runtime Validation Rules

### L1: REF Enforcement Consistency
If `ref_enforced == true`, then `phase_emitted` MUST be "REF" or "MIX"

### L2: Crossed Boundary Consistency
If `boundary_crossed == true`, then `boundary_verdict` MUST be "crossed"

### L3: Attempted But Not Crossed
If `boundary_cross_attempted == true` AND `boundary_crossed == false`, then `boundary_verdict` MUST be "blocked"

### L4: Authority-Boundary Invariant
If `authority_verdict != "pass"` AND `boundary_verdict == "crossed"`, the combination is INVALID (runtime invariant violation)

### L5: Boundary Phrase Match
`irreversible_boundary_phrase` must match plan exactly; `plan_hash` links to source plan

## Replay API

### Session Reconstruction

```python
from runtime.ledger.replay import LedgerReplay
from runtime.ledger.store import LedgerStore

store = LedgerStore("path/to/ledger.db")
replay = LedgerReplay(store)

# Reconstruct a complete session
session = replay.reconstruct_session("req-001")

# Check completeness
if session.is_complete():
    print(f"Plan: {session.plan_event}")
    print(f"Decision: {session.decision_event}")
    if session.has_execution():
        print(f"Execution: {session.execution_event}")
```

### Reconciliation by Join Key

```python
# Reconcile ledger rows by (request_id, plan_hash)
result = replay.reconcile("req-001", "abc123...")

if result.is_valid():
    print("All invariants satisfied")
else:
    print(f"Violations: {result.invariant_violations}")
    print(f"Boundary phrase match: {result.boundary_phrase_match}")
```

### Duplicate Detection

```python
# Verify no duplicate emissions for a request
errors = replay.validate_no_duplicate_emissions("req-001")

if errors:
    print(f"Duplicate emission errors: {errors}")
```

### Timeline Extraction

```python
# Get chronological timeline for debugging
timeline = replay.get_session_timeline("req-001")

for event in timeline:
    print(f"{event['timestamp_utc']}: {event['phase']} -> {event['posture']}")
```

## Emission API

### Decision Emission

```python
from runtime.ledger.emitter import LedgerEmitterV1
from runtime.ledger.store import LedgerStore

store = LedgerStore("path/to/ledger.db")
emitter = LedgerEmitterV1(store=store)

plan = {"request_id": "req-001", "action": "commit"}

row = emitter.emit_decision(
    request_id="req-001",
    session_id="sess-001",
    plan=plan,
    phase_emitted="DES",
    terminal_posture="safe_execute",
    authority_verdict="pass",
    boundary_verdict="not_reached",
    ref_enforced=False,
    irreversible_boundary_phrase="",
    boundary_cross_attempted=False,
    boundary_crossed=False,
    reason_codes=[],
)
```

### Execution Emission

```python
row = emitter.emit_execution(
    request_id="req-001",
    session_id="sess-001",
    plan_hash="abc123...",
    sandbox_id="sbx-001",
    outcome="executed",
    commands_executed=["echo hello"],
    commands_blocked=[],
    exit_code=0,
    duration_ms=100,
    artifacts=["out.txt"],
)
```

## Event Types

| Event Type | Description |
|------------|-------------|
| `plan_emitted` | Plan object created |
| `decision_emitted` | Runtime decision made |
| `execution_started` | Sandbox execution started |
| `execution_completed` | Sandbox execution completed |
| `execution_refused` | Execution refused by runtime |
| `execution_blocked` | Execution blocked by policy |
| `plangate_refused` | Plan-Gate refused request |
| `plangate_deferred` | Plan-Gate deferred request |
| `plangate_bounded_allow` | Plan-Gate allowed bounded action |
| `plangate_safe_execute` | Plan-Gate allowed safe execution |
| `transition_applied` | State transition applied |
| `boundary_blocked` | Irreversible boundary blocked |

## Query Patterns

### By Request ID
```python
rows = store.get_by_request_id("req-001")
```

### By Plan Hash
```python
rows = store.get_by_plan_hash("abc123...")
```

### By Join Key
```python
rows = store.get_by_join_key("req-001", "abc123...")
```

### By Event Type
```python
from runtime.ledger.contracts import LedgerEventType
rows = store.get_by_event_type(LedgerEventType.DECISION_EMITTED)
```

### By Session ID
```python
rows = store.get_by_session_id("sess-001")
```

## Statistics and Monitoring

```python
stats = replay.get_statistics()

print(f"Total rows: {stats['total_rows']}")
print(f"Unique requests: {stats['unique_requests']}")
print(f"By phase: {stats['by_phase']}")
print(f"By posture: {stats['by_posture']}")
print(f"Invariant violations: {stats['invariant_violations']}")
```

## Integration with Layer-4 Observation

The ledger provides the evidence surface for Layer-4 observation:

1. **Ingestion**: All ledger rows are available for ingestion via `iter_all()`
2. **Drift detection**: Invariant violations indicate potential drift
3. **Audit reconciliation**: Join key enables plan-decision-execution linking
4. **Baseline capture**: Statistics provide baseline distributions

## File Locations

- Contracts: `runtime/ledger/contracts.py`
- Emitter: `runtime/ledger/emitter.py`
- Store: `runtime/ledger/store.py`
- Replay: `runtime/ledger/replay.py`
- Tests: `runtime/tests/test_ledger_completeness.py`
