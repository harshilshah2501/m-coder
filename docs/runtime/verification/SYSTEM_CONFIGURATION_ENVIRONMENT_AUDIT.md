# System Configuration Environment Audit

**Report date:** 2026-03-13  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## Scope

Inspect environment variables, configuration files, and runtime flags used by or documented for the runtime and related services. Verify that governance execution cannot be disabled through configuration (e.g. no “skip Plan-Gate” or “disable sandbox” switch that would allow ungoverned execution).

---

## Surfaces Inspected

- **Execute service:** `runtime/execute_service/handlers.py` (env vars, request fields, client_policy)
- **Shadow schema:** `runtime/shadow/schemas/shadow_session.v0.1.schema.json` (policy, fail_closed_if_gate_unreachable)
- **Orchestrator/budget:** `runtime/orchestrator/budget_policy.py` (BudgetConfig; no governance disable)
- **Config YAML:** `ml/training/artifacts/artifact_store.yaml`, `observation/judge_drift_suite/thresholds.yaml` (artifact/observation only)
- **Grep:** runtime for disable, bypass, skip.*gate, enforcing, os.environ, getenv, config flags that could turn off Plan-Gate or sandbox

---

## Findings

### Execute service (handlers.py)

- **Plan-Gate availability:** If `PlanGateService` is `None` (import failure), the handler returns immediately with outcome `REFUSED`, reason “Plan-Gate service not available; execution path blocked.” No execution path when Plan-Gate is unavailable.
- **Ledger path:** `ledger_path = data.get("ledger_path") or os.environ.get("MOTADATA_EXECUTE_LEDGER_PATH")`. Used only to enable ledger persistence. When `ledger_path` is set and persistence fails, the handler returns `BLOCKED` (fail-closed). No flag to “skip” ledger or Plan-Gate.
- **Request overrides for test/demo:** Docstring states that “only explicit request fields (plan_gate_refuse, plan_gate_defer, plan_gate_bounded_allow) may override for test/demo.” These set the **posture** passed to Plan-Gate (e.g. force refuse/defer/bounded_allow); they do not bypass Plan-Gate or run sandbox without evaluation. Governance evaluation still runs; posture is forced for testing.
- **client_policy:** Taken from request (e.g. for shadow/fail-closed behavior). No key observed that disables Plan-Gate or sandbox enforcement.

**Finding:** No configuration or environment variable in the execute service disables Plan-Gate or allows ungoverned execution. Missing Plan-Gate → REFUSED; ledger path set but persistence failure → BLOCKED.

### Shadow session policy

- **fail_closed_if_gate_unreachable:** Required boolean in shadow session policy. Used to require fail-closed behavior when the gate is unreachable; no option to “disable governance” in shadow.

### Orchestrator / budget

- **BudgetConfig:** Controls iteration/token/time limits and warning thresholds. No flag to disable Plan-Gate, sandbox, or governance.

### Other config files

- **artifact_store.yaml:** Local/S3 artifact backend and credential env var names. No runtime governance flags.
- **thresholds.yaml:** Observation/drift thresholds. No runtime governance flags.

### Grep results (runtime)

- No pattern found that allows disabling Plan-Gate or bypassing the sandbox via configuration. References to “config” are for budget, policy, or test fixtures (e.g. “Plan-Gate not configured” in tests as expected message when service is absent).

---

## Test/demo posture overrides — enforcement status

Request fields `plan_gate_refuse`, `plan_gate_defer`, and `plan_gate_bounded_allow` are **non-production, test/demo-only** posture overrides. They force Plan-Gate outcome (refuse/defer/bounded_allow); they do not bypass Plan-Gate or run sandbox without evaluation. There is **no config or environment variable** that restricts these fields to a test mode or disables them in production. The runtime accepts them from any client; restriction to test/demo is **documented only** (handlers docstring, schema descriptions, bridge doc). Enforcement is **not implemented**—reliance is on client contract and deployment.

---

## Risks

1. **Test/demo overrides:** Request fields `plan_gate_refuse`, `plan_gate_defer`, `plan_gate_bounded_allow` force a posture. If a client (e.g. plugin or test) were misused in production with these set, behavior would still be “refuse/defer/bounded_allow” (no sandbox execution for defer/bounded_allow in MVP). Risk is misuse in production, not a back-door disable of governance; recommend restricting these to test/demo environments or authenticated test endpoints.
2. **MOTADATA_EXECUTE_LEDGER_PATH:** Only affects where ledger is written; does not disable governance.

---

## Verdict

**PASS.** No configuration or environment variable was found that disables Plan-Gate or allows ungoverned execution. Plan-Gate unavailable → REFUSED; ledger path set and persistence failure → BLOCKED. Overrides in the request are posture overrides for test/demo and do not skip governance evaluation or sandbox enforcement. Governance execution cannot be turned off through the inspected configuration or environment.
