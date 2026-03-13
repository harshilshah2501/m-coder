# Stage-7 Deterministic Compiler

**Source:** `ml/training/pipeline/STAGE4_VARIANT_GENERATION.md`

This directory hosts the canonical compiler that transforms governance doctrine into training artifacts. The compiler is **deterministic** and **audit-grade**: no heuristics, no LLM calls, abort on malformed doctrine.

## Stage-7 Outputs

| Output | Path |
|--------|------|
| Golden exemplars JSONL | `ml/training/generated/golden_exemplars_v1.jsonl` |
| Dataset manifest | `ml/training/generated/dataset_manifest.json` |

## Schema

The compiler emits JSONL rows conforming to `dataset_schema.json`. Each row represents one training sample. The schema enforces strict structure; validation MUST reject any row that does not conform.
