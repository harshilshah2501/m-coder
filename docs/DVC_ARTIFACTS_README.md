# DVC Artifacts — End-to-End Usage (Local Disk)

Git stores only source, config, and DVC pointer files. Large artifacts (checkpoints, datasets, exports) are tracked by DVC and stored on **local disk** for prototype/evaluation. Cloud (R2) is deferred for later.

**No cloud credentials required.** Large binaries are not committed to Git.

## One-time setup (after clone)

```bash
# Install DVC: pip install dvc or snap install dvc
./scripts/setup_dvc_local.sh
```

This creates the canonical storage directory and sets `localstore` as the default remote. Storage path: `/home/harshil/Harshil-PoCs/m-coder_artifacts/dvc`.

Override path via env: `DVC_LOCAL_PATH=/custom/path ./scripts/setup_dvc_local.sh`

## End-to-end workflow

### Push checkpoints

```bash
# Copy run into canonical dir
mkdir -p ml/artifacts/checkpoints/phase08D
cp -r ml/training/pipeline/stage08/checkpoints/phase08D/* ml/artifacts/checkpoints/phase08D/

make dvc-push-checkpoints RUN_ID=phase08D
git add ml/artifacts/checkpoints/phase08D.dvc
git commit -m "DVC: add checkpoint phase08D"
```

### Push dataset freeze

```bash
mkdir -p ml/artifacts/datasets/golden_v1
cp ml/training/pipeline/stage08/dataset/golden_exemplars_v1_conf_patch1.jsonl ml/artifacts/datasets/golden_v1/

make dvc-push-dataset FREEZE_ID=golden_v1
git add ml/artifacts/datasets/golden_v1.dvc
git commit -m "DVC: add dataset golden_v1"
```

### Restore after clone

```bash
git clone <repo-url> m-coder && cd m-coder
./scripts/setup_dvc_local.sh

make dvc-pull-checkpoints RUN_ID=phase08D
make dvc-pull-dataset FREEZE_ID=golden_v1

# Verify
ls -la ml/artifacts/checkpoints/phase08D/
ls -la ml/artifacts/datasets/golden_v1/
```

### Optional: publish to Hugging Face

```bash
export HF_TOKEN=hf_...
python scripts/publish_hf.py \
  --local-dir ml/artifacts/exports/adapter_phase08D \
  --repo-id your-org/m-coder-adapter \
  --private --run-id phase08D --freeze-id golden_v1
```

## Verification

```bash
dvc remote list
ls -la /home/harshil/Harshil-PoCs/m-coder_artifacts/dvc
bash tests/test_dvc_artifacts_acceptance.sh
```

## R2 (deferred)

R2 remote is kept in config but is **inactive**. See [DVC_R2_SETUP.md](DVC_R2_SETUP.md) for future cloud backup.

## See also

- [ml/artifacts/REGISTRY.md](../ml/artifacts/REGISTRY.md) — artifact contracts and naming
