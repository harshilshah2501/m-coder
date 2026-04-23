# Assist v2 Ask-to-Debug Investigate Bridge Task Report

Date: 2026-04-23  
Branch: `assist-layer-v2-investigate-bridge`  
Commit: `2ac02b4`

## Objective

Add a deterministic, additive Ask-to-Debug handoff under `assist_layer.assist_v2.investigate` without changing retrieval, governance, execution, or routing behavior.

In scope:

- Ask-mode payload shaping only.
- Surface investigate target only when owner file and owner method are explicitly grounded.
- Omit investigate bridge by default for weak or insufficient Ask results.

Out of scope:

- Any retrieval/ranking logic change.
- Any Plan-Gate governance change.
- Any Debug engine change.
- Any automatic debug execution.

## Implementation Summary

Updated files:

- `runtime/assist_layer/v2_router.py`
  - Added Ask-only investigate bridge builder.
  - Added strict eligibility gates:
    - `ask_path == v1_evidence`
    - `governance_posture == PLAN_ONLY`
    - `execution == false`
    - `evidence_quality == STRONG`
    - explicit owner file and owner method
    - method visibility evidence present
  - Added deterministic suggested prompt:
    - `Investigate this owner method and trace visible failure points.`
  - Omission-by-default behavior when not eligible.
- `runtime/tests/test_assist_layer_v1.py`
  - Added unit coverage for grounded investigate bridge inclusion.
  - Added unit coverage for weak-context omission.
  - Asserted no investigate bridge in Debug mode.
- `runtime/tests/test_ask_v1_ingest.py`
  - Added HTTP integration coverage for Ask-mode investigate bridge on grounded evidence.

## Test Plan and Results

### A) Automated tests (local branch validation)

Command:

```bash
pytest -q runtime/tests/test_assist_layer_v1.py \
  runtime/tests/test_ask_v1_ingest.py::test_ask_v1_ask_mode_via_plan_gate_http_surfaces_investigate_bridge \
  runtime/tests/test_ask_v1_ingest.py::test_ask_v1_debug_v2_via_plan_gate_http_preserves_explain_debug_shape
```

Result:

- `31 passed`

Command:

```bash
pytest -q \
  runtime/tests/test_ask_v1_ingest.py::test_ask_v1_via_plan_gate_http \
  runtime/tests/test_ask_service.py::test_handle_ask_request_execution_false_and_plan_only \
  runtime/tests/test_assist_layer_v1.py::test_assist_v2_debug_activation_adds_debug_v2_without_ask_sections
```

Result:

- `3 passed`

Lint status:

- No linter errors in modified files.

### B) Real-wire artifact (generated from branch)

Artifact:

- `runtime/.run/assist_v2_investigate_bridge.real_wire.json`

Observed in artifact:

- `assist_layer.assist_v2.route_decision.mode = ask`
- `assist_layer.assist_v2.investigate.available = true`
- Target grounded to explicit owner method:
  - `src/main/java/com/mindarray/integration/ServiceNowIntegration.java`
  - `synchronizeIncident`
- Ask invariants preserved:
  - `evidence_first_meta.ask_path = v1_evidence`
  - `governance_posture = PLAN_ONLY`
  - `execution = false`

### C) WSL manual verification (operator run)

Grounded case (manual `curl` to `/v1/ask`):

- `assist_layer.assist_v2.investigate` present
- `available = true`
- reason `owner_method_grounded`
- target file/method correctly populated

Weak case (manual `curl` to `/v1/ask`):

- `assist_layer.assist_v2.route_decision.mode = ask`
- `assist_layer.assist_v2.investigate = null` (omitted as designed)

## Conclusion

The Ask-to-Debug Investigate Bridge v1 is complete and validated for closure scope.

What is now true:

- Grounded Ask responses expose a deterministic investigate handoff.
- Weak/insufficient Ask responses do not expose a bridge (omission default).
- Ask remains evidence-first, plan-only, and non-executing.
- Debug behavior and payload remain unchanged.

This meets the intended product behavior: Ask selects, Debug inspects, and the bridge is explicit, grounded, and fail-closed.
