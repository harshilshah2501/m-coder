# Asset Index

Datasets, JSONL, checkpoints, logs, and model artifacts. Excludes `.venv/` and package metadata.

---

## JSONL Files

### Phase-6C Harness Outputs

| path | type | role |
|------|------|------|
| ml/training/src/sources/Motadata/phase6/phase6c/out/smoke_traces.jsonl | trace | intermediate |
| ml/training/src/sources/Motadata/phase6/phase6c/out_m3/smoke_traces.jsonl | trace | intermediate |
| ml/training/src/sources/Motadata/phase6/phase6c/out_m4/smoke_traces.jsonl | trace | intermediate |
| ml/training/src/sources/Motadata/phase6/phase6c/out_m4/phase6c_ledger.jsonl | ledger | output |

### SFT / Training Datasets

| path | type | role |
|------|------|------|
| ml/training/phase08/datasets/sft/*.jsonl | dataset | input/frozen |
| ml/training/data/processed/*.jsonl | dataset | processed |
| ml/datasets/v16_*/train.jsonl, val.jsonl, test.jsonl | dataset | input |
| ml/datasets/v17_*.jsonl | dataset | input |
| ml/datasets/generation/*.jsonl | dataset | generated |
| ml/datasets/cpt/*.jsonl | dataset | CPT chunks |

**Approx. count:** 42 JSONL files across these directories.

---

## Logs

| path | type |
|------|------|
| .cursor/debug-*.log | debug |
| ml/training/.../src/test/resources/log_reduce.log | test resource |

---

## Checkpoints / Model Artifacts

- **No `.ckpt`**, **`.pt`**, **`.safetensors`** files found in indexed scope.
- Model artifacts may live under `ml/training/phase08/training/` or external storage.

---

## Size Totals per Directory (Approximate)

| directory | asset_types | file_count | size_note |
|-----------|-------------|------------|-----------|
| ml/datasets/ | jsonl | ~30 | datasets, DPO pairs, v16/v17 |
| ml/training/phase08/datasets/sft/ | jsonl | 4 | frozen SFT splits |
| ml/training/src/.../phase6/phase6c/out*/ | jsonl | 4 | traces, ledger |
| ml/training/data/processed/ | jsonl | 2 | processed training data |
| ml/datasets/cpt/ | jsonl | 2 | CPT dataset |
| ml/datasets/generation/ | jsonl | 3 | generated datasets |

---

## Dataset / Artifact Directories

- `datasets/` — top-level datasets
- `ml/datasets/` — ML-specific datasets (v16, v17, CPT, generation)
- `ml/training/phase08/datasets/` — Phase-08 SFT datasets
- `ml/training/artifacts/` — training artifacts
- `ml/training/data/processed/` — processed data
- `ml/training/results/` — training results
