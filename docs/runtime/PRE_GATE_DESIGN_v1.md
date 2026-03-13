# Pre-Gate Design v1 — Deterministic Guards

**Status:** Design only. No implementation in this document.

**Purpose:** Define a deterministic pre-gate layer that runs before Plan-Gate and hard-fails on a fixed set of categories. This document describes intent, categories, decision flow, and integration point. It does not specify code.

---

## 1. Purpose of deterministic guards

- **Early, unambiguous refusal:** Before any policy or model-dependent logic, a set of checks that are purely syntactic or rule-based can refuse a request. This reduces load on Plan-Gate and makes certain failures independent of authority/boundary configuration.
- **Reproducibility:** Guards are deterministic (same request → same outcome). No LLM, no external service. Auditable and testable.
- **Clear failure reason:** When a guard fires, the reason falls into one of the hard-fail categories below. The response can be immediate (e.g. REFUSED with a specific reason code) without entering Plan-Gate.

Guards do **not** replace Plan-Gate. They sit in front of it. Requests that pass the guards still go to Plan-Gate; only requests that trigger a hard-fail category are refused before Plan-Gate.

---

## 2. Relationship to Plan-Gate

- **Pre-gate runs first.** Request → DeterministicGuard → (if pass) → Plan-Gate → (if safe_execute) → SandboxExecutor.
- **Plan-Gate remains the governance gate.** Pre-gate does not decide posture (refuse/defer/bounded_allow/safe_execute). It only decides “hard-fail immediately” vs “proceed to Plan-Gate.”
- **No overlap of responsibility.** Plan-Gate owns authority, boundary, and posture. Pre-gate owns a fixed set of hard-fail categories that are always refused regardless of Plan-Gate configuration.
- **Ledger:** If pre-gate hard-fails, the refusal can be ledgered (e.g. as a distinct event type or reason) so that the path is still auditable. Design choice: same store as Plan-Gate refusals, with a reason/category that indicates “pre-gate hard-fail.”

---

## 3. Hard-fail categories

The following categories cause **immediate refusal** before Plan-Gate. No sandbox run, no Plan-Gate evaluation.

| Category | Description | Rationale |
|----------|-------------|-----------|
| **Protected branch mutation** | Request targets a branch that is protected (e.g. main, release/*) for write or execution. | Prevents governed execution from being used to mutate protected branches. |
| **Destructive filesystem commands** | Command or arguments indicate bulk destructive FS operations (e.g. rm -rf /, format, overwrite of system paths) that are never allowed in the sandbox. | Avoids accidental or malicious wipe; rule set is fixed and conservative. |
| **Irreversible system actions** | Command or arguments indicate irreversible system-level actions (e.g. drop database, revoke credentials, delete immutable artifact) that the runtime never allows. | Aligns with constitutional “irreversible boundary”; hard-fail is deterministic before boundary policy. |
| **Authority mismatch** | Request claims an authority or context that does not match the caller’s allowed scope (e.g. role, token, or request metadata). | Ensures execution context is consistent with identity/authority before any policy evaluation. |
| **Unsupported network execution** | Request asks for outbound network execution (e.g. arbitrary curl, wget to arbitrary URL) that is not in the supported allowlist (e.g. no network, or only specific APIs). | Keeps execution local/container-scoped; avoids ungoverned network side effects. |

Each category must be defined in the design with **concrete, testable criteria** (e.g. branch name list, command/arg patterns, or metadata checks). Implementation would encode these as deterministic rules.

---

## 4. Decision flow

```
Request
   → DeterministicGuard.evaluate(request)
        → if hard_fail(category) → REFUSED (reason = category); optional ledger row; stop.
        → if pass → forward to Plan-Gate
   → PlanGateService.evaluate(request)
        → posture: refuse | defer | bounded_allow | safe_execute
   → if safe_execute only → SandboxExecutor.execute_sandbox_action(...)
```

- **Single entry:** All governed execution requests that reach Plan-Gate have already passed the deterministic guard (or the guard is not yet implemented; see integration point).
- **No bypass:** The guard is part of the same entry path as Plan-Gate (orchestrator or execute_service). There is no path that skips the guard and goes straight to Plan-Gate when the guard is enabled.

---

## 5. Where this would integrate in runtime

- **Approved execution surfaces (per ARCHITECTURE_FREEZE_v1):** Integration belongs in the same surfaces that today call Plan-Gate: `runtime/execute_service/` (handlers) and `runtime/orchestrator/` (LoopController). No new execution surface; the guard is a step inside the existing chain.
- **Execute service:** In `handle_execute_request`, after validation and before building the Plan-Gate request (or before calling PlanGateService.evaluate), call the deterministic guard. If guard returns hard-fail, return REFUSED and optionally persist a refusal ledger row; do not call Plan-Gate.
- **Orchestrator:** In the path that prepares guard_inputs and calls Plan-Gate (e.g. before `PlanGateService.evaluate`), call the deterministic guard first. If hard-fail, transition to refusal and ledger; do not call Plan-Gate or SandboxExecutor.
- **Module placement:** A dedicated module under an approved surface (e.g. `runtime/plangate/pre_gate.py` or `runtime/execute_service/pre_gate.py`) could host the guard logic so that execute_service and orchestrator both call the same implementation. No code in this doc; placement is a recommendation for implementation.

---

## 6. Summary

| Item | Design choice |
|------|----------------|
| Purpose | Deterministic, early refusal for a fixed set of categories; reproducible and auditable. |
| Relation to Plan-Gate | Pre-gate runs first; pass → Plan-Gate. Plan-Gate remains the governance gate. |
| Hard-fail categories | Protected branch mutation; destructive filesystem commands; irreversible system actions; authority mismatch; unsupported network execution. |
| Flow | Request → DeterministicGuard → (pass) → Plan-Gate → (safe_execute) → SandboxExecutor. |
| Integration | execute_service handlers and LoopController; guard invoked before PlanGateService.evaluate; no new execution surface. |
