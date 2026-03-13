# M4.1 Slice 2 — Implementation Note (Live path wiring)

**Slice:** Wire CanonicalExecutionIntent into the live governed runtime path; normalization once before governance; DeterministicGuard; Plan-Gate consumes lossless projection; no downstream re-parse.

## Files changed

| File | Change |
|------|--------|
| `runtime/integrity/canonical_intent.py` | Added optional `branch` to CanonicalExecutionIntent (for guard). |
| `runtime/integrity/command_normalizer.py` | Set `branch` from request. |
| `runtime/integrity/plangate_bridge.py` | **New.** `intent_to_plangate_request(intent, overrides)` for lossless projection. |
| `runtime/plangate/pre_gate.py` | **New.** DeterministicGuard + GuardResult; five refusal categories. |
| `runtime/execute_service/handlers.py` | Validate → normalize once → guard → Plan-Gate → sandbox; build SandboxAction from intent only; no _parse_command after normalize. |
| `runtime/orchestrator/loop_controller.py` | validated_to_sandbox: normalize guard_inputs → intent; guard → Plan-Gate; _run_sandbox_and_persist(task_id, state, intent=intent). |
| `runtime/orchestrator/loop_controller.py` | _run_sandbox_and_persist accepts optional `intent`; when set, action built from intent only. |
| `runtime/tests/test_plangate_integration.py` | Accept "not allowed" / "pre-gate" in refusal reason (guard can refuse before Plan-Gate). |
| `runtime/tests/test_m41_slice2_integration.py` | **New.** Same-request same-canonical_hash invariant; normalization once; guard short-circuit; posture unchanged; only safe_execute to sandbox. |
| `runtime/tests/test_deterministic_guard.py` | **New.** One suite per guard refusal category; guard does not mutate intent. |

## Flow (Slice 2)

- **execute_service:** request → validate → CommandNormalizer.normalize (once) → CanonicalExecutionIntent → DeterministicGuard.evaluate → if refused return REFUSED → intent_to_plangate_request(intent) → PlanGateService.evaluate(pg_request) → if safe_execute build SandboxAction from intent only → SandboxExecutor.execute_sandbox_action(action).
- **orchestrator (validated_to_sandbox):** guard_inputs → normalize to intent → guard.evaluate(intent) → if refused return → intent_to_plangate_request(intent) → plan_gate.evaluate(pg_request) → _run_sandbox_and_persist(task_id, state, intent=intent).

## Invariants preserved

- No execution bypass (guard and Plan-Gate remain in path).
- Fail-closed (normalization failure → BLOCKED; guard refuse → REFUSED).
- Governance boundary (drivers unchanged; no governance in driver).
- Shadow isolation (unchanged).
- Ledger append-only (unchanged).
- Plan-Gate posture semantics unchanged; only safe_execute reaches sandbox.

## DeterministicGuard refusal categories

- protected_branch_mutation (main, master, release/*)
- destructive_filesystem_commands (rm, mkfs, dd, format, shred; dangerous paths)
- irreversible_system_actions (argv pattern: drop database, revoke, etc.)
- authority_mismatch (explicit authority_context="mismatch" in MVP)
- unsupported_network_execution (curl, wget)

## Test evidence summary

- **Same request → same canonical_hash:** test_execute_service_same_request_same_canonical_hash, test_handlers_same_request_same_hash_through_flow.
- **Normalization once:** test_execute_service_path_uses_intent_only_for_sandbox, test_orchestrator_path_uses_intent_for_sandbox.
- **Guard short-circuit:** test_curl_refused_by_guard_before_plangate, test_protected_branch_refused_by_guard.
- **Plan-Gate posture unchanged:** test_explicit_plan_gate_refuse/defer/bounded_allow_still_*, test_only_safe_execute_reaches_sandbox.
- **Guard categories:** test_deterministic_guard.py (12 tests, one suite per category + no mutation).
- **Regression:** test_execute_service (37), test_plangate_integration (16), orchestrator_test_suite (40) all passing.

## Stop condition

None. No bypass path, no governance in drivers, no conflict with append-only ledger or shadow.

## Follow-up (later M4.x)

- Ledger integration: add canonical_hash to decision/execution payload (Slice 3/4).
- Replay/shadow compatibility: use canonical_hash when present (Slice 4).
