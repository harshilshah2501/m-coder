# Layer-2 Architecture Lock v2

## Canonical Structure

Layer-2 (ML Compilation) owns:

- `pipeline/` — Doctrine, mutation specs, Stage-6 harness
- `compiler/` — Deterministic compiler (doctrine → JSONL)
- `generated/` — Compiler outputs only (JSONL, manifests)
- `training/` — Training scripts, configs, checkpoints
- `evaluation/` — Evaluation tooling
- `datasets/` — Curated/frozen datasets (e.g. sft/)
- `vendor/` — Read-only upstream vendor mirror

## Invariants

- **Numeric stage directories as direct children of ml/training are forbidden.** Stage-6 and Stage-08 live under `pipeline/` (`pipeline/stage6/`, `pipeline/stage08/`).
- **Vendor mirror is read-only upstream code.** No STAGE*.md, no .jsonl in vendor.
- **Compiler outputs only to `generated/`.** No stage7/ references.
- **Manifests must be repo-relative.** No absolute paths (e.g. /root/).
- **Governance and constitutional semantics remain untouched.** No changes to governance/**.

## Governed Runtime Phases

REF and CONF are **governed runtime phases**. The model may assist, but final REF/CONF behavior is policy-rendered and policy-scored. DES and CODE remain model-expressive phases. This doctrine was adopted after CONF→DES drift remained unresolved under SFT-only attempts; deterministic CONF rendering in Stage-6C achieved the cure (severity 80 S0, CONF→DES 0, S2/S3 0).

## CI Enforcement

`scripts/ci/check_structure.py` enforces these rules and fails on violation.
