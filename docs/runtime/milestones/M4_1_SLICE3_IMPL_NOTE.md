# M4.1 Slice 3 — Implementation Note (Ledger identity propagation)

**Slice:** Propagate execution identity into ledger records so that Plan-Gate decisions and sandbox executions share the same canonical artifact. No changes to Plan-Gate logic, DeterministicGuard, or execution flow order; only extend ledger payloads and tests.

## Identity chain

```
request → CanonicalExecutionIntent → canonical_hash
    → Plan-Gate decision (ledger row)
    → sandbox execution (ledger row)
```

Both decision and execution rows carry the same identity when intent is available.

## Files changed

| File | Change |
|------|--------|
| `runtime/execute_service/handlers.py` | `_persist_plangate_decision` accepts optional `canonical_hash`, `intent_id`; includes them in payload when provided. Call site passes from `intent`. |
| `runtime/orchestrator/loop_controller.py` | `_persist_plangate_decision` accepts optional `intent`; adds `canonical_hash` and `intent_id` to payload when intent is provided. Call site passes `intent=intent`. |
| `runtime/sandbox/sandbox_executor.py` | `_ledger_payload_with_identity(base_payload, action, backend_name)` merges identity from `action.metadata` into payload. All four append sites (BLOCKED missing hash, BLOCKED policy, EXECUTED error, EXECUTED success) use it. When metadata contains `canonical_hash`, the ledger row includes it. |
| `runtime/tests/test_m41_slice3_ledger_identity.py` | **New.** test_plangate_decision_contains_canonical_hash; test_sandbox_execution_contains_canonical_hash; test_identity_consistency; test_ledger_backward_compatibility. |

## Plan-Gate decision payload (when intent available)

- `canonical_hash` (from CanonicalExecutionIntent.canonical_hash)
- `intent_id`
- `request_id`
- `plan_hash`
- `decision_posture`
- `reason`

Included for all four event types: REFUSED, DEFERRED, BOUNDED_ALLOW, SAFE_EXECUTE.

## Sandbox execution payload (when metadata has identity)

- `canonical_hash`, `intent_id`, `request_id`, `plan_hash` from `action.metadata` when present
- `backend` (driver name, e.g. local_process)
- `execution_surface` from metadata when present
- `exit_code` (already in GovernedExecutionResult.to_dict())

**Invariant:** If SandboxExecutor receives action metadata containing `canonical_hash`, the ledger row MUST include it. If metadata lacks it (legacy path), the row may omit it.

## Ledger schema compatibility

- Append-only; no migration. Payload is JSON; older rows may not contain `canonical_hash`.
- Loading and listing (get_by_ledger_row_id, get_by_request_id, list_all) remain compatible; payload is opaque.

## Tests

- **test_plangate_decision_contains_canonical_hash:** handle_execute_request with ledger_path; assert Plan-Gate decision row payload has canonical_hash and intent_id.
- **test_sandbox_execution_contains_canonical_hash:** SandboxExecutor with action.metadata containing canonical_hash; assert execution row payload includes it and backend.
- **test_identity_consistency:** One request through full path (safe_execute); assert decision row and execution row share the same canonical_hash.
- **test_ledger_backward_compatibility:** Append rows without canonical_hash; assert get_by_request_id and list_all still load and return them.

## Constraints respected

- Plan-Gate logic unchanged.
- DeterministicGuard logic unchanged.
- Execution flow ordering unchanged.
- Only ledger identity propagation extended.
