# Plugin UI Truth Certification

Purpose: certify that plugin UI is a truthful projection of backend outputs (no silent fallback, no outcome collapsing, no confidence theater).

## Scope

This pass is a UI truth audit, not a backend correctness audit.

The script generates backend truth artifacts for plugin-facing scenarios and creates operator checklists for UI parity validation.

## Script

Path: scripts/plugin_ui_truth_cert.py

Aggregation path: scripts/plugin_ui_truth_aggregate.py

Final operator flow runbook: docs/guides/JETBRAINS_PLUGIN_UI_FINAL_DEMO_RUNBOOK.md

## Run

```bash
cd /home/harshil/Harshil-PoCs/m-coder

# Use the same workspace root your Context Layer/Plan-Gate sees.
./scripts/plugin_ui_truth_cert.py \
  --workspace-root /home/harshil/Projects/Motadata
```

Optional overrides:

```bash
CONTEXT_URL=http://127.0.0.1:8091 \
PLAN_GATE_URL=http://127.0.0.1:8089 \
./scripts/plugin_ui_truth_cert.py \
  --workspace-root /home/harshil/Projects/Motadata \
  --out-dir docs/validation/artifacts/plugin_ui_truth_manual_run
```

## Output

Artifact root:

- docs/validation/artifacts/plugin_ui_truth_<timestamp>/

Generated files:

- preflight.json
- MATRIX.md
- matrix_backend_truth.json
- scenario_S*/backend_truth.json
- scenario_S*/operator_checklist.md

## Scenarios

- S1: v1 ask with strong evidence
- S2: default v0 ask
- S3: v1 fallback to v0 (operator-induced)
- S4: weak evidence
- S5: no-match
- S6: execute blocked
- S7: execute refused
- S8: execute failed after run

## Operator proof requirement per scenario

- backend JSON (already generated)
- plugin UI screenshot
- plugin log snippet containing trace_id or routing_mode
- PASS / FAIL / NOT_PROVEN in operator_checklist.md

## Acceptance rule

For each scenario, plugin must tell the same story as backend truth for:

- path selection (v0/v1/fallback)
- evidence or insufficiency visibility
- notes visibility where backend provides notes
- execute outcome class (executed, blocked, refused, executed_failed)

Fail the certification if any scenario shows silent fallback, hidden path, hidden insufficiency, or collapsed execute outcome semantics.

## Aggregate final certification

```bash
cd /home/harshil/Harshil-PoCs/m-coder

./scripts/plugin_ui_truth_aggregate.py \
  --artifact-root docs/validation/artifacts/plugin_ui_truth_manual_run \
  --strict
```

This writes:

- cert_summary.json
- cert_summary.md

Strict mode returns non-zero unless all scenarios are marked PASS.
