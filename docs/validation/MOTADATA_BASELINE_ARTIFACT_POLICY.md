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

Refresh authority index first (smart auto full/incremental):

```bash
PYTHONPATH=. python3 runtime/scripts/build_authority_code_index.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --out "runtime/.cache/authority_code_index.motadata.json"
```

Then run behavior verification:

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

---

## 6) Authority Hardening v1 validation note

Authority Expansion Hardening v1 validated on WSL with:

- baseline: `runtime/.run/motadata_behavior_validation.CANDIDATE.AUTHORITY_EXPANSION.motadata.json`
- candidate: `runtime/.run/motadata_behavior_validation.CANDIDATE.AUTHORITY_HARDENING_V1.motadata.json`
- suite status: `all_pass=true`

Observed effect (expected):

- `ask_api_request_routing_owner` no longer includes `motadata/db-files/report-templates/js/highcharts.js` in `context_bundle.files`.
- `ask_api_request_routing_owner` distractor count reduced (`distractor_count_at_k: 1 -> 0`).
- Stage A pool no longer seeds `db-files` noise rows for this code-oriented ask path.

Interpretation guidance:

- A small ratio shift (for example generic-infra ratio changes caused by top-k size differences) is acceptable when policy bounds still pass and distractor removal improves owner-grounded quality.
