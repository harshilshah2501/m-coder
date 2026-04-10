# Assist Layer v2 Evaluation Artifacts

This folder contains deterministic, shadow-only evaluation outputs for Stage 2.5 Assist Layer v1.

Scope

- Evaluation only; no runtime behavior changes.
- No Plan-Gate behavior changes.
- No runtime query authority changes.

Primary artifacts

- `assist_eval_summary.json`
  - Aggregate benchmark summary.
  - Includes totals, verdict distribution, counts by transform, counts by category, and notable deterministic patterns.
- `assist_confidence_policy.v1.json`
  - Evidence-derived confidence policy.
  - Advisory-only in this pass (not runtime-enforced).
- `assist_v2_batch_*.json`
  - Per-query evaluation artifacts for the batch run.

Recorded batch outcome (current)

- improved: 0
- same: 17
- degraded_minor: 16
- degraded_major: 2

Interpretation

- Assist is often neutral.
- Minor retrieval drift is frequent.
- Major degradation is present but uncommon.
- No consistent measurable improvement is demonstrated in the current batch.

System stance for this stage

- Assist Layer v1 remains advisory-only.
- `augmented_query` is not trusted to influence runtime retrieval or reasoning.
- Outputs are retained for inspection, observability, and future evaluation.
