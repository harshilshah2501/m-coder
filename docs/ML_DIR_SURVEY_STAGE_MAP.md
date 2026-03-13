# ML Directory Survey + Stage Taxonomy Verification

**Time of audit:** 2026-03-02T10:19:17+00:00

---

## 1) Environment + Tree Snapshots

### pwd

```
/home/harshil/Harshil-PoCs/m-coder
```

### ls -la (repo root)

```
total 156
drwxrwxr-x 12 harshil harshil  4096 Mar  2 07:41 .
drwxrwxr-x  4 harshil harshil  4096 Mar  2 07:55 ..
drwxrwxr-x  8 harshil harshil  4096 Mar  2 06:55 .git
-rw-rw-r--  1 harshil harshil  1004 Mar  2 09:19 .gitignore
...
drwxrwxr-x  7 harshil harshil  4096 Mar  2 06:55 ml
...
```

### tree -L 4 ml

```
ml
├── README.md
├── datasets
│   ├── cpt/
│   ├── generation/
│   ├── tools/
│   ├── v16_1_fixed/
│   ├── v16_2/
│   └── v17_* ...
├── evaluation
│   ├── analysis/
│   ├── diffs/
│   ├── reports/
│   └── results/
├── lineage
│   ├── schemas/
│   └── tests/
├── scripts
│   └── prepare_exemplars.sh
└── training
    ├── compiler/
    ├── data/
    ├── datasets/
    ├── pipeline/
    ├── sft/
    ├── src/
    └── ...
```

### tree -L 6 ml/training (key modules)

```
ml/training
├── ARCHITECTURE_LOCK_v2.md
├── compiler/
│   ├── compile_stage7.py
│   ├── freeze_manifest_schema.json
│   └── tests/
├── datasets/
│   └── sft/
│       ├── golden_exemplars_v1_frozen.jsonl
│       ├── golden_exemplars_v1_train_frozen.jsonl
│       └── golden_exemplars_v1_val_frozen.jsonl
├── pipeline/
│   ├── STAGE1_*.md .. STAGE6*.md
│   ├── stage08/
│   │   ├── _path_utils.py
│   │   ├── enforce_split_stage08D.py
│   │   ├── train.py
│   │   ├── train_stage08D.py
│   │   └── tests/
│   ├── stage6/
│   │   ├── stage6a/
│   │   ├── stage6b/
│   │   ├── stage6c/
│   │   └── stage6c_report/
│   └── stage7/
│       ├── __init__.py
│       └── cli.py
├── sft/
├── src/
│   ├── data/
│   ├── dataset_creation/
│   ├── evaluation/
│   ├── finetuning/
│   └── utils/
└── train_cpt.py
```

### Python file counts

```
find ml -name "*.py" -not -path "*/__pycache__/*" | wc -l
1246

find ml/training -name "*.py" -not -path "*/__pycache__/*" | wc -l
1220
```

### Python version

```
3.12.3 (main, Jan 22 2026, 20:57:42) [GCC 13.3.0]
```

### Top-level directory purpose

- **ml/datasets/** — Dataset specs, generation scripts, DPO pairs, versioned artifacts (v15–v17, cpt). Evidence: `ml/README.md` ("dataset specifications, generation scripts, and versioned dataset artifacts").
- **ml/evaluation/** — Model evaluation, benchmarks, KPI tests, phase_c probes, reports. Evidence: tree shows `comprehensive_model_evaluation.py`, `phase_c_completion_probe.py`, `reports/`, `results/`.
- **ml/lineage/** — Compilation DAG and provenance schemas (freeze manifest, lineage node). Evidence: `ml/README.md`; `ml/lineage/schemas/` contains `freeze.manifest.v0.1.schema.json`, `lineage.index.v0.1.schema.json`.
- **ml/scripts/** — Shared ML utility scripts. Evidence: `ml/scripts/prepare_exemplars.sh`; `ml/README.md` ("shared ML-related utility and CI scripts").
- **ml/training/** — Training, finetuning, pipeline (stage6, stage08), compiler, SFT exemplars. Evidence: `ml/README.md`; tree shows `pipeline/`, `compiler/`, `sft/`, `src/finetuning/`.

---

## 2) Stage ↔ Path Mapping Table

| Stage | Expected responsibility | Current implemented path(s) | Entry points / CLIs | Docs that define it | Status | Mismatch notes | Evidence |
|-------|------------------------|-----------------------------|----------------------|---------------------|--------|----------------|----------|
| Stage-1 | Structural mapping | — | — | `ml/training/pipeline/STAGE1_STRUCTURAL_MAPPING.md`, `STAGE1A_BOUNDARY_DETECTION.md` | docs-only | No executable code | tree ml/training; rg STAGE1 ml |
| Stage-2 | Artifact extraction | — | — | `ml/training/pipeline/STAGE2_ARTIFACT_EXTRACTION.md` | docs-only | No executable code | tree ml/training; rg STAGE2 ml |
| Stage-3 | Motadata base exemplar mapping | — | — | `ml/training/pipeline/STAGE3_BASE_EXEMPLAR_MAPPING.md` | docs-only | No executable code | tree ml/training |
| Stage-4 | Variant generation | — (compiler consumes) | — | `ml/training/pipeline/STAGE4_VARIANT_GENERATION.md` | docs-only | Doctrine input; `compile_stage7` parses it | rg compile_stage7 ml; compiler/README |
| Stage-5 | Variant stability gate | — | — | `ml/training/pipeline/STAGE5_VARIANT_STABILITY_REPORT.md` | docs-only | No executable code | tree ml/training |
| Stage-6A | Single-step mutation harness | `ml/training/pipeline/stage6/stage6a/` | — | `stage6a/README.md`, `PHASE6_DATASET_FREEZE_CHECKLIST.md`, `STAGE6_DIRECTORY_LAYOUT.md` | placeholder | Schemas, docs; 0 .py files | `find stage6a -name "*.py" | wc -l` → 0; tree stage6a |
| Stage-6B | Systemic hardening rewrite | `ml/training/pipeline/stage6/stage6b/` | — | `stage6b/README.md`, `STAGE6B_COLLAPSE_TAXONOMY.md`, `STAGE6B_PHASE_HARDENING_SPEC.md`, `STAGE6B_REWRITE_CHANGELOG.md` | placeholder | README only; 0 .py | `find stage6b -name "*.py" | wc -l` → 0; stage6b/README: "placeholder" |
| Stage-6C | Agent-loop mutation harness | `ml/training/pipeline/stage6/stage6c/` | `stage6c-smoke-run`, `stage6c-report`, `stage6c-run-suite`, `stage6c-freeze` | `STAGE6C_DESIGN_SPEC_V1.1.md`, mutation/*.md | implemented | — | rg Stage-6C ml; pyproject.toml lines 17–20 |
| Stage-7 | Dataset compilation (freeze/manifest/splits) | `ml/training/compiler/compile_stage7.py` (doctrine→JSONL); `ml/training/pipeline/stage6/stage6c/freeze/` (orchestration) | `stage6c-freeze` (freeze CLI) | `COMPILER_PARSING_CONTRACT_v1.0.md`, `freeze_manifest_schema.json`, `docs/STAGE_LAYOUT_CANONICAL.md` | implemented | Split across compiler/ and stage6c/freeze/ | freeze.py:176-177 (compile_stage7, enforce_split); freeze/cli.py:1 |
| Stage-8 | SFT training | `ml/training/pipeline/stage08/` | `train_stage08D.py`, `train.py`, `enforce_split_stage08D.py` | stage08/__init__.py | implemented | Internal naming uses `phase08D` in function/log file names | stage08/__init__.py:1; train_stage08D.py:275, 352 |

---

## 3) Import Roots + PYTHONPATH Reality Check

### rg -n "PYTHONPATH|stage6\.stage6c|stage08\.|compile_stage7|phase6c" ml/training -S

```
ml/training/scripts/test_stage6c.sh
7:export PYTHONPATH="$REPO_ROOT/ml/training/pipeline:$REPO_ROOT/ml/training"

ml/training/pipeline/stage7/__init__.py
14:    from compiler.compile_stage7 import compile_doctrine
20:    from stage6.stage6c.freeze import (

ml/training/pipeline/stage6/stage6c/freeze/freeze.py
176:    from compiler.compile_stage7 import compile_doctrine
177:    from stage08.enforce_split_stage08D import VALID_PHASES, balanced_base_split_phase08D

ml/training/pipeline/stage6/stage6c/tests/test_freeze.py
11:from stage6.stage6c.freeze import evaluate_freeze_gates, run_freeze
227:    from compiler.compile_stage7 import compile_doctrine

ml/training/pipeline/stage6/pyproject.toml
17:stage6c-smoke-run = "stage6.stage6c.cli.main:main"
...
20:stage6c-freeze = "stage6.stage6c.freeze.cli:main"
```

### rg -n "phase6c|stage6c|stage6\.stage6c|stage08|phase08" ml -S (excerpt)

```
ml/training/pipeline/stage6/stage6c_report/summary.json
2:  "ledger_path": "/root/m-coder/ml/training/src/sources/Motadata/phase6/phase6c/out_m4/phase6c_ledger.jsonl"

ml/training/pipeline/stage6/stage6c_report/Stage6C_Report.md
4:- **Input ledger**: `/root/m-coder/ml/training/src/sources/Motadata/phase6/phase6c/out_m4/phase6c_ledger.jsonl`

ml/training/pipeline/stage08/enforce_split_stage08D.py
110:        out = SCRIPT_DIR / "logs" / "phase08D_split_stats_enforced.txt"
129:def balanced_base_split_phase08D(records):
```

### Actual import roots

| Root | Path (relative to PYTHONPATH entry) | Used by |
|------|-------------------------------------|---------|
| `stage6` | `ml/training/pipeline/` | stage6c tests, freeze (as `stage6.stage6c.*`) |
| `stage08` | `ml/training/pipeline/` | freeze (imports `stage08.enforce_split_stage08D`) |
| `compiler` | `ml/training/` | freeze, test_freeze, stage7 __init__ |

### Forwarding / shim packages

| Package | Forwards to | Evidence |
|---------|-------------|----------|
| `stage7` | `compiler.compile_stage7.compile_doctrine`, `stage6.stage6c.freeze` (run_freeze, evaluate_freeze_gates) | stage7/__init__.py:14,20; stage7/cli.py:10 |

### How to run (evidence-based)

```bash
# From repo root
export PYTHONPATH="$(pwd)/ml/training/pipeline:$(pwd)/ml/training"

# Stage-6C tests
python -m pytest ml/training/pipeline/stage6/stage6c/tests -v

# Stage-08 tests
python -m pytest ml/training/pipeline/stage08/tests -v

# Or use the script
ml/training/scripts/test_stage6c.sh
```

Evidence: `ml/training/scripts/test_stage6c.sh` lines 7–9.

---

## 4) Stage-7 + Stage-8 Wiring Trace

### Stage-7 (freeze/compile/manifest/splits)

- **Freeze orchestration entrypoint:** `stage6.stage6c.freeze.cli:main` (stage6c-freeze)  
  Evidence: `ml/training/pipeline/stage6/pyproject.toml:20`

- **freeze.py → compile_stage7:**  
  `stage6/stage6c/freeze/freeze.py` line 176: `from compiler.compile_stage7 import compile_doctrine`  
  Called inside `run_freeze()` for doctrine→JSONL.

- **Manifest schema:**  
  `ml/training/compiler/freeze_manifest_schema.json` — `"title": "Stage-7 Freeze Manifest"`  
  Referenced in `freeze.py` (writes `stage7_freeze_manifest.json`).

- **Split determinism:**  
  `stage08/enforce_split_stage08D.py` exports `balanced_base_split_phase08D`.  
  `freeze.py:177` imports it; line 285 calls it for deterministic train/val split.

**Wiring:**

```
stage6c-freeze (cli) → stage6.stage6c.freeze.run_freeze
  → compiler.compile_stage7.compile_doctrine (freeze.py:176)
  → stage08.enforce_split_stage08D.balanced_base_split_phase08D (freeze.py:177,285)
  → manifest schema: compiler/freeze_manifest_schema.json
```

### Stage-8 (training)

- **Entrypoints:** `train_stage08D.py`, `train.py`, `enforce_split_stage08D.py`  
  Evidence: tree; `stage08/__init__.py:1`

- **Dataset discovery:** `discover_dataset_dir()` in `train.py`, `train_stage08D.py`, `enforce_split_stage08D.py`  
  Uses `get_canonical_sft_dataset_dir()` from `_path_utils.py`  
  Evidence: `ml/training/pipeline/stage08/_path_utils.py:36-37` → `get_training_root() / "datasets" / "sft"`

- **Expected vs actual dataset dir:**  
  - Expected (canonical): `ml/training/datasets/sft/`  
  - Actual: exists with `golden_exemplars_v1_frozen.jsonl`, `golden_exemplars_v1_train_frozen.jsonl`, `golden_exemplars_v1_val_frozen.jsonl`  
  Evidence: `ls ml/training/datasets/sft/*.jsonl`; `test_dataset_discovery.py`; `_path_utils.py:37`

---

## 5) Known Mismatches + Risks

| # | Mismatch | Impact | How to detect | Minimal fix suggestion |
|---|----------|--------|---------------|------------------------|
| 1 | Phase08 vs stage08 naming | Log files, function names use `phase08D`; directory is `stage08` | `rg "phase08" ml/training` | (docs-only) Note in STAGE_LAYOUT_CANONICAL.md that `phase08D` is retained for API stability |
| 2 | Stage-7 split across two roots | Compiler in `compiler/`, freeze in `stage6c/freeze/` | No single `stage7/` implementation dir | (docs-only) Already documented in STAGE_LAYOUT_CANONICAL.md; stage7/ is forwarding-only |
| 3 | Stale absolute paths in reports | `stage6c_report/summary.json` and `Stage6C_Report.md` contain `/root/m-coder/.../phase6/phase6c/...` | `rg "/root/" ml/training` | (small code patch) Render ledger path as repo-relative in `render.py` when writing reports |
| 4 | stage6a, stage6b have no .py | Only schemas/docs; no harness implementation | `find stage6a stage6b -name "*.py"` → 0 | (docs-only) Mark as placeholder in survey |

---

## 6) Minimal Reconciliation Plan (NO code changes)

1. **(docs-only)** Add "Time of audit" to future surveys for reproducibility.
2. **(docs-only)** Add note in STAGE_LAYOUT_CANONICAL.md that `phase08D` in function/log names is retained for API stability; directory is `stage08`.
3. **(small code patch)** In `reporting/render.py`, optionally render `ledger_path` as repo-relative when writing summary.json and Stage6C_Report.md.
4. **(docs-only)** Add a single source-of-truth pointer: `docs/STAGE_LAYOUT_CANONICAL.md` and `docs/ML_DIR_SURVEY_STAGE_MAP.md` both describe layout; link between them.
5. **(structural move)** Do not move Stage-7 logic; current split (compiler + freeze) is documented and functional.

---

## Verdict

**The directory layout does not fully match the taxonomy.** Divergences:

1. **Stages 1–5:** Implemented only as docs/specs under `ml/training/pipeline/`; no executable code (docs-only).
2. **Stage-6A, 6B:** Placeholder dirs with schemas/docs only; no mutation harness code.
3. **Stage-7:** Responsibilities are split: doctrine→JSONL in `compiler/`, freeze orchestration in `stage6c/freeze/`; no single `stage7/` implementation directory (stage7/ is forwarding-only).
4. **Stage-8:** Uses `phase08D` in function names and log paths while the directory is `stage08` (naming drift).
5. **Legacy paths:** `stage6c_report/summary.json` and `Stage6C_Report.md` contain absolute paths (`/root/m-coder/.../phase6/phase6c/...`) that no longer exist. Evidence: `rg "ledger_path" ml/training/pipeline/stage6/stage6c_report/` and `rg "/root/" ml`.
