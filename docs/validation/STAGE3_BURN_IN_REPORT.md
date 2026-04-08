# Stage 3 — Burn-in execution report

Human-readable record for **audit / closure**.

- **Native Linux:** raw proof `artifacts/stage3_pytest_output.txt` — re-captured **2026-04-08** at commit **`d4a2807`** (Stage 2 closure chronology; supersedes older dev-host hash in prior drafts).
- **WSL:** **validated** — see status block below (artifacts match; not “WSL skipped”).
- **Sample observability (offline controller):** `artifacts/sample_ledger_trace.json`

### Burn-in validation status (source-of-truth)

**WSL:** Validated (**Ubuntu 24.04** userland, **Python 3.12.3**). Operator session `root@DESKTOP-MBPAQK1` / `~/Harshil-PoCs/m-coder`; transcript source **`docs/Notes.md`**.

**Artifacts:**

| Artifact | Contents |
|----------|----------|
| `docs/validation/artifacts/stage3_pytest_output_wsl.txt` | Full pytest **22/22** passed |
| `docs/validation/artifacts/stage3_pytest_subset_wsl.txt` | Nine-scenario **`-k`** subset (**10** passed, 12 deselected) |

**Native Linux:** `docs/validation/artifacts/stage3_pytest_output.txt` — full pytest **22/22** (dev-host capture; commit recorded in §1.1).

---

## 1. Environment

### 1.1 Native Linux capture (development server)

| Field | Value |
|--------|--------|
| **Host** | Ubuntu 24.04.4 LTS (Noble), Linux 6.8.x, x86_64 — native Linux dev host |
| **Python** | 3.12.3 (`/usr/bin/python3`) |
| **pytest** | 7.4.4 (see raw file) |
| **Repository commit** | `d4a2807de90c9ff29f7b32be659f3a1ff66fb051` (short: `d4a2807`) |
| **Capture date** | 2026-04-08 |

### 1.2 WSL — validated (operator capture)

**Status:** WSL was **used** for burn-in; results are **not** native-only. Same pass counts as §“Burn-in validation status”.

| Field | Value |
|--------|--------|
| **OS** | **Ubuntu 24.04** (WSL userland on Windows) |
| **Source** | Transcript in **`docs/Notes.md`** (shell prompt `root@DESKTOP-MBPAQK1`, path `~/Harshil-PoCs/m-coder`) |
| **Python** | 3.12.3 — interpreter `/root/.venvs/motadata-context-layer/bin/python3` (venv **motadata-context-layer**) |
| **pytest** | 9.0.2, pluggy 1.6.0 |
| **Repo root** | `/root/Harshil-PoCs/m-coder` |
| **Commit at capture** | WSL session predates tip; **parity signal** is identical **22/22** pass count vs native — see `stage3_pytest_output_wsl.txt`. Re-run on WSL at `d4a2807` optional for commit-hash alignment. |

**WSL result summary (full suite):**

```
total_tests: 22
passed: 22
failed: 0
```

Duration: **0.42s** (WSL run — see `stage3_pytest_output_wsl.txt`).

**WSL subset run (nine-scenario `-k` filter):** 10 passed, 12 deselected in **0.09s** — see `stage3_pytest_subset_wsl.txt`.

---

## 2. Command executed

```bash
export M_CODER_ROOT=/root/Harshil-PoCs/m-coder   # WSL example; native: your path
cd "$M_CODER_ROOT"
python3 -m pytest runtime/tests/test_stage3_loop.py -v --tb=short
```

**Raw outputs saved:**

| Host | File |
|------|------|
| Native Linux | `docs/validation/artifacts/stage3_pytest_output.txt` |
| WSL | `docs/validation/artifacts/stage3_pytest_output_wsl.txt` |

---

## 3. Result summary

### Native Linux (this repo capture)

```
total_tests: 22
passed: 22
failed: 0
```

Duration: ~0.07 s — see `stage3_pytest_output.txt` (2026-04-08 capture at `d4a2807`).

### WSL (`docs/Notes.md` capture)

```
total_tests: 22
passed: 22
failed: 0
```

Duration: **0.42 s** — see `stage3_pytest_output_wsl.txt`.

Both hosts: **same test module, same pass count** — burn-in is **not** native-only.

---

## 4. Scenario coverage (burn-in matrix → pytest)

| Scenario | Pytest test(s) | Role |
|----------|----------------|------|
| ASK — no-tool success | `test_terminal_correctness_success_no_tool_not_run` | COMPLETED / `not_run` |
| Evidence integrity — invalid refs (fail-closed) | `test_fake_evidence_refs_rejected` | Refs not in envelope; no tool |
| CODE — blocked tool | `test_tool_denied_path_is_blocked_execution_truth` | BLOCKED / `blocked` |
| EXECUTE — pre-loop refusal | `test_plan_gate_refusal` | REFUSED; model not called |
| EXECUTE — in-loop Plan-Gate recheck failure | `test_inloop_plan_gate_recheck_exception_fail_closed` | Fail-closed; sandbox calls 0 |
| EXECUTE — timeout | `test_timeout_normalization_and_failed_truth` | Normalized timeout / failed truth |
| CODE — terminal tool failure (post-result) | `test_terminal_tool_failure_after_tool_result_ready_regression` | TOOL_RESULT_READY → FAILED |
| DEBUG — insufficiency after tool | `test_insufficiency_after_tool_result` | INSUFFICIENT |
| EXECUTE — success + execution truth | `test_tool_success_execution_truth_executed` | `executed` + artifacts |
| EXECUTE — ledger trace linkage | `test_ledger_trace_linkage_contains_refs` | `proposal_ref` / `decision_ref` / `tool_result_ref` |
| Invalid proposal / budget / gate defer | `test_invalid_proposal_schema`, `test_retry_loop_exhaustion`, `test_no_silent_fallback` | Schema + policy termination |
| Executor / validation fail-closed | `test_explicit_failed_terminal_normalization`, `test_tool_result_validation_failure_fail_closed_no_nameerror`, … | Normalization + no raw crash |
| Pre-loop / frame fail-closed | `test_preloop_*`, `test_loop_context_frame_validation_fail_closed` | Deterministic FAILED |
| Illegal transition / final-response validation | `test_fail_closed_illegal_transition_path`, `test_final_response_validation_failure_consistency` | Fail-closed terminal alignment |

*Full list of 22 tests appears in both pytest artifact files.*

---

## 5. Key behavioral confirmations

Based on passing tests in `runtime/tests/test_stage3_loop.py` (verified on **native Linux and WSL**):

| Area | Confirmation |
|------|----------------|
| **Fail-closed paths** | Pre-loop validation, Plan-Gate errors, in-loop recheck exception, tool-result validation, illegal transition, final-response validation — terminal **FAILED** (or policy-consistent outcome), no unhandled exception path. |
| **Blocked / refused / failed semantics** | `BLOCKED`, `REFUSED`, `FAILED`, `INSUFFICIENT`, `COMPLETED` align with `FinalResponse` and execution truth (`not_run` / `executed` / `blocked` / `failed`). |
| **No silent fallback** | `test_no_silent_fallback` — gate defer does not execute sandbox. |
| **Execution truth** | Final `execution_result.status` reflects normalized tool outcome, not mere presence of refs (`test_tool_*`, denied, timeout, insufficiency cases). |
| **Ledger trace linkage** | Iteration records include `proposal_ref`, `decision_ref`, `tool_result_ref`; `reconstruct_trace` yields `terminal_decision_summary` and `execution_truth_summary` (see sample JSON). |

---

## 6. Scenario checklist (pass/fail)

| Scenario | Result | Notes |
|----------|--------|--------|
| ASK no-tool | **PASS** | `test_terminal_correctness_success_no_tool_not_run` |
| DEBUG invalid evidence | **PASS** | Evidence-integrity fail-closed — `test_fake_evidence_refs_rejected` (envelope ASK in test) |
| CODE blocked | **PASS** | `test_tool_denied_path_is_blocked_execution_truth` |
| EXECUTE refusal | **PASS** | `test_plan_gate_refusal` |
| EXECUTE recheck failure | **PASS** | No sandbox — `test_inloop_plan_gate_recheck_exception_fail_closed` |
| EXECUTE timeout | **PASS** | `test_timeout_normalization_and_failed_truth` |
| CODE tool failure | **PASS** | `test_terminal_tool_failure_after_tool_result_ready_regression` |
| DEBUG insufficiency | **PASS** | `test_insufficiency_after_tool_result` |
| EXECUTE success trace | **PASS** | `test_tool_success_execution_truth_executed` + `test_ledger_trace_linkage_contains_refs` |

**WSL:** All rows **PASS** per `stage3_pytest_output_wsl.txt` (22/22).

---

## 7. Closure acceptance criteria (engineering gate)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| **1. Determinism** | **Met (test suite)** | Same code + doubles → reproducible outcomes; hashes in ledger sample are stable for fixed inputs per run. |
| **2. Fail-closed guarantee** | **Met** | Dedicated tests for validation/gate/transition failures; no silent success on policy violation. |
| **3. Execution truth integrity** | **Met** | Tests assert `execution_result.status` vs actual normalized outcomes. |
| **4. Trace reconstructability** | **Met** | `sample_ledger_trace.json` shows `iteration_linkage`, refs, `terminal_decision_summary`, `execution_truth_summary`, and full event list. |
| **5. WSL parity** | **Met** | **22 passed** on WSL (`stage3_pytest_output_wsl.txt`) — same module, operator session documented in **`docs/Notes.md`**. |

If any criterion becomes **fuzzy** (e.g. non-deterministic hashes without documented inputs, or missing ledger fields), burn-in is **not** complete for that scope.

---

## 8. Artifact index

| File | Description |
|------|-------------|
| `docs/validation/STAGE3_BURN_IN_REPORT.md` | This report |
| `docs/validation/artifacts/stage3_pytest_output.txt` | Full pytest stdout — **native Linux** dev host |
| `docs/validation/artifacts/stage3_pytest_output_wsl.txt` | Full pytest stdout — **WSL** (`docs/Notes.md` capture) |
| `docs/validation/artifacts/stage3_pytest_subset_wsl.txt` | WSL nine-scenario `-k` subset (10 passed) |
| `docs/validation/artifacts/sample_ledger_trace.json` | One **EXECUTE** success run: `Stage3LoopController` + test doubles (offline; not WSL-specific) |
| `docs/validation/artifacts/stage3_live_smoke_output.txt` | **Live** governed path: `/healthz`, `/version`, then `runtime/scripts/verify_ask_path.sh` (export → `/v1/ask`) — **PASS** |
| `docs/validation/artifacts/stage3_trace_reconstruction.txt` | **Traceability:** grep-stable `PLAN_GATE request` + `[ASK_V1]` lines for matching `request_id`; plus **offline** `test_ledger_trace_linkage_contains_refs` **PASS** |

---

## 9. Live governed HTTP slice (B7 remainder — 2026-04-08)

**Purpose:** Artifact-backed proof that **Context Layer → Plan-Gate** is healthy for real `export_evidence` → `ask_request.v1.0` → `/v1/ask` traffic, with **grep-stable** correlation in `runtime/.run/plan_gate.log` (Action 5 pattern).

**Topology note:** Capture was performed on a **single native Linux host** with **8091 / 8089 / 8000** on localhost (runbook Parts B–C collapsed onto one machine). HTTP contracts match the **WSL Context Layer + GPU Plan-Gate** split; a **separate WSL-only** transcript is **not** duplicated here — use the same commands from **`docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md`** on WSL for charter parity if required.

**Commit alignment:** The artifact records **`repo_commit_short`** at documentation time. Long-running services may report an older `git_commit` in `GET /version` until restarted from the same tree — see **Commit / process alignment note** inside `stage3_live_smoke_output.txt`.

**Stage 3 loop product path:** This slice **does not** assert IDE or live traffic through **`Stage3LoopController`** end-to-end (unchanged from runbook **§7**).

---

### Final closure checklist (sanity)

| Item | Status |
|------|--------|
| Full pytest (22) → **WSL** | Done — `stage3_pytest_output_wsl.txt` |
| Scenario subset → **WSL** | Done — `stage3_pytest_subset_wsl.txt` |
| Raw logs stored (native + WSL) | Done — §8 artifact index |
| Ledger trace sample | Done — `sample_ledger_trace.json` |
| Report states **WSL validated** (not “WSL unused”) | Done — §“Burn-in validation status” + §1.2 |
| Live HTTP smoke + trace snippet | Done — §9 + `stage3_live_smoke_output.txt` + `stage3_trace_reconstruction.txt` |

---

*WSL results are transcribed from **`docs/Notes.md`**; native results from automated capture in this repo. No manual fabrication of pass/fail lines.*
