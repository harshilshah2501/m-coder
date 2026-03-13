# Artifact Registry (DVC + Local Disk)

This directory holds **versioned artifact contracts** and canonical paths for checkpoints, datasets, and exports. Git stores only metadata and DVC pointer files; large files are stored on **local disk** via DVC (prototype/evaluation stage). Cloud (R2) is deferred.

**Large binaries are not committed to Git.**

## Directory layout

| Path | Purpose |
|------|---------|
| `checkpoints/<run_id>/` | Training run checkpoints (e.g. LoRA adapter snapshots). One DVC-tracked dir per `run_id`. |
| `datasets/<freeze_id>/` | Frozen dataset snapshots (e.g. golden exemplars, train/val splits). One DVC-tracked dir per `freeze_id`. |
| `exports/<model_id>/` | Blessed model exports (adapter-only or merged). One DVC-tracked dir per `model_id`. |

## Naming conventions

- **run_id**: e.g. `phase08D`, `stage08_lora_20260306`
- **freeze_id**: e.g. `golden_v1_conf_patch1`, `stage8_freeze_20260306`
- **model_id**: e.g. `qwen_stage8_conf_patch1`, `adapter_phase08D`

## Governed runtime phases

REF and CONF are **governed runtime phases** — final REF/CONF outputs are policy-rendered and policy-scored, not free-generation. DES and CODE remain model-expressive. This doctrine was adopted after CONF→DES drift remained unresolved under SFT-only attempts; deterministic CONF rendering in Stage-6C achieved the cure (Patch-2: severity 80 S0, CONF→DES 0, S2/S3 0).

## Artifact contracts

### Checkpoints (`checkpoints/<run_id>/`)

- Contains: `checkpoint-*/` with `adapter_config.json`, `adapter_model.safetensors`, etc.
- Track: `make dvc-push-checkpoints RUN_ID=<run_id>` then commit the `.dvc` file.

### Datasets (`datasets/<freeze_id>/`)

- Contains: `.jsonl` data files, optional `manifest.json`.
- Track: `make dvc-push-dataset FREEZE_ID=<freeze_id>` then commit the `.dvc` file.

### Exports (`exports/<model_id>/`)

- Contains: merged or adapter-only weights. Optional: `scripts/publish_hf.py`.

## Commands

```bash
# Setup (one-time)
./scripts/setup_dvc_local.sh

# Push / Pull
make dvc-push-checkpoints RUN_ID=phase08D
make dvc-pull-checkpoints RUN_ID=phase08D
make dvc-push-dataset FREEZE_ID=golden_v1
make dvc-pull-dataset FREEZE_ID=golden_v1

# Verify
ls -la ml/artifacts/checkpoints/phase08D/
sha256sum ml/artifacts/checkpoints/phase08D/checkpoint-*/*.safetensors 2>/dev/null
```

## See also

- [docs/DVC_ARTIFACTS_README.md](../../docs/DVC_ARTIFACTS_README.md) — setup and end-to-end usage
- [docs/DVC_R2_SETUP.md](../../docs/DVC_R2_SETUP.md) — R2 (deferred)
