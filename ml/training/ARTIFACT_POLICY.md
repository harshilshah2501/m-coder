# Artifact Policy (Stage-6C / Stage-7)

## Purpose
This repository is **control-plane only**. Git stores code, configs, manifests, summaries, and pointers. Large runtime artifacts are stored in the external artifact store.

## Control-plane (Git tracked)
- Source code and configuration files
- Freeze certificates and small JSON manifests
- Small summary markdown reports
- Pointer files referencing artifact-store URIs/paths

## Data-plane (NOT Git tracked)
- Stage-6C ledgers and traces (`stage6c_ledger.jsonl`, `suite_traces.jsonl`)
- Generated plots and large logs
- Checkpoints / model binaries (`*.safetensors`, `*.bin`, `*.pt`, `*.ckpt`, `*.npz`)
- Stage-7 frozen dataset payloads when large

## Artifact Store Layout
Default local root:
`/home/harshil/Harshil-PoCs/m-coder_artifacts`

Structure:
- `stage6c/suites/<suite_id>/...`
- `stage7/freeze/<freeze_id>/...`

## Required Workflow
1. Initialize artifact store:
   - `artifacts init`
2. Run Stage-6C suite as usual.
3. Import outputs into artifact store:
   - `artifacts import-stage6c-run --run-dir <path>`
4. Verify manifest integrity:
   - `artifacts verify-manifest --manifest ml/training/freeze_manifests/stage6c/<suite_id>.manifest.json`
5. Run hygiene gate before commit:
   - `scripts/verify_artifact_hygiene.sh`

## Compliance Rules
- Never commit `ml/training/generated/**` runtime outputs.
- Every imported suite must produce a manifest with SHA256 checksums.
- Keep evaluation logic and freeze gates unchanged; segregation is post-run only.

## Auditability
Each manifest records:
- `suite_id`, `run_count`, `created_at`, `git_commit`
- `config_digest`, `seeds_digest`, `model_id`
- artifact file list with `size_bytes`, `sha256`, and artifact-store paths
