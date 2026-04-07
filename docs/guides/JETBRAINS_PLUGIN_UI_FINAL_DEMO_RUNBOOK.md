# <u>JetBrains Plugin UI Final Demo Runbook</u>

**Purpose:** run a final, truthful plugin demo where UI output is certified against backend truth.

<u>Environment values fixed for this runbook</u>:

- MOTADATA_ROOT=/home/harshil/Projects/Motadata
- TUNNEL_TARGET=harshil@45.195.82.10

<u>Plugin package for install from disk</u>:

- jetbrains-plugin/build/distributions/motadata-jetbrains-plugin-0.2.7.zip

## <u>1) Outcome Target</u>

**Goal:** define the single pass/fail bar for demo readiness.

A demo is accepted only if plugin-visible behavior matches backend truth for all scenario classes:

- Ask path visibility (v0, v1, explain/debug, fallback)
- Evidence and insufficiency visibility
- plan_summary.notes visibility
- Honest empty/no-match behavior
- Execute outcome truthfulness (executed, blocked, refused, executed_failed)
- Explicit fallback visibility

## <u>2) Terminal Setup (WSL)</u>

**Goal:** bring up WSL services and tunnel with strict compatibility checks.

**Command (Terminal A):**

```bash
cd /home/harshil/Harshil-PoCs/m-coder

export MOTADATA_ROOT=/home/harshil/Projects/Motadata
export M_CODER_REPO_ROOT=/home/harshil/Harshil-PoCs/m-coder
export ENABLE_SSH_TUNNEL=1
export TUNNEL_TARGET=harshil@45.195.82.10
export PLAN_GATE_URL=http://127.0.0.1:8089
export CONTEXT_URL=http://127.0.0.1:8091
export AUTO_ALIGN_CONTEXT_COMMIT=1
export CONTEXT_PORT_RECLAIM=1

./scripts/wsl_plugin_mvp_stack.sh up
```

**Expected:**

- tunnel up to GPU host
- Context Layer started on WSL
- health checks pass
- version and compatibility checks pass

**Command (pre-IDE explicit check):**

```bash
cd /home/harshil/Harshil-PoCs/m-coder

export MOTADATA_ROOT=/home/harshil/Projects/Motadata
export M_CODER_REPO_ROOT=/home/harshil/Harshil-PoCs/m-coder
export ENABLE_SSH_TUNNEL=1
export TUNNEL_TARGET=harshil@45.195.82.10
export AUTO_ALIGN_CONTEXT_COMMIT=1
export CONTEXT_PORT_RECLAIM=1

./scripts/wsl_plugin_mvp_stack.sh check
```

If commit mismatch still appears, force clean re-alignment:

```bash
cd /home/harshil/Harshil-PoCs/m-coder

./scripts/wsl_plugin_mvp_stack.sh down

M_CODER_REPO_ROOT=/home/harshil/Harshil-PoCs/m-coder \
MOTADATA_ROOT=/home/harshil/Projects/Motadata \
ENABLE_SSH_TUNNEL=1 \
TUNNEL_TARGET=harshil@45.195.82.10 \
AUTO_ALIGN_CONTEXT_COMMIT=1 \
CONTEXT_PORT_RECLAIM=1 \
./scripts/wsl_plugin_mvp_stack.sh up
```

## <u>3) JetBrains Plugin Launch Config</u>

**Goal:** ensure plugin uses the exact runtime endpoints and evidence-first mode.

**Command/UI steps (plugin install in IntelliJ IDEA):**

1. Settings -> Plugins
2. Gear icon -> Install Plugin from Disk...
3. Select: jetbrains-plugin/build/distributions/motadata-jetbrains-plugin-0.2.7.zip

**Command (runtime URL + flags in plugin host context):**

- MOTADATA_PLAN_GATE_URL=http://127.0.0.1:8089
- MOTADATA_CONTEXT_LAYER_URL=http://127.0.0.1:8091
- MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1

*Optional strict startup toggle:*

- motadata.startup.stack.check.enabled=true

**Recommended VM options for deterministic demo runs**:

-Dmotadata.plan_gate.url=http://127.0.0.1:8089
-Dmotadata.context_layer.url=http://127.0.0.1:8091
-Dmotadata.ask.evidence_first=true

**Expected (on project load):**

- Motadata Stack Check: OK
- Motadata Stack Check: WARN
- Motadata Stack Check: FAIL

**Do not continue demo if FAIL** unless the scenario intentionally demonstrates failure handling.

Note for strict provenance checks:
- If you require Context Layer to publish `git_commit` in `/version` for every run, use `REQUIRE_CONTEXT_GIT_COMMIT=1` during `check`.

## <u>4) Generate Backend Truth Pack (WSL)</u>

**Goal:** generate backend-truth artifacts used as the authoritative UI parity baseline.

**Command (Terminal B):**

```bash
cd /home/harshil/Harshil-PoCs/m-coder

./scripts/plugin_ui_truth_cert.py \
  --workspace-root /home/harshil/Projects/Motadata \
  --out-dir docs/validation/artifacts/plugin_ui_truth_final_demo
```

**Expected artifacts:**

- preflight.json
- run.log
- log_locations.json
- MATRIX.md
- matrix_backend_truth.json
- scenario_S*/backend_truth.json
- scenario_S*/operator_checklist.md

**Artifact meaning (what each file signifies and why it exists):**

- `preflight.json`: environment truth at run start (URLs, health/version snapshots, commit hints). Use this to prove the run context was valid.
- `run.log`: live chronological progress log from `plugin_ui_truth_cert.py` (scenario begin/done and status codes). Use this to debug long-running or stalled runs.
- `log_locations.json`: pointers to important process logs (WSL Context Layer log, tunnel log, remote Plan-Gate/vLLM hints, IntelliJ log location). Use this as the operator index for trace capture.
- `MATRIX.md`: human-readable scenario matrix describing what plugin must show and fail conditions.
- `matrix_backend_truth.json`: machine-readable backend-truth rollup across all scenarios.
- `scenario_S*/backend_truth.json`: authoritative expected truth for each scenario (path/outcome/evidence signals). Plugin UI is judged against this.
- `scenario_S*/operator_checklist.md`: operator evidence sheet where screenshot path, plugin log snippet, and PASS/FAIL/NOT_PROVEN are recorded.

## <u>5) Execute Plugin UI Scenarios and Capture Proof</u>

**Goal:** prove plugin UI tells the same story as backend truth for each scenario class.

**Command/UI steps (execute these exact scenario inputs):**

1. **S1:** Strong v1 ask
  - Keep evidence-first ON.
  - Ask query: How does alert correlation work in this repo?
2. **S2:** Default v0 ask
  - Start IDE with evidence-first OFF (remove -Dmotadata.ask.evidence_first=true and unset MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST).
  - Ask query: How does alert correlation work in this repo?
3. **S3:** v1 fallback to v0 (operator-induced)
  - Keep evidence-first ON.
  - Temporarily set Context Layer URL to an unreachable port (for example: -Dmotadata.context_layer.url=http://127.0.0.1:65535).
  - Ask query: How does alert correlation work in this repo?
  - Restore context URL to http://127.0.0.1:8091 after capture.
4. **S4:** Weak evidence
  - Evidence-first ON.
  - Ask query: Which files implement topology anomaly scoring pipeline?
5. **S5:** No-match
  - Evidence-first ON.
  - Ask query: Where is the quantum flux capacitor serializer pipeline?
6. **S6:** Execute blocked
  - Action: Submit to Runtime
  - Command: false
7. **S7:** Execute refused
  - Action: Submit to Runtime
  - Command: curl https://example.com
8. **S8:** Execute failed after run
  - Action: Submit to Runtime
  - Command: python3 -c "import sys; sys.exit(1)"

**Expected capture workflow (for each scenario S1..S8):**

1. Run the scenario action from plugin UI.
2. Capture plugin-visible screenshot.
3. Capture plugin log snippet containing trace_id and/or routing_mode.
4. Fill scenario_S*/operator_checklist.md:
   - screenshot_path
   - plugin_log_snippet_path
   - PASS / FAIL / NOT_PROVEN

<u>Minimum capture per scenario</u>:

- backend JSON: already in scenario folder
- UI screenshot
- plugin log snippet

**Command/UI steps (plugin log source in IntelliJ):**

1. Help -> Show Log in Explorer/Finder/File Manager
2. Capture lines around the scenario timestamp with fields such as trace_id, routing_mode, plugin_ask_routing, or startup stack check findings.

## <u>6) Aggregate Certification</u>

**Goal:** convert per-scenario checklists into a single deterministic PASS/FAIL certification result.

**Command:**

```bash
cd /home/harshil/Harshil-PoCs/m-coder

./scripts/plugin_ui_truth_aggregate.py \
  --artifact-root docs/validation/artifacts/plugin_ui_truth_final_demo \
  --strict
```

**Expected outputs:**

- cert_summary.json
- cert_summary.md

*Strict mode exit behavior*:

- exit 0 only when all scenarios are PASS
- exit 1 when any FAIL or NOT_PROVEN remains

## <u>7) Final Demo Gate</u>

**Goal:** block demo claims unless UI truth certification is complete and clean.

Demo-ready only if:

- cert_summary overall is PASS
- no scenario has FAIL
- no scenario has NOT_PROVEN

If not PASS, do defect isolation before stagecraft:

- compare backend_truth.json vs plugin screenshot/log for the failing scenario
- fix plugin projection gap
- rerun that scenario and aggregate again

<u>Final proof pack must contain per scenario</u>:

- backend_truth.json
- screenshot file
- plugin log snippet file
- completed operator_checklist.md with PASS/FAIL/NOT_PROVEN

## <u>8) Quick Shutdown (WSL)</u>

**Goal:** cleanly stop local managed demo processes after run completion.

**Command:**

```bash
cd /home/harshil/Harshil-PoCs/m-coder
./scripts/wsl_plugin_mvp_stack.sh down
```

## <u>9) One-Command Cheat Sheet</u>

**Goal:** provide copy-paste shortcuts for operators during live demo prep.

**Bring-up**:

```bash
cd /home/harshil/Harshil-PoCs/m-coder && \
MOTADATA_ROOT=/home/harshil/Projects/Motadata \
M_CODER_REPO_ROOT=/home/harshil/Harshil-PoCs/m-coder \
ENABLE_SSH_TUNNEL=1 \
TUNNEL_TARGET=harshil@45.195.82.10 \
AUTO_ALIGN_CONTEXT_COMMIT=1 \
CONTEXT_PORT_RECLAIM=1 \
./scripts/wsl_plugin_mvp_stack.sh up
```

**Truth pack**:

```bash
cd /home/harshil/Harshil-PoCs/m-coder && \
./scripts/plugin_ui_truth_cert.py \
  --workspace-root /home/harshil/Projects/Motadata \
  --out-dir docs/validation/artifacts/plugin_ui_truth_final_demo
```

**Aggregate**:

```bash
cd /home/harshil/Harshil-PoCs/m-coder && \
./scripts/plugin_ui_truth_aggregate.py \
  --artifact-root docs/validation/artifacts/plugin_ui_truth_final_demo \
  --strict
```
