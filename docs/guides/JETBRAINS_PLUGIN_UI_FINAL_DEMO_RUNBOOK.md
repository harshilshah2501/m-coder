# JetBrains Plugin UI Final Demo Runbook

Purpose: run a final, truthful plugin demo where UI output is certified against backend truth.

Environment values fixed for this runbook:

- MOTADATA_ROOT=/home/harshil/Projects/Motadata
- TUNNEL_TARGET=harshil@45.195.82.10

Plugin package for install from disk:

- jetbrains-plugin/build/distributions/motadata-jetbrains-plugin-0.2.7.zip

## 1) Outcome target

A demo is accepted only if plugin-visible behavior matches backend truth for all scenario classes:

- Ask path visibility (v0, v1, explain/debug, fallback)
- Evidence and insufficiency visibility
- plan_summary.notes visibility
- Honest empty/no-match behavior
- Execute outcome truthfulness (executed, blocked, refused, executed_failed)
- Explicit fallback visibility

## 2) Terminal setup (WSL)

Use Terminal A for stack control and keep it available during the demo.

```bash
cd /home/harshil/Harshil-PoCs/m-coder

export MOTADATA_ROOT=/home/harshil/Projects/Motadata
export ENABLE_SSH_TUNNEL=1
export TUNNEL_TARGET=harshil@45.195.82.10
export PLAN_GATE_URL=http://127.0.0.1:8089
export CONTEXT_URL=http://127.0.0.1:8091

./scripts/wsl_plugin_mvp_stack.sh up
```

Expected:

- tunnel up to GPU host
- Context Layer started on WSL
- health checks pass
- version and compatibility checks pass

Run explicit check command before opening IDE:

```bash
cd /home/harshil/Harshil-PoCs/m-coder

export MOTADATA_ROOT=/home/harshil/Projects/Motadata
export ENABLE_SSH_TUNNEL=1
export TUNNEL_TARGET=harshil@45.195.82.10

./scripts/wsl_plugin_mvp_stack.sh check
```

## 3) JetBrains plugin launch config

Install plugin ZIP in IntelliJ IDEA:

1. Settings -> Plugins
2. Gear icon -> Install Plugin from Disk...
3. Select: jetbrains-plugin/build/distributions/motadata-jetbrains-plugin-0.2.7.zip

Start IDE with plugin enabled and configure runtime URLs in the same host context as the plugin process:

- MOTADATA_PLAN_GATE_URL=http://127.0.0.1:8089
- MOTADATA_CONTEXT_LAYER_URL=http://127.0.0.1:8091
- MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST=1

Optional strict startup toggle:

- motadata.startup.stack.check.enabled=true

Recommended VM options for deterministic demo runs:

-Dmotadata.plan_gate.url=http://127.0.0.1:8089
-Dmotadata.context_layer.url=http://127.0.0.1:8091
-Dmotadata.ask.evidence_first=true

On project load, plugin startup check should show one of:

- Motadata Stack Check: OK
- Motadata Stack Check: WARN
- Motadata Stack Check: FAIL

Do not continue demo if FAIL unless the scenario intentionally demonstrates failure handling.

## 4) Generate backend truth pack (WSL)

Use Terminal B:

```bash
cd /home/harshil/Harshil-PoCs/m-coder

./scripts/plugin_ui_truth_cert.py \
  --workspace-root /home/harshil/Projects/Motadata \
  --out-dir docs/validation/artifacts/plugin_ui_truth_final_demo
```

Generated artifacts include:

- preflight.json
- MATRIX.md
- scenario_S*/backend_truth.json
- scenario_S*/operator_checklist.md

## 5) Execute plugin UI scenarios and capture proof

Use these exact UI inputs for each scenario in order:

1. S1 Strong v1 ask
  - Keep evidence-first ON.
  - Ask query: How does alert correlation work in this repo?
2. S2 Default v0 ask
  - Start IDE with evidence-first OFF (remove -Dmotadata.ask.evidence_first=true and unset MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST).
  - Ask query: How does alert correlation work in this repo?
3. S3 v1 fallback to v0 (operator-induced)
  - Keep evidence-first ON.
  - Temporarily set Context Layer URL to an unreachable port (for example: -Dmotadata.context_layer.url=http://127.0.0.1:65535).
  - Ask query: How does alert correlation work in this repo?
  - Restore context URL to http://127.0.0.1:8091 after capture.
4. S4 Weak evidence
  - Evidence-first ON.
  - Ask query: Which files implement topology anomaly scoring pipeline?
5. S5 No-match
  - Evidence-first ON.
  - Ask query: Where is the quantum flux capacitor serializer pipeline?
6. S6 Execute blocked
  - Action: Submit to Runtime
  - Command: false
7. S7 Execute refused
  - Action: Submit to Runtime
  - Command: curl https://example.com
8. S8 Execute failed after run
  - Action: Submit to Runtime
  - Command: python3 -c "import sys; sys.exit(1)"

For each scenario S1..S8 in the generated matrix:

1. Run the scenario action from plugin UI.
2. Capture plugin-visible screenshot.
3. Capture plugin log snippet containing trace_id and/or routing_mode.
4. Fill scenario_S*/operator_checklist.md:
   - screenshot_path
   - plugin_log_snippet_path
   - PASS / FAIL / NOT_PROVEN

Minimum capture per scenario:

- backend JSON: already in scenario folder
- UI screenshot
- plugin log snippet

Plugin log source in IntelliJ:

1. Help -> Show Log in Explorer/Finder/File Manager
2. Capture lines around the scenario timestamp with fields such as trace_id, routing_mode, plugin_ask_routing, or startup stack check findings.

## 6) Aggregate certification

After filling all scenario checklists:

```bash
cd /home/harshil/Harshil-PoCs/m-coder

./scripts/plugin_ui_truth_aggregate.py \
  --artifact-root docs/validation/artifacts/plugin_ui_truth_final_demo \
  --strict
```

Outputs:

- cert_summary.json
- cert_summary.md

Strict mode exit behavior:

- exit 0 only when all scenarios are PASS
- exit 1 when any FAIL or NOT_PROVEN remains

## 7) Final demo gate

Demo-ready only if:

- cert_summary overall is PASS
- no scenario has FAIL
- no scenario has NOT_PROVEN

If not PASS, do defect isolation before stagecraft:

- compare backend_truth.json vs plugin screenshot/log for the failing scenario
- fix plugin projection gap
- rerun that scenario and aggregate again

Final proof pack must contain per scenario:

- backend_truth.json
- screenshot file
- plugin log snippet file
- completed operator_checklist.md with PASS/FAIL/NOT_PROVEN

## 8) Quick shutdown (WSL)

```bash
cd /home/harshil/Harshil-PoCs/m-coder
./scripts/wsl_plugin_mvp_stack.sh down
```

## 9) One-command cheat sheet

Bring-up:

```bash
cd /home/harshil/Harshil-PoCs/m-coder && \
MOTADATA_ROOT=/home/harshil/Projects/Motadata \
ENABLE_SSH_TUNNEL=1 \
TUNNEL_TARGET=harshil@45.195.82.10 \
./scripts/wsl_plugin_mvp_stack.sh up
```

Truth pack:

```bash
cd /home/harshil/Harshil-PoCs/m-coder && \
./scripts/plugin_ui_truth_cert.py \
  --workspace-root /home/harshil/Projects/Motadata \
  --out-dir docs/validation/artifacts/plugin_ui_truth_final_demo
```

Aggregate:

```bash
cd /home/harshil/Harshil-PoCs/m-coder && \
./scripts/plugin_ui_truth_aggregate.py \
  --artifact-root docs/validation/artifacts/plugin_ui_truth_final_demo \
  --strict
```
