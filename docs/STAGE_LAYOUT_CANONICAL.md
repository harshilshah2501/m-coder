# Pipeline Stage Layout — Canonical Path Reference

This document defines the authoritative mapping between pipeline stages and filesystem paths in the Motadata ML pipeline. Use it for discovery and navigation; no logic has been relocated.

---

## Changelog (Stage Layout Cleanup)

- **2026-03**: Fixed Stage-8 dataset discovery to resolve canonical `ml/training/datasets/sft/` via sentinel-based `get_training_root()`. Added `stage08/_path_utils.py`, tests in `stage08/tests/test_dataset_discovery.py`. Updated phase08→stage08 in docstrings. Added Stage-7 forwarding package `stage7/` for discoverability.


## Stage ↔ Path Table

| Stage | Responsibility | Canonical Path(s) |
|-------|----------------|-------------------|
| **Stage-6A** | Single-step mutation harness (schemas, docs) | `ml/training/pipeline/stage6/stage6a/` |
| **Stage-6B** | Systemic rewrite (placeholder) | `ml/training/pipeline/stage6/stage6b/` |
| **Stage-6C** | Agent-loop mutation harness | `ml/training/pipeline/stage6/stage6c/` |
| **Stage-7 compiler** | Doctrine → JSONL (deterministic) | `ml/training/compiler/compile_stage7.py` |
| **Stage-7 freeze** | Freeze orchestration, manifest, split determinism | `ml/training/pipeline/stage6/stage6c/freeze/` |
| **Stage-8** | SFT training (LoRA, split enforcement) | `ml/training/pipeline/stage08/` |

---

## Stage-7 Discoverability

Stage-7 responsibilities are split across two roots:

- **Compiler**: `ml/training/compiler/` — parses STAGE4_VARIANT_GENERATION.md, produces JSONL.
- **Freeze**: `ml/training/pipeline/stage6/stage6c/freeze/` — orchestration, gates, manifest, split hashes.

The `ml/training/pipeline/stage7/` package provides a forwarding layer for discoverability. It does **not** contain new logic; it only imports and re-exports the canonical implementations.

### Usage

```python
# Prefer direct imports for production:
from compiler.compile_stage7 import compile_doctrine
from stage6.stage6c.freeze import run_freeze, evaluate_freeze_gates

# Or via stage7 forwarding (discoverability):
from stage7 import compile_doctrine, run_freeze, evaluate_freeze_gates
```

---

## Entry Points

| Stage | CLI / Entry Point |
|-------|-------------------|
| Stage-6C smoke | `stage6c-smoke-run` |
| Stage-6C report | `stage6c-report` |
| Stage-6C suite | `stage6c-run-suite` |
| Stage-7 freeze | `stage6c-freeze` |
| Stage-8 train | `train_stage08D.py`, `train.py` |
| Stage-8 split | `enforce_split_stage08D.py` |

---

## Canonical SFT Dataset

- **Path**: `ml/training/datasets/sft/`
- **Frozen files**: `golden_exemplars_v1_frozen.jsonl`, `golden_exemplars_v1_train_frozen.jsonl`, `golden_exemplars_v1_val_frozen.jsonl`

---

## Naming Compatibility (phase* vs stage*)

Directory and import naming are canonical: `stage08/`, `stage6/stage6c/`. Use these in paths and docstrings.

`phase08D` identifiers (e.g. `balanced_base_split_phase08D`, `write_split_stats_phase08D`, log filenames like `phase08D_split_stats.txt`) remain **only for API stability** — they are function names and output filenames, not directory paths or import roots. Do not use `phase08` or `phase08/` as path references in docs or help text.

---

## Stage Layout Sanity Check + Determinism Report (2026-03)

### Step 0 — Sanity check

**Layout verified:**
- Stage-6C root: `ml/training/pipeline/stage6/stage6c/` (import path `stage6.stage6c`)
- Stage-8 root: `ml/training/pipeline/stage08/` (import path `stage08`)
- Compiler root: `ml/training/compiler/` (import path `compiler`)
- `phase6c` references only in report/shim paths (historical)

### Refinement 1 — Stage-7 freeze determinism

Implemented in `stage6/stage6c/freeze/freeze.py`:
- `_stable_row_key`, `_stable_row`, `_canonical_json_bytes` for deterministic hashing
- `corpus_hash` from sorted stable rows; excludes timestamps, paths, volatile fields
- `split_hashes` from sorted stable rows; rows sorted before `balanced_base_split_phase08D`

### Refinement 2 — Stage-8 dataset discovery (CWD-independent)

All entrypoints use `stage08/_path_utils.py:get_canonical_sft_dataset_dir()`:
- `train.py`, `train_stage08D.py`, `enforce_split_stage08D.py` → `discover_dataset_dir()` → canonical resolver
- No hardcoded `parent / "datasets" / "sft"` or similar in entrypoints
- Tests: `test_discover_dataset_dir_cwd_independent`, `test_no_hardcoded_datasets_sft_in_entrypoints`

### Final verification commands

```bash
export PYTHONPATH="$(pwd)/ml/training/pipeline:$(pwd)/ml/training"
python -m pytest ml/training/pipeline/stage08/tests -q
python -m pytest ml/training/pipeline/stage6/stage6c/tests/test_freeze.py -q
python -m pytest ml/training/pipeline/stage6/stage6c/tests -q
```

| Suite | Result |
|-------|--------|
| stage08/tests | 14 passed |
| test_freeze.py (full) | 9 passed, 1 skipped |
| stage6c/tests (full) | 103 passed, 1 skipped |
