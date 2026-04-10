# Assist Layer v1 Integration Proof Pass

## Proof plan (minimal)

1. Live metadata proof via one `/v0/ask` call:
- Command: `curl -X POST http://127.0.0.1:28089/v0/ask --data-binary @live_ask_request.json`
- Inspect: `live_ask_response.json` and `live_ask_response_excerpt.json`
- Pass criteria:
  - `assist_layer` exists
  - contains `original_query`, `augmented_query`, `assist_status`, `transform_codes_applied`, `retrieval_drift_validation`

2. Runtime query authority proof at integration seam:
- Command: python comparison script producing `authority_and_drift_comparison.json`
- Inspect:
  - `authority_proof.runtime_query_is_original == true`
  - `authority_proof.runtime_query_differs_from_augmented == true`
- Pass criteria:
  - runtime ask payload query equals original query
  - runtime ask payload query is not augmented query when augmentation occurred

3. Behavioral drift proof (representative control comparison):
- Command: same python comparison script
- Inspect:
  - `behavior_control_comparison.same_core_fields` all true
  - `same_context_files == true`
  - `same_plan_steps == true`
- Pass criteria:
  - no meaningful drift in representative Ask output path/outcome for same runtime input

## Representative live Ask input

- Query: `Where   is retrive cfg??`
- Why chosen: triggers visible deterministic transforms (whitespace, punctuation, typo-light, abbreviation)

## Results

- `assist_layer` metadata present: PASS
- runtime query authority anchored to original query: PASS
- representative no-drift control comparison: PASS

## Notes

- Assist metadata shows transformed advisory output (`augmented_query`), but runtime query remains the original input used by Ask handlers.
- Governance posture and execution semantics remain unchanged (`PLAN_ONLY`, `execution=false`).
