# Batch A — Governed runtime core (review record)

**Status:** completed (initial pass)  
**Date:** 2026-04-13  
**Scope:** `runtime/plangate/`, `runtime/orchestrator/`, `runtime/loop/`, `runtime/state/`, `runtime/sandbox/`, `runtime/execute_service/`, ledger surfaces (`runtime/sandbox/sandbox_ledger_store.py`, `runtime/obs/ledger` as applicable)  
**Prompts:** 1 (architectural consistency), 2 (governance / invariants), 4 (Plan-Gate + runtime safety), with §0 canonical path as source of truth.

## Merge posture

Findings below are **review inputs**, not mandatory blockers for every merge. Fix **P1** items on the governed path before claiming closure where relevant; **P2** can follow in separate PRs. Incremental merge to `main` is fine as long as triage tracks open P1s.

## Findings

| ID | Severity | Path class | Summary |
|----|----------|------------|---------|
| A-1 | P1 | primary | Orchestrator: `_persist_plangate_decision` swallows append failures; `safe_execute` may proceed to sandbox without a persisted `plangate_*` row when `ledger_store` is configured. File: `runtime/orchestrator/loop_controller.py`. |
| A-2 | P1 (confirm intent) | primary | Stage 3 loop: `_invoke_plan_gate` uses synthetic `command` `[task_type, intent_type]`, not real tool argv; differs from M4.1 `CanonicalExecutionIntent` path. Mitigation: sandbox policy + executor rules. File: `runtime/loop/loop_controller.py`. |
| A-3 | P2 | primary | Stage 3: broad `except Exception` around pre-loop Plan-Gate — fail-closed but weak diagnosability. File: `runtime/loop/loop_controller.py`. |
| A-4 | P2 | primary | Parameter name `plan_gate_service` on `LoopController` refers to `runtime.plangate.PlanGateService`, not HTTP `runtime/plan_gate_service/` — naming confusion for reviewers. File: `runtime/orchestrator/loop_controller.py`. |

## Explicitly out of scope (this batch)

- `runtime/plan_gate_service/` and `runtime/plan_gate_stub/` as **execution** gates (compatibility / CI / protocol surfaces per §0).

## Strong behaviors noted (no finding)

- `execute_service/handlers.py`: M4.1 chain; fail-closed when `ledger_path` set and Plan-Gate decision cannot be persisted.
- `orchestrator` `validated_to_sandbox`: refuses if Plan-Gate not configured; no sandbox on non–`safe_execute` postures.
- `SandboxExecutor`: blocks missing `canonical_hash` for strict governed identity path.

## Follow-up (manual)

1. Reproduce A-1 with failing `ledger_store.append` after a `safe_execute` decision.
2. Confirm product intent for A-2 (synthetic Plan-Gate input in Stage 3 vs argv-level gate).
