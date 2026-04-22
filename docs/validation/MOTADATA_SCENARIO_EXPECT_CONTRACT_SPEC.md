# Motadata Scenario Expect Contract Spec

This is the canonical field guide for `expect` blocks in:
- `docs/validation/motadata_aiops_behavior_scenarios.v1.json`

Goal:
- Explain **which `expect` keys are valid** per capability
- Explain **what each key means** in simple words
- Show **required vs optional** behavior in practice

Primary runtime enforcement:
- `runtime/scripts/motadata_behavior_verify.py`

---

## 1) Scenario object skeleton

Every scenario row uses this shape:

```json
{
  "id": "scenario_id",
  "capability": "ask|debug|plan|code",
  "description": "why this scenario exists",
  "... capability-specific input fields ...": "...",
  "expect": {
    "... capability-specific contract fields ...": "..."
  }
}
```

Notes:
- `expect` is capability-specific.
- Extra flags outside `expect` (for example `must_cite_file_or_symbol_anchor`) are also enforced by verifier logic.

---

## 2) Ask capability contract

### Input fields commonly used
- `query` (string)
- optional guard flags:
  - `must_cite_file_or_symbol_anchor` (bool)
  - `forbid_generic_scan_answer` (bool)
  - `requires_behavior_flow` (bool)

### `expect` keys for Ask

| Key | Type | Meaning |
|---|---|---|
| `governance_posture` | string | Expected posture returned by Ask (`PLAN_ONLY` for these scenarios). |
| `execution` | bool | Expected execution flag in Ask response (usually `false`). |
| `ask_path` | string | Expected Ask path marker (usually `v1_evidence`). |
| `min_plan_steps` | int | Minimum number of answer steps required. |
| `text_contains_any` | list[string] | At least one phrase must appear in answer text (`plan_summary.steps/notes`). |
| `evidence_quality_any_of` | list[string] | Optional allowed values for evidence quality. |
| `require_authority_primary_owner` | bool | Owner file must exist in `authority_resolution`. |
| `require_owner_in_top3` | bool | Owner file must appear in top-3 evidence entries. |
| `require_stage_a_owner_injected_min` | int | Minimum Stage A owner_injected lane count. |
| `require_authority_status` | string | Exact expected authority status (`validated`, etc.). |

### Quality policy interaction (Ask)

When `--quality-policy` is supplied, Ask scenarios are also checked against policy profile (from `motadata_evidence_quality_policy.v1.json`), including:
- `max_generic_infra_ratio_top_k`
- `max_distractor_count_top_k`
- `min_anchor_hit_rate_top_k`
- `require_owner_in_top3`
- `require_owner_in_top1`
- `require_stage_a_owner_injected_min`

---

## 3) Debug capability contract

### Input fields commonly used
- `query`
- `debug_query`
- `selected_file`
- `selection`
- optional `requires_selected_file_binding` (bool)

### `expect` keys for Debug

| Key | Type | Meaning |
|---|---|---|
| `routing_mode` | string | Expected debug routing mode (`explain_debug`). |
| `explain_debug_has_keys` | list[string] | Required keys inside `explain_debug` object. |
| `must_reference_selected_file_or_symbol` | bool | Debug answer/evidence must mention selected file symbol. |
| `require_selected_file_in_evidence` | bool | Selected file/symbol must appear in `explain_debug.evidence`. |
| `require_selected_file_in_context_bundle` | bool | Selected file must be present in `context_bundle.files`. |
| `must_suggest_concrete_failure_points` | bool | Must include concrete control-flow/failure cues (branch/null/condition/etc.). |
| `required_text_contains_any` | list[string] | At least one required phrase must appear in debug summary/evidence. |
| `must_have_confidence_limits` | bool | `confidence_limits` must be present and non-empty. |
| `require_insufficient_grounding` | bool | Must explicitly report insufficient grounding when context is missing. |
| `require_missing_in_context_marker` | bool | Evidence must contain `missing_in_context` marker. |
| `require_selected_file_symbol_hits_min` | int | Minimum count of selected file/symbol mentions across explain text + evidence. |
| `require_method_name_mentions_min` | int | Minimum number of method-like mentions in explain text/evidence refs. |
| `require_evidence_line_refs_min` | int | Minimum count of evidence refs shaped like `path:method_or_anchor`. |
| `require_control_flow_markers_min` | int | Minimum count of control-flow cues (`if`, `branch`, `return`, `null`, etc.). |
| `forbid_generic_phrases_any` | list[string] | Disallowed generic phrases that should fail depth quality when present. |

### Contract pass vs depth pass (Debug)

Debug scenarios now report two outcomes:
- `contract_pass`: routing/schema/truthfulness contract checks
- `depth_pass`: engineering-depth checks (symbol hits, method mentions, evidence refs, anti-generic language)

Overall scenario `pass` for Debug is `contract_pass AND depth_pass`.

---

## 4) Plan capability contract

### Input fields commonly used
- No natural-language query required in current shadow scenarios.
- Verifier sends deterministic shadow `plan_request.v0.1`.

### `expect` keys for Plan

| Key | Type | Meaning |
|---|---|---|
| `schema_version` | string | Expected response schema version (`decision_response.v0.1`). |
| `decision_present` | bool | `decision` must be non-empty. |
| `decision_any_of` | list[string] | Optional allow-list for decision values. |

### Extra scenario flag
- `requires_playbook` (bool): if true, missing decision fails regardless of other keys.

---

## 5) Code capability contract

### Input fields commonly used
- `command` (string)

### `expect` keys for Code

| Key | Type | Meaning |
|---|---|---|
| `schema_version` | string | Expected response schema version (`execute_response.v0.1`). |
| `outcome` | string | Exact expected outcome (`EXECUTED`, `BLOCKED`, `REFUSED`). |
| `outcome_any_of` | list[string] | Allowed outcome set (useful for environment-flexible probes). |
| `executed` | bool | Exact expected executed flag. |
| `executed_any_of` | list[bool] | Allowed executed values. |
| `posture` | string | Optional exact posture check. |
| `coherent_executed` | bool | Enforce consistency: `EXECUTED -> executed=true`; `BLOCKED/REFUSED -> executed=false`. |

---

## 6) Minimal examples by capability

### Ask

```json
{
  "id": "ask_example",
  "capability": "ask",
  "query": "How are config stores organized?",
  "expect": {
    "governance_posture": "PLAN_ONLY",
    "execution": false,
    "ask_path": "v1_evidence",
    "min_plan_steps": 1,
    "text_contains_any": ["AbstractConfigStore"]
  }
}
```

### Debug

```json
{
  "id": "debug_example",
  "capability": "debug",
  "query": "Why might ConfigStore.getItem() return null?",
  "debug_query": "Debug null-return paths in AbstractConfigStore.getItem.",
  "selected_file": "motadata/src/main/java/com/mindarray/store/AbstractConfigStore.java",
  "selection": "Trace null checks and branches.",
  "expect": {
    "routing_mode": "explain_debug",
    "explain_debug_has_keys": ["summary", "evidence", "confidence_limits"],
    "require_selected_file_in_evidence": true,
    "must_suggest_concrete_failure_points": true,
    "require_selected_file_symbol_hits_min": 2,
    "require_method_name_mentions_min": 1,
    "require_evidence_line_refs_min": 1
  }
}
```

### Plan

```json
{
  "id": "plan_example",
  "capability": "plan",
  "expect": {
    "schema_version": "decision_response.v0.1",
    "decision_present": true
  }
}
```

### Code

```json
{
  "id": "code_example",
  "capability": "code",
  "command": "pwd",
  "expect": {
    "schema_version": "execute_response.v0.1",
    "outcome_any_of": ["EXECUTED", "REFUSED", "BLOCKED"],
    "coherent_executed": true
  }
}
```

---

## 7) Practical authoring rules

1. Keep `expect` **minimal**: only add keys that reflect the behavior you truly require.
2. Prefer `*_any_of` for environment-dependent probes.
3. Use strict keys (`outcome`, `executed`) for hard safety guarantees (for example destructive commands must be blocked).
4. For Ask correctness, rely on `text_contains_any` plus policy gates.
5. For Debug truthfulness, include insufficiency markers when selected file is intentionally missing.

---

## 8) Versioning and change discipline

- Scenario pack schema is currently:
  - `motadata_aiops_behavior_scenarios.v1`
- Quality policy schema is currently:
  - `motadata_evidence_quality_policy.v1`

When adding/changing fields:
1. Update scenario JSON.
2. Update verifier enforcement logic.
3. Update this contract spec.
4. Re-run deep slices for affected capabilities.

