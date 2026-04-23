# Context Budget Policy Enforcement v1

Status: active  
Scope: telemetry-to-policy enforcement for Ask/Debug surfaces, plus declared policy budgets for Plan/Code validation.

## Policy version

- `context_budget_policy.v1`

## Truncation order (deterministic)

1. `bundle_items_order`
2. `max_files`
3. `max_bytes`

## Surface budgets

| Surface | warn_prompt_input_tokens | warn_bundle_context_bytes | max_files | max_bytes |
|---|---:|---:|---:|---:|
| Ask | 7500 | 240000 | 40 | 350000 |
| Debug | 9000 | 280000 | 40 | 350000 |
| Plan | 4000 | 140000 | 24 | 220000 |
| Code | 3500 | 120000 | 20 | 180000 |

## Runtime behavior

- Ask/Debug now emit `metadata.context_budget_policy` with:
  - warning thresholds
  - hard caps
  - truncation order
  - warnings emitted at runtime (`warn_*`, `hard_cap_truncation_applied`)
- Retrieval/governance/routing semantics are unchanged.

## Notes

- Plan/Code budgets are currently policy declarations for validation and observability alignment.
- This pass intentionally avoids retrieval, ranking, and Plan-Gate authority changes.
