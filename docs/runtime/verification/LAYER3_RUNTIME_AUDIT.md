# Layer-3 Runtime Audit

**Report date:** 2026-03-13  
**Canonical state reference:** [SYSTEM_CANONICAL_STATE_AUDIT.md](SYSTEM_CANONICAL_STATE_AUDIT.md)  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## 1. Scope

Audit runtime execution chain (Orchestrator → Executor → Driver → Backend), sandbox driver abstraction, container driver, ledger/replay and shadow surfaces, plugin bridge, and the four required invariants: (1) no runtime bypass, (2) fail-closed behavior, (3) governance boundary (drivers do not emit ledger / implement governance), (4) shadow isolation. Include attack-surface scan for risky patterns.

---

## 2. Runtime Surfaces Inspected

- **Orchestrator:** `runtime/orchestrator/` (LoopController, transition_executor, budget_policy, stop_conditions, replay).
- **Plan-Gate:** `runtime/plangate/`, `runtime/plan_gate_service/`, `runtime/plan_gate_stub/`.
- **Sandbox:** `runtime/sandbox/` — sandbox_executor.py, sandbox_driver.py, container_sandbox_driver.py, sandbox_runner.py, sandbox_ledger*, sandbox_policy, sandbox_result.
- **Ledger:** `runtime/ledger/` (emitter, store, replay, contracts).
- **Shadow:** `runtime/shadow/`, `runtime/shadow_runner/`.
- **Execute service:** `runtime/execute_service/handlers.py`.
- **IDE:** `runtime/ide/schemas`, plugin bridge (jetbrains-plugin).

---

## 3. Execution Chain Findings

- **LoopController** uses **SandboxExecutor** (injectable); calls `sandbox_executor.execute_sandbox_action(action)` for PROPOSAL_VALIDATED → SANDBOX_EXECUTED (see loop_controller.py).
- **SandboxExecutor** holds a **SandboxDriver** (protocol); default `LocalProcessSandboxDriver(policy)`; calls `self._driver.run(...)` for execution. Ledger emission and GovernedExecutionResult construction are in executor only.
- **LocalProcessSandboxDriver** (sandbox_driver.py) delegates to **SandboxRunner** for run(); **SandboxRunner** and **ContainerSandboxDriver** use `subprocess.run()` for actual execution.
- **execute_service** builds SandboxExecutor (with optional ledger_store), builds SandboxAction, calls `executor.execute_sandbox_action(action)`. No direct subprocess in handlers; execution only via executor/driver.

**Conclusion:** Single execution path: Orchestrator/execute_service → SandboxExecutor → SandboxDriver (LocalProcess or Container) → subprocess (in runner or container driver). No bypass.

---

## 4. Four-Invariant Audit

### Invariant 1 — No runtime bypass

- **subprocess:** Found in `runtime/sandbox/container_sandbox_driver.py`, `runtime/sandbox/sandbox_runner.py` (governed execution path); in `archive/legacy_runtime_rag/` (tests, compiler_tool, rag_api, performance_monitor) and in `runtime/plan_gate_stub/tests`, `runtime/plan_gate_service/tests`, `runtime/ci_gate/tests` (CLI/service tests). Governed user command execution flows only through sandbox drivers; RAG and tests use subprocess for tooling/CLI, not for Plan-Gate–governed execution.
- **os.system:** Not found in runtime/. **Verdict:** Invariant holds; execution only in sandbox driver (and test/utility code outside governed path).

### Invariant 2 — Fail-closed behavior

- **SandboxPolicyViolation / SandboxExecutionError / SandboxTimeout:** Raised by drivers and sandbox_runner; SandboxExecutor catches SandboxPolicyViolation and returns GovernedExecutionResult (blocked); SandboxExecutionError/SandboxTimeout propagate or are converted to failed result, not swallowed.
- **Silent swallow:** One `except Exception: pass` in `runtime/orchestrator/transition_executor.py` (line 349) for post-hooks ("Post-hooks should not fail the transition"). This does not swallow policy/timeout/execution errors from the sandbox path; it only suppresses post-hook failures. **Risk:** If a post-hook were to perform critical work, its failure would be hidden; current design documents this as intentional. Other `except Exception` blocks in execute_service/handlers and loop_controller set ledger_store to None or return None, and handlers then enforce BLOCKED (fail-closed) when ledger_path was set. **Verdict:** Fail-closed preserved; one deliberate post-hook swallow documented.

### Invariant 3 — Governance boundary (drivers do not emit ledger; executor owns governance)

- **ledger.append / emit_ledger / GovernedExecutionResult** in `runtime/sandbox/`: Present only in `sandbox_executor.py`, `sandbox_result.py`, and `__init__.py`. **Not** in `sandbox_driver.py` or `container_sandbox_driver.py`. Drivers return SandboxResult; executor constructs GovernedExecutionResult and uses ledger_emitter/ledger_store. **Verdict:** Invariant holds.

### Invariant 4 — Shadow isolation

- **sandbox_executor / execute_sandbox_action / SandboxExecutor** in `runtime/shadow/` and `runtime/shadow_runner/`: No matches. Shadow code does not call sandbox executor directly. **Verdict:** Invariant holds; shadow does not cross irreversible boundary via executor.

---

## 5. Attack Surface Scan

Searched for: `subprocess`, `os.system`, `eval(`, `exec(`, `pickle.load`, `yaml.load`, `except Exception: pass` (or equivalent).

### Expected findings

| Pattern | Location | Classification | Notes |
|--------|----------|----------------|--------|
| subprocess | runtime/sandbox/container_sandbox_driver.py | Expected | Governed container execution path. |
| subprocess | runtime/sandbox/sandbox_runner.py | Expected | Governed local process execution path. |
| subprocess | runtime/tests/test_container_sandbox_driver.py | Expected | Mocking driver subprocess. |
| subprocess | runtime/plan_gate_stub/tests, plan_gate_service/tests, ci_gate/tests | Expected | CLI/service tests. |
| subprocess | runtime/execute_service/handlers.py | Expected | Comment only ("suitable for subprocess"); no direct call. |
| .eval() | archive/legacy_runtime_rag/src/api/rag_api.py (embed_model.eval()) | Expected | PyTorch eval mode, not Python eval(). |
| except Exception: pass | runtime/orchestrator/transition_executor.py:349 | Expected | Post-hooks; documented as "should not fail the transition". |
| except Exception (decode fallback) | runtime/sandbox/sandbox_runner.py:220,225 | Expected | Decode errors for stdout/stderr; not execution errors. |

### Suspicious findings / needs review

| Pattern | Location | Classification | Notes |
|--------|----------|----------------|--------|
| subprocess | archive/legacy_runtime_rag/src/utils/compiler_tool.py | Needs review | Runs compiler; not part of Plan-Gate sandbox. Ensure not used for user-supplied command execution. |
| subprocess | archive/legacy_runtime_rag/src/api/rag_api.py (execute_tool, check_syntax) | Needs review | RAG API tool execution; verify this is not the same as governed execute path or is clearly out-of-band. |

### Risk classification

- **Unsafe dynamic execution (eval/exec/pickle.load/yaml.load):** No occurrences in runtime/ (only embed_model.eval() which is PyTorch). **No finding.**
- **Silent failure swallowing:** One intentional `except Exception: pass` in transition_executor (post-hooks). No silent swallow of SandboxPolicyViolation, SandboxExecutionError, or SandboxTimeout in governed path.
- **Execution outside sandbox boundaries:** Governed execution is confined to SandboxExecutor → SandboxDriver. RAG subprocess use is for tooling/compiler/API; not the same as the /v0/execute governed path. **Recommendation:** Document RAG execute_tool/compiler_tool as non-governed tooling so future audits can confirm they are not exposed as Plan-Gate execution.

---

## 6. Risks

- **RAG subprocess usage:** `archive/legacy_runtime_rag/` uses subprocess for compiler and API tools. These are outside the Plan-Gate/sandbox execution chain; ensure they are never used to execute user-supplied commands in a governed context without going through SandboxExecutor.
- **Post-hook exception pass:** transition_executor.py line 349; acceptable per design but any critical post-hook logic would not fail the transition.

---

## 7. Pass/Fail Verdict

**PASS.** Execution chain is Orchestrator/execute_service → SandboxExecutor → SandboxDriver → Backend (subprocess only in sandbox drivers/runner and container driver). All four invariants hold: no bypass, fail-closed preserved, drivers do not emit ledger or build GovernedExecutionResult, shadow does not call sandbox executor. Attack surface scan: no unsafe eval/exec/pickle/yaml; subprocess confined to sandbox path and to RAG/tests (documented); one intentional except-pass in post-hooks. No violations that require failing the audit.

---

## 8. Shadow Impact Review (process checklist)

When changing decision, result, ledger, or shadow semantics (or before merging such changes), confirm:

- [ ] **Decision semantics changed?** If Plan-Gate postures or decision contract changed, shadow harness and baseline scenarios still align (no unintended boundary_crossed).
- [ ] **Result schema changed?** If GovernedExecutionResult or execute response schema changed, plugin and shadow consumers are updated; replay fixtures still valid.
- [ ] **Sandbox semantics changed?** If sandbox policy, allowlist, or driver behavior changed, shadow does not rely on executing through sandbox; baseline scenarios remain validation-only.
- [ ] **Ledger semantics changed?** If ledger event types or row shape changed, shadow ingestion/replay and replay fixtures are updated; append-only and join contract preserved.
- [ ] **Shadow baseline updated?** If new scenarios or invariants (e.g. S-1, S-2) were added, `runtime/shadow/` baseline scenarios and docs/runtime/shadow/* are updated.
- [ ] **Replay fixtures updated?** If ledger replay or plan/ledger examples changed, `runtime/schemas/examples/`, ledger demos, and any replay test fixtures are updated.
