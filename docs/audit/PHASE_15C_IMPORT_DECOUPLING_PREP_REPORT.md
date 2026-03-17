# Phase 15C — Import-Decoupling Prep Report

## 1. Objective

This pass removes the minimum coupling blockers for later containment of retained v15 dataset-construction utilities. It does **not** execute containment. v15 dataset-construction utilities are treated as retained legacy lineage, non-canonical for the forward judgment-based system.

## 2. Accepted baseline

- Phase 15B identified that containment of retained legacy dataset-construction utilities is blocked by import coupling.
- The clearest blocker: `ml/training/src/utils/remove_v15_duplicates.py` importing from `create_v15_balanced_dataset` via an unqualified import that depended on same-directory or cwd-based resolution.
- Phase 15B deferred containment execution until this coupling was removed. Active flows were not to be changed.

## 3. Scope executed

- **Exact files changed:** `ml/training/src/utils/remove_v15_duplicates.py`
- **Exact files inspected but not changed:** `ml/training/src/dataset_creation/create_v15_balanced_dataset.py` (inspected to confirm `classify_example` and `is_valid_example` exist and are used only for the import).
- **Why the changed file was necessary:** The only way to remove the unqualified/same-dir import dependency was to edit `remove_v15_duplicates.py`, which contained the fragile import block. No change to `create_v15_balanced_dataset.py` was required; it already exposes the two functions as module-level symbols.

## 4. Coupling blocker changes completed

| File | Old coupling form | New coupling form | Why safer for later containment |
|------|-------------------|-------------------|----------------------------------|
| `ml/training/src/utils/remove_v15_duplicates.py` | Inside `main()`, when backfilling: `sys.path.insert(0, str(Path(__file__).parent))` then `from create_v15_balanced_dataset import classify_example, is_valid_example` | Inside `main()`, when backfilling: `_repo_root = Path(__file__).resolve().parents[4]`; if not in `sys.path`, `sys.path.insert(0, str(_repo_root))`; then `from ml.training.src.dataset_creation.create_v15_balanced_dataset import classify_example, is_valid_example` | The new form does not depend on `create_v15_balanced_dataset` being in the same directory or on cwd. It uses the repo root and the package path `ml.training.src.dataset_creation.create_v15_balanced_dataset`, so later containment (e.g. moving retained-lineage modules under a dedicated subdir while keeping `ml` on path) can be done without breaking this import, as long as the module remains importable under that package path. |

## 5. Remaining containment blockers

- **Path/location assumptions (documented for later containment):**  
  - `remove_v15_duplicates.py` still uses CWD-relative paths for inputs/outputs: `V15_FILE = Path("evaluation/finetuning/v15_balanced.jsonl")`, `V15_DEDUP_FILE = Path("evaluation/finetuning/v15_balanced_dedup.jsonl")`, and other `evaluation/finetuning/` paths. These assume the script is run from a directory from which `evaluation/finetuning/` exists (e.g. repo root or a parent). A later containment execution pass that moves this script or changes working-dir assumptions must either preserve this contract or switch to a data-root–based path (out of scope for this phase).
- **Blockers intentionally left unchanged:** No other code was changed. The rest of the v15 utility chain (e.g. `create_v15_balanced_dataset.py` path assumptions, other `create_v15_*` scripts) was not modified.
- **Later containment execution pass:** Beyond this phase, a containment execution pass can relocate retained-lineage modules (e.g. under a dedicated `retained_lineage` or `legacy_v15` area) provided the import path `ml.training.src.dataset_creation.create_v15_balanced_dataset` is still resolvable (e.g. by keeping that package structure or by adding a shim). No further decoupling prep is strictly required for this single blocker; any additional path normalization is optional and can be part of containment or a separate path-contract pass.

## 6. Validation performed

- **Import validation:** Confirmed the new import resolves: from repo root, `from ml.training.src.dataset_creation.create_v15_balanced_dataset import classify_example, is_valid_example` runs successfully when repo root is on `sys.path`.
- **Module-load validation:** Ran `python3 ml/training/src/utils/remove_v15_duplicates.py` from repo root. The module loads, `main()` runs, and the backfill branch (which performs the import) executes without `ImportError`. The script later fails with `FileNotFoundError` when writing to `evaluation/finetuning/v15_balanced_dedup.jsonl` because that directory does not exist—this is a pre-existing legacy path assumption, not a regression from the import change.
- **Behavior-preservation validation:** No logic changes were made beyond the import block. The same two symbols `classify_example` and `is_valid_example` are used in the same way after the import.
- **Test results:** No new tests were added. No existing tests were modified. Manual validation only.

## 7. Explicit non-actions

- No files were moved.
- No files were renamed.
- No files were deleted.
- No containment was executed.
- No archive/export was executed.
- No active pipeline was redesigned.

## 8. Recommendation for next pass

**Recommendation: containment execution pass.** The import blocker identified in Phase 15B has been removed. A containment execution pass can now consider relocating retained-lineage v15 dataset-construction utilities (e.g. under a dedicated in-repo area) without this coupling preventing it, as long as the package path `ml.training.src.dataset_creation.create_v15_balanced_dataset` remains valid or is re-established (e.g. via package structure or shim). Optionally, that pass or a separate path-contract pass can address the legacy CWD-relative paths in `remove_v15_duplicates.py` and related utilities.
