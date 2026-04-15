# Motadata developer utility validation

This document describes the **developer utility** validation track: whether Ask, Debug, and Plan outputs are *useful* on Motadata-shaped tasks, beyond transport and contract correctness. It assumes the same **Layer-5 → Layer-3** path as production verification (evidence from Context Layer, decisions from Plan-Gate); see `docs/ARCHITECTURE_4_LAYER.md`.

## How this differs from production / contract verification

| Track | Proves | Primary guide / artifact |
| ----- | ------ | ------------------------- |
| **Contract / system** | Healthy services, expected routes, response shapes, governance fields, repeatability | [MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md) |
| **Developer utility** | Heuristic checks on groundedness, honesty on weak evidence, explain structure, and plan content cues | This guide + `docs/validation/motadata_developer_utility_scenarios.v1.json` |

Contract verification can pass while answers are vague or misleading; utility checks are an **additional** signal, not a replacement for human review.

## Initial scope (v1)

The first scenario file is intentionally small:

- **Anchored Ask** — specific question with path/symbol expectations.
- **Broad Ask honesty** — when evidence is weak, responses should not fake certainty; assertions are partly **heuristic** (substring and metadata checks).
- **Anchored Debug** — EXPLAIN_DEBUG with file context; structured fields and concrete failure language.
- **Bounded Plan** — plan/decision response contains risk or guardrail language and file-like references where applicable.

## What is *not* claimed

- **Stage 3 loop** (or any multi-step product agent) end-to-end usefulness on real traffic is **not** treated as closed by this track.
- Utility assertions are **approximate**: they use text matching, path overlap, and simple counts. Tune scenarios when the model or retrieval stack shifts.

## Scenario file and verifier

- Scenarios: `docs/validation/motadata_developer_utility_scenarios.v1.json`
- Verifier: `runtime/scripts/motadata_behavior_verify.py`
- JSON report key: `developer_utility_suite` (alongside `scenario_suite` for contract scenarios).

### Examples

Utility only (no smoke pipeline; requires at least one scenario file):

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --utility-scenarios docs/validation/motadata_developer_utility_scenarios.v1.json \
  --scenarios-only \
  --print dev
```

Contract + utility with smoke:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --repeat 2 \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --utility-scenarios docs/validation/motadata_developer_utility_scenarios.v1.json \
  --print dev
```

Keep the utility suite **small and anchored**; broad, repo-wide questions are poor fit for stable automated gates.
