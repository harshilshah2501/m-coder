# Architecture Freeze v1 — Governed Runtime (post–M3.11)

| Architecture Freeze Version | v1 |
|-----------------------------|----|
| Repository State            | main@03acb511cc0ee723a5f6bbbb4b8275ffe069062d |
| Milestone Baseline          | M3.11 |

This freeze is immutable for this repository state. Changes to the codebase that contradict the freeze require an explicit architecture decision and a new freeze revision (v2) tied to the new commit.

**Status:** Canonical snapshot of the governed runtime architecture after M3.11. This document is authoritative for execution chain, invariants, and ownership. Changes that contradict it require an explicit architecture decision and freeze revision.

**Scope:** Layer-3 runtime (governed execution, Plan-Gate, sandbox, ledger, shadow). Does not redefine phase semantics, dominance rules, or Layer-1/2 doctrine.

---

## 1. Canonical execution chain

Governed execution flows in one direction only:

```
Orchestrator (LoopController / execute_service)
    → Plan-Gate (PlanGateService.evaluate)
    → SandboxExecutor
        → SandboxDriver (protocol; implementation chosen by executor)
            → Backend (local process or container)
```

- **Orchestrator:** Owns loop control and transition logic. Invokes Plan-Gate before any sandbox step; builds guard_inputs and receives PlanGateDecision; calls SandboxExecutor only when posture is `safe_execute`. Entry points: in-process LoopController; plugin-facing `/v0/execute` (execute_service handlers).
- **SandboxExecutor:** Single executor type. Owns governance (policy, timeout, allowlist), ledger emission for sandbox outcomes, and construction of GovernedExecutionResult. Does not implement execution; delegates to a driver.
- **SandboxDriver:** Abstraction (BaseSandboxDriver). Implementations: LocalProcessSandboxDriver (default), ContainerSandboxDriver. Driver only runs or validates; it does not emit ledger rows or build GovernedExecutionResult.
- **Backend:** Concrete execution environment—subprocess (local) or container (podman/docker). No governance or ledger logic in the backend.

No execution path may skip Orchestrator → Plan-Gate → SandboxExecutor → Driver → Backend. Subprocess or command execution in `runtime/rag/` or other out-of-band tooling is not part of this chain.

---

## 2. Approved execution surfaces

Governed execution and execution-related orchestration are **only** allowed from these trees:

| Surface | Role |
|---------|------|
| `runtime/sandbox/` | SandboxExecutor, drivers (local + container), policy, ledger store integration |
| `runtime/execute_service/` | Plugin-facing `/v0/execute`; request handling, Plan-Gate call, sandbox invocation |
| `runtime/shadow/` | Shadow runner, harness, baseline scenarios (validation only; does not run user commands through sandbox) |

Any subprocess or command execution **outside** these locations must be documented as **non-governed tooling** and must not be used for governed execution. (Example: `runtime/rag/` subprocess use is out-of-band tooling; see §6.)

---

## 3. Four runtime invariants

These must hold after every change.

1. **No bypass.** No path may execute user-requested or agent-requested side effects without going through Plan-Gate and SandboxExecutor. No “back door” execution, no config/env to disable governance.
2. **Fail-closed.** Plan-Gate unavailable → refuse. Ledger path set and persistence failure → block. Sandbox policy violation, timeout, or runtime missing → error surfaced; no silent fallback to ungoverned execution. REF dominates ambiguity.
3. **Governance boundary.** Drivers and backends do not implement governance or emit ledger rows. Only the executor and orchestration layer own decision persistence and GovernedExecutionResult. Model does not own control flow.
4. **Shadow isolation.** Shadow mode never crosses irreversible boundaries. Shadow runner uses plan + ledger semantics for validation only; it does not call SandboxExecutor for user-supplied commands. Shadow scenarios must not emit boundary_crossed / boundary_verdict=crossed.

---

## 4. Plan-Gate role

Plan-Gate is the mandatory pre-sandbox decision gate. All governed execution requests are evaluated by PlanGateService.evaluate(request) before any sandbox step.

- **Output:** PlanGateDecision (posture: refuse | defer | bounded_allow | safe_execute; authority_ok, boundary_detected, irreversible, reason).
- **Internal decomposition (M3.6):** AuthorityValidator → IrreversibilityDetector → JudgeGate → PlanGateDecision. External contract: evaluate(request) → PlanGateDecision.
- **Postures:** Only `safe_execute` may proceed to SandboxExecutor. refuse/defer/bounded_allow produce ledger evidence and stop; no sandbox run.
- **Ownership:** Plan-Gate is runtime-owned; deterministic, rule-based (no LLM in MVP). Request fields plan_gate_refuse, plan_gate_defer, plan_gate_bounded_allow are test/demo-only overrides and must not be used for production policy.

---

## 5. Ledger ownership

The runtime owns the execution ledger. No driver or backend emits ledger rows.

- **Persistence:** SandboxLedgerStore (and/or execute_service when ledger_path is set) persists Plan-Gate decisions (plangate_refused, plangate_deferred, plangate_bounded_allow, plangate_safe_execute) and sandbox outcomes (sandbox_executed, sandbox_refused, sandbox_blocked). Linkage by request_id.
- **Contract:** ledger_row.v0.1; append-only. No delete or in-place update. Replay and join contracts are defined in docs/runtime/ledger/.
- **Failure:** If ledger path is set and persistence fails, the execution path returns BLOCKED (fail-closed).

---

## 6. Shadow role

Shadow mode validates governance behavior without executing user commands through the sandbox.

- **Purpose:** Run baseline scenarios (plan + optional ledger) to assert that shadow mode never crosses irreversible boundaries and that plan/ledger semantics are consistent.
- **Constraint:** Shadow runner must not invoke SandboxExecutor for user-supplied commands. Shadow is observation and validation only.
- **Invariants:** S-1 (shadow_mode_never_crossed); S-2 (plan and ledger emitted per run where applicable). Enforced by harness and tests (e.g. test_emulator_invariants, test_shadow_mode_never_crossed).

---

## 7. Governed execution vs non-governed tooling

- **Governed execution:** User- or agent-triggered execution that must change state or run commands in the repo. Must flow through Plugin/API → Plan-Gate → SandboxExecutor → Driver → Backend. All such execution is ledgered and policy-bound.
- **Non-governed tooling:** Subprocess or helper execution in `runtime/rag/` (e.g. compiler invocations, RAG index tools) or elsewhere that is not part of the Plan-Gate / SandboxExecutor path. Out-of-band only. Must not be used to fulfill governed execution requests; must not be treated as part of the canonical execution chain. CI must not invoke governed execution for user-supplied commands (see docs/reference/CI_EXECUTION_MODEL.md).

---

## 8. Authority hierarchy among docs

| Rank | Document type | Role |
|------|----------------|------|
| 1 | **Architecture freeze** (this document) | Defines canonical execution chain, invariants, ownership, and boundaries. Changes require an explicit freeze revision. |
| 2 | **Live roadmap tracker** (docs/LIVE_ROADMAP_TRACKER.md) | Single source of progress and evidence for milestones. Must not alter doctrine or phase semantics. Updates only when evidence exists. |
| 3 | **Milestone docs** (docs/runtime/milestones/*.md) | Describe scope, artifacts, and exit criteria for a given milestone. Subordinate to freeze and tracker; may add detail but must not contradict the freeze. |
| 4 | **Historical / verification reports** (e.g. docs/runtime/verification/*.md) | Audit snapshots and findings. Reference only; they do not define current architecture. Discrepancies with freeze or tracker are resolved in favor of freeze then tracker. |

When in conflict, architecture freeze wins over roadmap tracker; roadmap tracker wins over milestone docs; milestone docs over historical reports.

**Related design:** docs/runtime/CANONICAL_EXECUTION_INTENT_v1.md — pre-M4.1 integrity design for canonical execution artifact (evaluate-once, execute-same). Does not change this freeze.
