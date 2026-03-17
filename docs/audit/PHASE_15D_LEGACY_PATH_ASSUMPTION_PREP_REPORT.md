# Phase 15D — Legacy Path-Assumption Prep Report

## 1. Objective

This pass removes the minimum location/CWD-sensitive path blockers for later containment of retained v15 dataset-construction utilities. It does **not** execute containment. Retained v15 utilities remain legacy lineage, non-canonical for the forward system.

## 2. Accepted baseline

- Phase 15C removed the import-coupling blocker in `remove_v15_duplicates.py` and reported that the remaining blocker was legacy CWD/location-sensitive path assumptions.
- Phase 15C identified paths such as `evaluation/finetuning/v15_balanced.jsonl` and `evaluation/finetuning/v15_balanced_dedup.jsonl` as depending on current working directory (or accidental co-location), making later containment execution risky.
- Active flows were not to be changed; only the retained-lineage v15 utility cluster was in scope.

## 3. Scope executed

- **Exact files changed:** `ml/training/src/utils/remove_v15_duplicates.py`
- **Exact files inspected but not changed:** None. `create_v15_balanced_dataset.py` and other `create_v15_*` files were not modified; their path assumptions were not in the critical path for the Phase 15C-identified blocker (remove_v15_duplicates path assumptions).
- **Why the changed file was necessary:** The only path-assumption blocker called out for this phase was in `remove_v15_duplicates.py`. Fixing it required editing that file only; no related file needed changes to keep the path chain coherent.

## 4. Path-assumption changes completed

| File | Old path assumption form | New path resolution form | Why safer for later containment |
|------|---------------------------|--------------------------|----------------------------------|
| `ml/training/src/utils/remove_v15_duplicates.py` | All input/output paths were raw CWD-relative: `Path("evaluation/finetuning/v15_balanced.jsonl")`, `Path("evaluation/finetuning/v15_balanced_dedup.jsonl")`, and similarly for V12_FILE, V13_FILE, V14_FILE, V15_ADDITIONAL_FILE, V15_MISSING_FILE. | Repo root derived once from module location: `_REPO_ROOT = Path(__file__).resolve().parents[4]`, `_LEGACY_FINETUNING = _REPO_ROOT / "evaluation/finetuning"`. All path constants now use `_LEGACY_FINETUNING / "<filename>"`. Before writing the output file, `V15_DEDUP_FILE.parent.mkdir(parents=True, exist_ok=True)` is called so the script does not fail with FileNotFoundError when the directory is missing. | Paths no longer depend on current working directory. The script resolves "evaluation/finetuning" relative to a stable anchor (repo root derived from `__file__`). Later containment can relocate the script; as long as the script file’s position relative to repo root is unchanged (or the derivation is updated in one place), the same logical paths are used. Missing data remains a clear, honest condition (file not found under the resolved path) rather than arbitrary CWD-dependent failure. |

## 5. Remaining containment blockers

- **Remaining path/location assumptions:** `create_v15_balanced_dataset.py` and other `create_v15_*` scripts in `ml/training/src/dataset_creation/` still use CWD-relative paths (e.g. `Path("evaluation/finetuning/...")`). They were intentionally left unchanged in this pass; they were not part of the minimum blocker set identified by Phase 15C for remove_v15_duplicates.
- **Blockers intentionally left unchanged:** No other legacy utilities were modified. Broader path normalization for the full v15 dataset-creation chain is out of scope for this phase.
- **Later containment execution pass:** A containment execution pass can proceed for the remove_v15_duplicates utility with the path blocker neutralized. If retained-lineage scripts are grouped into a different directory, the repo-root derivation in remove_v15_duplicates (`Path(__file__).resolve().parents[4]`) may need to be updated (e.g. different `parents[n]`) so that _REPO_ROOT still points at the repository root; that is a single local change. No further path-assumption prep is strictly required for this file before containment.

## 6. Validation performed

- **Path-assumption validation:** The CWD-relative path literals in `remove_v15_duplicates.py` were replaced with repo-root–relative resolution. The script was run from repo root; it completed successfully (exit code 0) and wrote output to `/home/harshil/Harshil-PoCs/m-coder/evaluation/finetuning/v15_balanced_dedup.jsonl`. The previous FileNotFoundError (caused by writing to a path whose parent directory did not exist when using CWD-relative resolution) no longer occurs; the output directory is created when needed.
- **Module-load validation:** The script was executed with `python3 ml/training/src/utils/remove_v15_duplicates.py` from repo root; the module loads and runs to completion.
- **Behavior-preservation validation:** No logic changes were made beyond path resolution and ensuring the output directory exists before write. Input/output path intent (evaluation/finetuning/...) is unchanged; only the resolution anchor is now stable.
- **Test/manual-run results:** No new tests were added. Manual run from repo root: success (exit 0), output file written under repo-root–resolved path.

## 7. Explicit non-actions

- No files were moved.
- No files were renamed.
- No files were deleted.
- No containment was executed.
- No archive/export was executed.
- No active pipeline was redesigned.

## 8. Recommendation for next pass

**Recommendation: containment execution pass.** The path-assumption blocker identified for `remove_v15_duplicates.py` has been neutralized. A containment execution pass can proceed to group or relocate retained-lineage v15 dataset-construction utilities as planned. If the script is moved to a different depth in the tree, update the `parents[4]` to the correct depth so _REPO_ROOT remains the repository root. Optionally, a later pass can apply the same minimal pattern (repo-root–relative resolution) to other `create_v15_*` path assumptions if they become relevant to containment.
