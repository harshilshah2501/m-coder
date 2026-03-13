# System E2E Validation

**Report date:** 2026-03-13  
**Canonical state reference:** [SYSTEM_CANONICAL_STATE_AUDIT.md](SYSTEM_CANONICAL_STATE_AUDIT.md)  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## 1. Scope

Audit and document the existence/readiness of E2E scenarios for: REF/CONF/DES paths, allowed/blocked/refused execution, container execution, ledger replay, shadow validation, and plugin/runtime path. Discovery via demo entry points, test discovery, and pytest --collect-only. No fixes; document only.

---

## 2. Scenario Inventory

| Scenario category | Expected | Location / evidence |
|-------------------|----------|----------------------|
| REF path | Refusal, no safe_execute | plan_ref_missing_authority.json, plan_invalid_r2_ref_phase_not_refuse.json; test_emulator_invariants (test_merge_without_approval_ref_refuse, authority_fail_never_safe_execute) |
| CONF path | bounded_allow, no defer | plan_conf_preboundary.json, ledger_conf_preboundary.json; test_commit_prod_change_conf_bounded_allow, boundary_*_never_defer |
| DES path | safe_execute | test_safe_commit_des_safe_execute; demo scenarios |
| Allowed execution | safe_execute → sandbox | demo_governed_execution.py; test_plangate_integration (may_execute_only_safe_execute); test_sandbox_demo_e2e |
| Blocked execution | BLOCKED outcome | ledger_ref_blocked.json; tests for refusal/defer/bounded_allow block sandbox |
| Refused execution | REFUSED outcome | Plan-Gate refusal path; test_plangate_integration, test_emulator_invariants |
| Container execution | Container driver | test_container_sandbox_driver.py; container_sandbox_driver.py (runtime-dependent) |
| Ledger replay | Replay from ledger | runtime/ledger/replay.py; demo_trace.py; test_ledger_completeness |
| Shadow validation | No boundary crossed | test_emulator_invariants (test_shadow_mode_never_crossed); shadow_runner/run_demo.py; baseline_scenarios |
| Plugin/runtime path | Bridge → /v0/plan, /v0/execute | jetbrains-plugin bridge; plan_gate_service; execute_service |

---

## 3. Available Demos / Tests

- **Demos:** `runtime/sandbox/demo_governed_execution.py`, `runtime/shadow_runner/run_demo.py`, `runtime/ledger/demo_trace.py`.
- **Schema examples:** `runtime/schemas/examples/` — plan_*.json (REF, CONF, invalid R1/R2), ledger_*.json (ref_blocked, conf_preboundary, invalid_l4).
- **Tests (collected):** test_emulator_invariants (authority, boundary, PlanGate invariants, scenarios, ledger, hashing, reason codes), test_plangate_integration (decision, integration), test_sandbox_demo_e2e, test_ledger_completeness, test_container_sandbox_driver (container path; may skip if no runtime).

---

## 4. Missing Scenarios

- No missing critical scenario surfaces identified. REF/CONF/DES, allowed/blocked/refused, ledger, and shadow have either demo or test or schema examples. Plugin path is implemented (bridge + execute_service); E2E for plugin is via Gradle tests in jetbrains-plugin.

---

## 5. Environment-Dependent Cases

- **Container sandbox:** `test_container_sandbox_driver.py` and container driver execution require podman or docker. When runtime is absent, driver raises SandboxExecutionError (fail-closed); tests may skip or mock. Documented as expected; not an audit failure.
- **RAG / vLLM:** Not part of governed E2E; optional for full stack.

---

## 6. Pass/Fail Verdict

**PASS.** E2E scenario inventory is present: REF/CONF/DES paths, allowed/blocked/refused execution, ledger replay, and shadow validation have demos, tests, or schema examples. Container execution is present and documented as environment-dependent. Plugin/runtime path exists (bridge + services). No critical E2E scenario missing; skip conditions for container tests documented.
