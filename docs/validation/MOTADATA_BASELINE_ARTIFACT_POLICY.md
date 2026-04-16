# Motadata Baseline Artifact Policy

This policy defines how retrieval/behavior baseline artifacts are named, generated, and compared.

Primary artifact type:

- `motadata_behavior_validation.json` produced by `runtime/scripts/motadata_behavior_verify.py`

---

## 1) Baseline vs candidate naming

Use deterministic filenames under `runtime/.run/`:

- Baseline:
  - `motadata_behavior_validation.BASELINE.<label>.json`
- Candidate:
  - `motadata_behavior_validation.CANDIDATE.<label>.json`

Recommended `<label>` format:

- `<YYYYMMDD>.<short_sha>.<workspace_tag>`
- example: `20260416.250c40b.motadata`

Avoid generic names like `new.json`, `latest.json`, or ad-hoc copies.

---

## 2) Required run invariants

Baseline and candidate comparisons are valid only when all are identical:

- same `--workspace-root`
- same `--scenarios` file
- same `--quality-policy` file
- same Stage A mode (`--export-stage-a`)
- same service topology/state (Context Layer + Plan-Gate + model readiness)

If any invariant differs, treat the comparison as informational only, not regression-grade.

---

## 3) Canonical generation command

```bash
PYTHONPATH=. python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print dev \
  --out "runtime/.run/motadata_behavior_validation.<BASELINE_OR_CANDIDATE>.<label>.json"
```

For the rolling canonical pointer, also write:

- `runtime/.run/motadata_behavior_validation.json`

---

## 4) Comparison protocol

Use the diff utility:

```bash
python3 runtime/scripts/diff_motadata_behavior_validation.py \
  "runtime/.run/motadata_behavior_validation.BASELINE.<label>.json" \
  "runtime/.run/motadata_behavior_validation.CANDIDATE.<label>.json"
```

Required in regression reports:

- both JSON artifact paths
- m-coder git SHA
- workspace identity hash (from scenario `actual_summary.retrieval_gates.workspace_identity_hash`)
- note on Stage A mode and policy file

---

## 5) Current frozen proof point

Current baseline proof after Debug Usefulness v1.1 and retrieval stabilization:

- suite status: `all_pass=true`
- strict anchored owner-top1: pass
- broad ask: improved (reduced generic-infra ratio vs earlier baseline)
- artifact: `runtime/.run/motadata_behavior_validation.json` (latest synchronized run)

Use this as the reference point for next-lane work unless a new baseline is intentionally promoted.
