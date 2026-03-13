Day-2 Workflow: Stage-6C Artifact Segregation
============================================

## Control-plane vs data-plane

- **Repo (control-plane)**: Only stores configuration, manifests, pointers, and human-readable summaries. **No large artifacts, traces, or run outputs live in git.**
- **Artifact store (data-plane)**: Stores all heavy, mutable, or time-series data for Stage-6C runs (ledgers, traces, exemplars, freeze manifests, etc.).
- **Separation rule**: If it is needed to *reconstruct or audit* a Stage-6C run, but is large and/or run-specific, it belongs in the artifact store, not in the repo.

## Fresh run + import workflow

Run this from the repo root (or wherever your project expects), adjusting env vars as needed.

```bash
# 1) Launch a Stage-6C suite run
export MODEL="gpt4.1-mini"
export SEEDS="0,1,2"
export CFG="configs/stage6c/default.yml"
export OUT="runs/stage6c/$(date +%Y%m%d-%H%M%S)"

stage6c-run-suite \
  --model "$MODEL" \
  --seeds "$SEEDS" \
  --config "$CFG" \
  --out-dir "$OUT"

# 2) Initialize artifact store (idempotent; safe to re-run)
artifacts init

# 3) Import this Stage-6C run into the artifact store
artifacts import-stage6c-run --run-dir "$OUT"

# 4) Verify the freeze manifest that was produced during import
# Replace <path> with the actual manifest path if your layout differs.
artifacts verify-manifest --manifest "$OUT/freeze_manifest.json"

# 5) Enforce artifact hygiene (repo vs artifact-store segregation)
scripts/verify_artifact_hygiene.sh
```

## Expected files after a clean run

### In git (control-plane only)

Only lightweight coordination artifacts should ever be committed:

- **Manifests / pointers / summaries**:
  - `freeze_manifest.json` (or a relocated copy under a tracked `manifests/` tree)
  - Any **pointer files** that reference artifact-store locations (paths, URIs, IDs)
  - Human-readable **summary/README** files that describe the run and how to rehydrate it

No `.jsonl` ledgers, traces, or exemplar payloads belong in git.

### In the artifact store (data-plane)

For each imported Stage-6C run, expect (names may be scoped by run-id or directory layout):

- `stage6c_ledger.jsonl`
- `suite_traces.jsonl`
- `freeze_manifest.json`
- `golden_exemplars_v1.jsonl`

These should reside under the configured artifact-store root (e.g., an object store bucket or on-prem artifact volume), **not** under tracked git directories.

## Troubleshooting

### `scripts/verify_artifact_hygiene.sh` fails

- **Symptom**: Script reports disallowed files under tracked git paths (e.g., `.jsonl` ledgers or traces in `ml/training/...`).
- **Actions**:
  - Move the offending files out of the repo tree into the artifact store (or delete them if they are disposable scratch).
  - Ensure any needed references back into those artifacts are represented as small pointer/manifest files that *are* safe to commit.
  - Re-run `scripts/verify_artifact_hygiene.sh` until it passes.

### `artifacts verify-manifest` fails

- **Symptom**: `verify-manifest` reports missing blobs, mismatched checksums, or inconsistent paths.
- **Actions**:
  - Confirm the `--manifest` path is correct and points to the freeze manifest produced by the latest import.
  - Check that the artifact store is reachable (correct bucket, volume, credentials, and permissions).
  - If only a subset of artifacts is missing, re-run `artifacts import-stage6c-run --run-dir "$OUT"` to repair the run and regenerate or update the manifest.
  - If corruption is suspected, invalidate the bad run in your higher-level registry and re-run Stage-6C from scratch.

## CI usage

- **When manifests or pointer files change**, CI should:
  - Run `scripts/verify_artifact_hygiene.sh` to ensure no data-plane files leaked into git.
  - Run `artifacts verify-manifest --manifest <path>` for any modified or newly added manifests to ensure the artifact store is consistent.
