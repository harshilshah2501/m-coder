# Assist v2 API Contract Freeze v1

Date: 2026-04-23  
Status: frozen for backend deployment hardening  
Applies to: `POST /v1/ask` response payload (`assist_layer.assist_v2`)

## 1) Scope and intent

This document freezes the backend contract for Assist v2 surfaces that are already shipped:

- Ask surface (`assist_v2.answer/evidence/gaps/next_steps`)
- Debug surface (`assist_v2.debug_v2`)
- Ask-to-Debug Investigate bridge (`assist_v2.investigate`)

This is a compatibility and deployment freeze. It does not redefine retrieval, governance, or execution behavior.

## 2) Global invariants (must hold)

- Ask path remains evidence-first: `evidence_first_meta.ask_path = v1_evidence`
- Governance remains advisory-only: `governance_posture = PLAN_ONLY`
- Ask execution remains disabled: `execution = false`
- Debug remains selected-file grounded and fail-closed for missing-file insufficiency
- Assist v2 shaping is additive only; it does not replace top-level contracts (`plan_summary`, `explain_debug`, metadata)

## 3) Routing and mode contract

`assist_v2.route_decision.mode` is authoritative for Assist v2 surface selection:

- `ask` -> Ask sections may be present; Debug section must be absent
- `debug` -> `debug_v2` may be present; Ask sections and Investigate bridge must be absent
- `mixed` -> Ask sections may be present; Investigate bridge omitted in v1 freeze

## 4) Ask surface contract (frozen)

When mode is `ask` or `mixed`, Assist v2 may include:

- `answer`
  - `direct_grounded_answer` (optional)
  - `primary_owner_or_locus` (optional object: `symbol`, `file`, `method`)
  - `execution_summary` (optional)
- `evidence`
  - `owner_anchor`
  - `context_anchors`
  - `proof_density_summary`
  - `context_budget_telemetry_summary`
- `gaps`
  - `explicit_evidence_limits` (array)
- `next_steps`
  - `bounded_verification_steps` (array)

Compatibility rule:

- Existing top-level Ask payload fields remain source-of-truth and unchanged.
- Assist fields are additive projections from existing payload/meta, not new inference engines.

## 5) Debug surface contract (frozen)

When mode is `debug`, Assist v2 includes:

- `debug_v2.summary` (string)
- `debug_v2.execution_flow` (string)
- `debug_v2.likely_failure_points` (array[string])
- `debug_v2.evidence`
  - `selected_file` (string)
  - `selected_method` (string)
  - `line_refs` (array[string])
  - `grounding_tier` (`none|declarative|partial|executable`)
- `debug_v2.confidence_limits`
  - `visible` (array[string])
  - `not_visible` (array[string])
  - `requires_next_inspection` (array[string])
- `debug_v2.next_inspection_targets` (array[object])

Compatibility rule:

- Top-level `explain_debug` remains present and unchanged in Debug responses.
- `debug_v2` is additive structured projection, not replacement.

## 6) Investigate bridge contract (frozen)

Surface:

- `assist_v2.investigate` (Ask mode only)

Eligibility (all required):

- `evidence_first_meta.ask_path == v1_evidence`
- `governance_posture == PLAN_ONLY`
- `execution == false`
- evidence quality strong enough for explicit owner-method grounding
- owner file is explicit
- owner method is explicit
- owner method visibility is grounded

Payload shape:

- `available` (boolean; true when present in v1)
- `reason` (`owner_method_grounded|owner_method_visible`)
- `target`
  - `file`
  - `method`
  - `symbol_hints` (array)
- `handoff_context`
  - `source_mode` (`ask`)
  - `ask_path`
  - `governance_posture`
  - `execution`
- `evidence_anchor`
  - `owner_file`
  - `owner_method_visible`
  - `grounding_tier`
  - `proof_density` (`method_window_visible_rate`, `execution_path_stitched`, `call_site_resolution_state`)
- `suggested_prompt` (fixed deterministic string)

Omission rule (v1 freeze):

- If eligibility is not met, omit `assist_v2.investigate` entirely.
- Do not emit decorative `available=false` objects in this phase.

## 7) Compatibility policy

- Additive-only changes are allowed if they do not alter current semantics.
- Removal/rename/type-change of frozen keys is a breaking change and forbidden in this phase.
- Any new surface must be gated behind explicit versioning or a new freeze document.

## 8) Canonical examples

### 8.1 Ask + Investigate present (grounded)

```json
{
  "assist_layer": {
    "assist_v2": {
      "route_decision": {"mode": "ask"},
      "answer": {},
      "evidence": {},
      "gaps": {},
      "next_steps": {},
      "investigate": {
        "available": true,
        "reason": "owner_method_grounded",
        "target": {
          "file": "src/main/java/com/mindarray/integration/ServiceNowIntegration.java",
          "method": "synchronizeIncident",
          "symbol_hints": ["ServiceNowIntegration", "synchronizeIncident"]
        },
        "handoff_context": {
          "source_mode": "ask",
          "ask_path": "v1_evidence",
          "governance_posture": "PLAN_ONLY",
          "execution": false
        },
        "evidence_anchor": {
          "owner_file": "src/main/java/com/mindarray/integration/ServiceNowIntegration.java",
          "owner_method_visible": true,
          "grounding_tier": "executable",
          "proof_density": {
            "method_window_visible_rate": 1.0,
            "execution_path_stitched": false,
            "call_site_resolution_state": "none"
          }
        },
        "suggested_prompt": "Investigate this owner method and trace visible failure points."
      }
    }
  }
}
```

### 8.2 Ask weak context (Investigate omitted)

```json
{
  "assist_layer": {
    "assist_v2": {
      "route_decision": {"mode": "ask"},
      "answer": {},
      "evidence": {},
      "gaps": {},
      "next_steps": {}
    }
  }
}
```

### 8.3 Debug structured output

```json
{
  "assist_layer": {
    "assist_v2": {
      "route_decision": {"mode": "debug"},
      "debug_v2": {
        "summary": "...",
        "execution_flow": "...",
        "likely_failure_points": ["..."],
        "evidence": {
          "selected_file": "module/sample.py",
          "selected_method": "hello_unit",
          "line_refs": [],
          "grounding_tier": "partial"
        },
        "confidence_limits": {
          "visible": [],
          "not_visible": [],
          "requires_next_inspection": []
        },
        "next_inspection_targets": []
      }
    }
  }
}
```
