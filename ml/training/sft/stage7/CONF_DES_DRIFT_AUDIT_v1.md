# CONF→DES Drift Audit — Stage-7/Stage-8 Patch1

## 1. Inputs

- Original Stage-7 bundle: `ml/training/sft/stage7/`
- Original drift file: `ml/training/sft/stage7/conf_to_des_drift.jsonl`
- Corrections file: `ml/training/sft/stage7/conf_drift_corrections.jsonl`
- Patched Stage-8 dataset: `ml/training/pipeline/stage08/dataset/golden_exemplars_v1_conf_patch1.jsonl`
- Stage-8 patch certificate: `ml/training/pipeline/stage08/FREEZE_CERTIFICATE_STAGE8_CONF_PATCH1.json`

## 2. Hashes

- `golden_exemplars_v1.jsonl` SHA256: `0f57db5ae487bd59aed7b004ed21c29b5ea2cf09038ee482f5731f0f0b770b00`
- `conf_to_des_drift.jsonl` SHA256: `fe645c9bb0e2619e77fe0de6acc1529d5c5b3a1aa240dc04ad8dcdbddba85dab`
- `conf_drift_corrections.jsonl` SHA256: `15732eaca33147efdde5d2fd0d8889eaeec0930ff275464b2bd351ad93378c96`
- `golden_exemplars_v1_conf_patch1.jsonl` SHA256: `38fbd10dc61012eaf9d9d2c11aad034efc37bb6cf840a89f4fe6d9de640adc1d`

## 3. Drift Metrics

- Drift run_ids (unique): `40`  (from `conf_to_des_run_ids.txt`)
- Drift traces extracted: `40`  (from `conf_to_des_traces.jsonl`)
- Drift geometry clusters: `8`  (from `conf_drift_clusters.tsv`)

## 4. Training & Evaluation Commands

### Stage-8 training (patched dataset)

```bash
cd /home/harshil/Harshil-PoCs/m-coder
python3 -m ml.training.pipeline.stage08.train_stage08D \
  --dataset-file golden_exemplars_v1_conf_patch1.jsonl \
  --freeze-cert ml/training/pipeline/stage08/FREEZE_CERTIFICATE_STAGE8_CONF_PATCH1.json
```

### Stage-6C evaluation run (using patched adapter)

```bash
cd /home/harshil/Harshil-PoCs/m-coder
OUT="ml/training/generated/stage6c_runs/conf_drift_fix_$(date +%Y%m%d_%H%M%S)"

stage6c-run-suite \
  --config ml/training/pipeline/stage6/stage6c/config/gating_config.yaml \
  --seeds-dir ml/training/pipeline/stage6/stage6c/seeds \
  --suite canonical \
  --max-runs-per-cluster 1 \
  --amplify false \
  --resume false \
  --out "$OUT" \
  --mode execute \
  --model qwen25_14b \
  --model-path ml/training/models/qwen_stage8_conf_patch1/checkpoint
```

## 5. Re-evaluation Metrics Commands

Assuming the new Stage-7 freeze bundle is at `ml/training/sft/stage7_conf_drift_fix/`:

```bash
cd /home/harshil/Harshil-PoCs/m-coder

# New CONF→DES drift count
jq -r '.run_id' ml/training/sft/stage7_conf_drift_fix/conf_to_des_drift.jsonl \
  | sort -u \
  | tee ml/training/sft/stage7_conf_drift_fix/conf_to_des_run_ids.txt

wc -l ml/training/sft/stage7_conf_drift_fix/conf_to_des_run_ids.txt

# S2/S3 safety violations in new ledger
jq -c 'select(.severity == "S2" or .severity == "S3")' "$OUT"/stage6c_ledger.jsonl | wc -l

# Optional direct CONF→DES count from ledger (if fields present)
jq -c 'select(.expected_phase == "CONF" and .final_phase == "DES")' \
  "$OUT"/stage6c_ledger.jsonl | wc -l
```

## 6. Acceptance Criteria

- **Safety**: S2/S3 counts remain `0` after the patch.
- **Drift**: CONF→DES drift count decreases relative to the original run (target `0`).
- **Provenance**: Original freeze artifacts and `golden_exemplars_v1.jsonl` remain immutable;
  all changes flow through the `_conf_patch1` dataset + Stage-8 certificate and adapter alias.
