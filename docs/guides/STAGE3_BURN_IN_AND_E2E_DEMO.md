# Stage 3 — Burn-in validation (WSL) and WSL → GPU end-to-end demo

**Status:** Stage 3 runtime loop implementation is **accepted for burn-in** (deterministic pytest coverage). This document gives **exact commands** for local validation and for the **governed vertical slice** (WSL evidence → GPU Plan-Gate + vLLM → sandbox / spool), without implying the IDE yet calls `Stage3LoopController` directly (that integration is a separate wiring step).

---

## 1. Machine roles and paths

| Role | Host | `M_CODER_ROOT` | Product repo (`MOTADATA_ROOT` / workspace) |
|------|------|----------------|--------------------------------------------|
| **GPU dev server** (RTX 6000 — Plan-Gate + vLLM) | This Linux machine | `/home/harshil/Harshil-PoCs/m-coder` | `/home/harshil/Projects/Motadata` (reference for scenarios) |
| **WSL** (Context Layer + burn-in) | Ubuntu 24.04 on Windows | `/root/Harshil-PoCs/m-coder` | `/home/harshil/Projects/Motadata` (JetBrains WSL backend) |

Adjust usernames if your WSL user is not `root`; keep **`MOTADATA_ROOT`** pointing at the **same Motadata clone** the IDE indexes.

---

## 2. Part A — Burn-in from WSL (Stage 3 pytest)

**Purpose:** Reproduce the **22** Stage 3 scenarios under pressure (CI parity on your laptop/WSL).

**Prerequisites**

- Python **3.9+** (3.11/3.12 typical).
- Repo synced with GPU branch (same commit as RTX server when comparing results).

**Commands (WSL)**

```bash
export M_CODER_ROOT=/root/Harshil-PoCs/m-coder
cd "$M_CODER_ROOT"
python3 -m pytest runtime/tests/test_stage3_loop.py -v --tb=short
```

**Expected:** `22 passed` (0 failed).

### 2.1 Scenario → test mapping (targeted runs)

Use these when you want **one scenario at a time** (`-k` matches test name substrings).

| Burn-in scenario | Pytest filter (example) | What it proves |
|------------------|---------------------------|----------------|
| **ASK — no-tool success** | `-k terminal_correctness_success_no_tool_not_run` | `COMPLETED`, `execution_result.status == not_run` |
| **DEBUG — fake / invalid evidence refs** | `-k fake_evidence_refs_rejected` | Evidence integrity fails closed; no sandbox run (test envelope defaults to **ASK**; ref validation is what matters) |
| **CODE — blocked tool path** | `-k tool_denied_path_is_blocked` | `BLOCKED`, `execution_result.status == blocked` |
| **EXECUTE — pre-loop refusal** | `-k plan_gate_refusal` | `REFUSED` before model; `not_run` |
| **EXECUTE — in-loop Plan-Gate recheck failure** | `-k inloop_plan_gate_recheck_exception` | Fail-closed `inloop_plan_gate_failed`; **sandbox calls == 0** |
| **EXECUTE — timeout normalization** | `-k timeout_normalization_and_failed` | `failed` + `tool_timeout` in reason chain |
| **CODE — terminal tool failure (post-result)** | `-k terminal_tool_failure_after_tool_result_ready` | Legal transition from `TOOL_RESULT_READY` → `FAILED` |
| **DEBUG — insufficiency after tool** | `-k insufficiency_after_tool_result` | `INSUFFICIENT` from structured partial/insufficient tool outcome |
| **EXECUTE — success + trace reconstruction** | `-k "tool_success_execution_truth_executed or ledger_trace_linkage_contains_refs"` | `executed` + per-iteration `proposal_ref` / `decision_ref` / `tool_result_ref` |

**Single combined burn-in command (nine scenarios above)**

```bash
python3 -m pytest runtime/tests/test_stage3_loop.py -v --tb=short \
  -k "terminal_correctness_success_no_tool_not_run or fake_evidence_refs_rejected or tool_denied_path_is_blocked or plan_gate_refusal or inloop_plan_gate_recheck_exception_fail_closed or timeout_normalization_and_failed_truth or terminal_tool_failure_after_tool_result_ready_regression or insufficiency_after_tool_result or tool_success_execution_truth_executed or ledger_trace_linkage_contains_refs"
```

Expect **10 passed** from that filter (subset of the full 22).

---

## 3. Part B — GPU (RTX server): Plan-Gate + vLLM

**Purpose:** Bring up the **governed stack** used by Ask / plugin flows: Plan-Gate on **8089**, vLLM on **8000** (defaults).

**On the GPU machine**

```bash
export M_CODER_ROOT=/home/harshil/Harshil-PoCs/m-coder
cd "$M_CODER_ROOT"
# One-time: copy and edit runtime/config/demo_stack.env from demo_stack.env.example — set VLLM_BASE_MODEL
./runtime/scripts/governed_services.sh start
./runtime/scripts/governed_services.sh status
```

**Health checks (GPU localhost)**

```bash
curl -sS http://127.0.0.1:8089/healthz
curl -sS http://127.0.0.1:8089/version
# If vLLM is up:
curl -sS http://127.0.0.1:8000/v1/models || true
```

**Plan-Gate alone (minimal, no launcher)**

```bash
cd "$M_CODER_ROOT"
PLAN_GATE_PORT=8089 PLAN_GATE_SPOOL_DIR=/tmp/plan_gate_spool python3 -m runtime.plan_gate_service.app
```

Spool / artifacts: see `runtime/plan_gate_service/README.md` (`plan.json`, `decision_response.json`, `ledger_row.json`, etc.).

---

## 4. Part C — WSL: Context Layer (evidence truth)

**Purpose:** Workspace-local **Layer-5 evidence** (`layer5.evidence_bundle.v1`) via HTTP **8091** — no GPU repo reads.

**Install + run (from repo)**

```bash
export M_CODER_ROOT=/root/Harshil-PoCs/m-coder
cd "$M_CODER_ROOT/packaging/motadata-context-layer"
python3 -m venv .venv && . .venv/bin/activate
pip install .
export MOTADATA_ROOT=/home/harshil/Projects/Motadata
motadata-context-layer
# or: python -m runtime.context_layer_service
```

**Verify**

```bash
curl -sS http://127.0.0.1:8091/healthz
curl -sS http://127.0.0.1:8091/version
```

**Optional packaged pipeline (build + health + export sanity)**

```bash
cd "$M_CODER_ROOT"
WORKSPACE_ROOT=/home/harshil/Projects/Motadata \
PLAN_GATE_URL=http://127.0.0.1:8089 \
bash packaging/motadata-context-layer/build_and_verify_wsl_context_layer.sh
```

Details: `packaging/motadata-context-layer/README.md`, `docs/runtime/WSL_CONTEXT_LAYER_CLIENT.md`.

---

## 5. Part D — WSL → GPU networking (plugin / IDE)

The JetBrains plugin talks to **Plan-Gate** at a configurable base URL (default `http://127.0.0.1:8089`). Context Layer stays on **WSL `127.0.0.1:8091`**.

**Typical pattern:** run Plan-Gate (+ vLLM) on the **GPU host**, then from **Windows** open an SSH local forward so the IDE sees Plan-Gate on localhost:

```powershell
ssh -N -L 8089:127.0.0.1:8089 -L 8000:127.0.0.1:8000 <user>@<gpu-host>
```

Leave the session open. Then on Windows:

```powershell
curl.exe http://127.0.0.1:8089/healthz
```

**IDE / JVM options** (see `jetbrains-plugin/.../MotadataRuntimeConfig.kt`):

- `-Dmotadata.plan_gate.url=http://127.0.0.1:8089` or env `MOTADATA_PLAN_GATE_URL`
- Context Layer: `-Dmotadata.context_layer.url=http://127.0.0.1:8091` (WSL port forwarded if needed, or native WSL localhost from plugin depending on your setup)

Extended walkthrough: `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md`.

---

## 6. Part E — End-to-end checklist (governed slice)

Use this as a **manual demo script** after Parts B–D are green.

| Step | Where | Action | Pass criterion |
|------|--------|--------|----------------|
| 1 | GPU | `governed_services.sh status` | Plan-Gate **8089** and vLLM **8000** respond |
| 2 | WSL | Context Layer **8091** | `/healthz` OK |
| 3 | Windows | SSH tunnel to GPU | `curl` to `127.0.0.1:8089/healthz` OK |
| 4 | IDE | Open `MOTADATA_ROOT`, trigger **Ask** or flow that hits Plan-Gate | No connection errors; spool or logs show `request_id` |
| 5 | GPU | Inspect `PLAN_GATE_SPOOL_DIR` (or default `.spool/plan_gate`) | `plan.json` / `decision_response.json` for the run |
| 6 | WSL | `export_evidence` log line **`CONTEXT_LAYER export_evidence begin`** | Confirms evidence path, not a stale 8091 listener |

**vLLM / Explain:** Plan-Gate can health-check vLLM when `MOTADATA_EXPLAIN_VLLM_URL` is set (see `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md`).

---

## 7. Relationship to Stage 3 `Stage3LoopController`

- **Burn-in (Part A)** validates the **Python** loop: state machine, schemas, decision engine, tool executor normalization, ledger trace reconstruction — **fully offline** with test doubles.
- **Parts B–E** validate the **existing product vertical**: Context Layer → Plan-Gate → Ask/Execute services → vLLM, as wired today.
- Wiring **production** traffic so a single user request flows through **real** evidence, **real** Plan-Gate, **real** vLLM, **real** sandbox, and **`Stage3LoopController`** is a **follow-on integration** task; use this doc to keep **environment variables, ports, and health commands** identical across WSL and GPU while that wiring lands.

---

## 8. Quick reference — ports

| Service | Default port | Host in demo |
|---------|--------------|----------------|
| Context Layer | 8091 | WSL |
| Plan-Gate | 8089 | GPU (tunneled to Windows localhost) |
| vLLM | 8000 | GPU (tunneled if IDE or tools need it) |

---

## 9. Semantic note (non-blocking)

`DecisionEngine` may still encode **tool denial** as a `TERMINATE_FAILED`-class decision internally; the **controller** maps that to **blocked** terminal semantics. That indirection is **documented in code/tests** and is **not** a burn-in blocker.
