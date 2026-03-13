## 1) Architecture summary (Phase 1, plan only)

- Keep Stage-6C compute behavior unchanged; add a storage segregation layer after run completion.
- Treat the repo as control-plane: code, configs, manifests, certificates, summaries, and artifact pointers only.
- Treat artifact store as data-plane: ledgers, traces, plots, checkpoints, large JSONL/NPZ/binaries.
- Default backend is local filesystem root at `/home/harshil/Harshil-PoCs/m-coder_artifacts`.
- Backend abstraction supports later S3/MinIO by config + env vars (no logic rewrite).
- Each imported suite gets immutable manifest with sha256 for key files and deterministic metadata (commit, digests, model_id, expected counts).
- Stage-6C suite output remains compatible with existing tests; segregation initially via post-run import command.
- Optional minimal hook can be added in `ml/training/pipeline/stage6/stage6c/orchestrator/cli.py` after execute/report, not inside per-run write loop.
- Freeze outputs remain auditable through manifest + certificate + small summary in repo.
- Enforcement uses `.gitignore` + hygiene script to fail if forbidden large artifacts are tracked.
- Existing entrypoints remain intact from `ml/training/pipeline/stage6/pyproject.toml`.

## 2) Folder conventions (tree)

**Repo (Git tracked)**
- `ml/training/artifacts/artifact_store.yaml`
- `ml/training/ARTIFACT_POLICY.md`
- `ml/training/freeze_manifests/stage6c/`
  - `<run_id>.manifest.json`
  - `<run_id>.summary.md`
  - `<run_id>.pointer.json`
- `ml/training/freeze_manifests/stage6c/index.jsonl`
- `scripts/verify_artifact_hygiene.sh`

**Artifact store (not tracked by Git)**
- `/home/harshil/Harshil-PoCs/m-coder_artifacts/`
  - `stage6c/suites/<suite_id>/`
    - `stage6c_ledger.jsonl`
    - `suite_traces.jsonl`
    - `plots/...`
  - `stage7/freeze/<freeze_id>/`
    - `golden_exemplars_v1.jsonl`
    - `freeze_manifest.json`
  - `models/checkpoints/...`
  - `datasets/...`
  - `manifests/mirror/stage6c/<suite_id>.manifest.json` (optional mirror copy)

## 3) Manifest JSON example

```json
{
  "schema_version": "stage6c-artifact-manifest/v1",
  "suite_id": "canonical_20260305_104233",
  "run_count": 80,
  "created_at": "2026-03-05T10:12:33Z",
  "git_commit": "f17a104",
  "suite": "canonical",
  "config_path": "ml/training/pipeline/stage6/stage6c/config/gating_config.yaml",
  "config_digest": "8f72916bae2465de",
  "seeds_digest": "c0fab47a3180e714",
  "model_id": "qwen2.5-14b-instruct|vllm|bf16|max=512|lora=checkpoint-38",
  "expected_counts": {
    "planned_runs": 80,
    "executed_runs": 80,
    "trace_rows": 80,
    "ledger_rows": 80
  },
  "artifact_backend": {
    "kind": "local",
    "root_uri": "file:///home/harshil/Harshil-PoCs/m-coder_artifacts",
    "bucket": null,
    "prefix": null
  },
  "files": [
    {
      "logical_name": "stage6c_ledger",
      "artifact_relpath": "stage6c/suites/canonical_20260305_104233/stage6c_ledger.jsonl",
      "repo_pointer": "ml/training/freeze_manifests/stage6c/canonical_20260305_104233.pointer.json",
      "size_bytes": 7932,
      "sha256": "abc123...",
      "media_type": "application/x-ndjson"
    },
    {
      "logical_name": "suite_traces",
      "artifact_relpath": "stage6c/suites/canonical_20260305_104233/suite_traces.jsonl",
      "repo_pointer": "ml/training/freeze_manifests/stage6c/canonical_20260305_104233.pointer.json",
      "size_bytes": 106457,
      "sha256": "def456...",
      "media_type": "application/x-ndjson"
    },
    {
      "logical_name": "stage7_golden_exemplars",
      "artifact_relpath": "stage7/freeze/freeze_20260305_111045/golden_exemplars_v1.jsonl",
      "repo_pointer": "ml/training/freeze_manifests/stage6c/canonical_20260305_104233.pointer.json",
      "size_bytes": 245901,
      "sha256": "789abc...",
      "media_type": "application/x-ndjson"
    },
    {
      "logical_name": "stage7_freeze_manifest",
      "artifact_relpath": "stage7/freeze/freeze_20260305_111045/freeze_manifest.json",
      "repo_pointer": "ml/training/freeze_manifests/stage6c/canonical_20260305_104233.pointer.json",
      "size_bytes": 2812,
      "sha256": "ff1122...",
      "media_type": "application/json"
    }
  ],
  "freeze_certificate_ref": "ml/training/pipeline/FREEZE_CERTIFICATE_v1.json",
  "notes": "Post-run import completed; large artifacts removed from repo paths."
}
```

## 4) Verification commands

- Git cleanliness:
  - `git status --short`
- Ensure forbidden patterns are untracked:
  - `git ls-files | rg 'ml/training/generated/|suite_traces.*\\.jsonl|stage6c_ledger.*\\.jsonl|\\.safetensors$|\\.bin$|\\.pt$|\\.ckpt$|\\.npz$'`
- Size guard on tracked files:
  - `git ls-files -z | xargs -0 -I{} bash -lc 's=$(stat -c%s "{}" ); [ $s -gt 10485760 ] && echo "$s {}"'`
- Manifest checksum validation:
  - `python -m stage6.stage6c.artifacts.cli artifacts verify-manifest --manifest ml/training/freeze_manifests/stage6c/<run_id>.manifest.json`
- Assert ledger/traces are artifact-store only:
  - `test ! -f ml/training/generated/stage6c_runs/<run_dir>/stage6c_ledger.jsonl`
  - `test ! -f ml/training/generated/stage6c_runs/<run_dir>/suite_traces.jsonl`

## 5) Migration steps for existing runs

1. Inventory existing suite directories under `ml/training/generated/stage6c_runs`.
2. For each suite directory, execute `artifacts import-stage6c-run --run-dir <path>` (treating each run-dir as one suite artifact package).
3. Import command computes sha256, writes:
  - manifest JSON + summary MD + pointer JSON under `ml/training/freeze_manifests/stage6c`
  - Stage-6C artifacts into `stage6c/suites/<suite_id>/...`
  - Stage-7 freeze artifacts into `stage7/freeze/<freeze_id>/...`
4. Append/update index file at `ml/training/freeze_manifests/stage6c/index.jsonl`.
5. Remove or archive large files from repo working tree path (keep only tiny pointer/summary/manifest).
6. Run hygiene verification script and commit only control-plane files.
7. Ensure freeze outputs in `ml/training/sft/stage7` are migrated to artifact store and replaced by pointers/manifests in repo.

## 6) Risks + mitigations

- **Risk:** Breaking current Stage-6C tests by changing executor write paths.
  - **Mitigation:** Phase 2 starts with standalone import command; no gate/eval path changes.
- **Risk:** Manifest drift / non-deterministic metadata.
  - **Mitigation:** fixed schema version, sorted file lists, explicit sha256, commit pinning.
- **Risk:** Developers accidentally commit large files.
  - **Mitigation:** strict `.gitignore` rules + failing `scripts/verify_artifact_hygiene.sh`.
- **Risk:** Local artifact root unavailable.
  - **Mitigation:** `artifacts init` preflight with writable check and clear error.
- **Risk:** Future S3 migration friction.
  - **Mitigation:** backend interface now (`local` default), env-driven S3 fields in config from day one.
- **Risk:** Duplicate artifact copies (repo + store) during migration.
  - **Mitigation:** import command supports `--move` mode after checksum success.

If approved, Phase 2 will follow the requested commit order exactly: `.gitignore + policy`, then artifacts module/CLI, then verify script, then minimal Stage-6C integration hook, then verification outputs.
