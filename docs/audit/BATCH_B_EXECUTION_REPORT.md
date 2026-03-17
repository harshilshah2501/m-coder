# Phase 9 — Batch B Execution Report (Root Hygiene + Artifact-Home Clarification)

**Repository:** m-coder  
**Batch:** B — Root hygiene + artifact-home clarification  
**Date:** 2026-03-15  
**Governing plan:** [STRUCTURAL_REMEDIATION_PLAN.md](STRUCTURAL_REMEDIATION_PLAN.md)

---

## 1. Purpose

Batch B is **root hygiene + artifact-home clarification only**. It addresses root-level structural clarity by: (1) closing the ignore-coverage gap for generated root artifacts, (2) ensuring root-generated artifact leakage is controlled via .gitignore so they are not committed, and (3) relocating root-level temporary/planning prompt files to an existing archival location. No canonical paths were renamed or moved. No code was edited. No broad cleanup was performed.

---

## 2. Files inspected

| Item | Type | Inspected |
|------|------|-----------|
| `ledger.db` | file | Present at root; untracked; not in .gitignore |
| `stage6c_ledger.jsonl` | file | Present at root; already ignored by `**/stage6c_ledger*.jsonl` |
| `suite_traces.jsonl` | file | Present at root; already ignored by `**/suite_traces*.jsonl` |
| `tail_stage6c_ledger.txt` | file | Present at root; not in .gitignore |
| `plan-artifactSegregation.prompt.md` | file | Present at root; tracked |
| `plan-stage6c-ref-sanitizer.prompt.md` | file | Present at root; tracked |
| `plan-stage6cPassToStage7Freeze.prompt.md` | file | Present at root; tracked |
| `.gitignore` | file | Read; existing patterns for suite_traces, stage6c_ledger; no ledger.db or tail_* |
| `README.md` (root) | file | Not modified (canonical entry; Batch A already clarified) |
| `archive/` | dir | Exists; used as existing archival home |

---

## 3. Changes executed

### .gitignore

- **File changed:** `.gitignore`
- **Exact change:** Added two explicit ignore entries and a short comment after the existing Stage6C block:
  - `ledger.db`
  - `tail_stage6c_ledger.txt`
  - Comment: `# Root-generated artifacts (do not commit; use .spool or ml/training/generated)`
- **Justification:** Audits identified ledger.db and tail_stage6c_ledger.txt as generated root artifacts not covered by .gitignore; adding them prevents accidental commit and matches intended artifact-home (.spool / ml/training/generated).
- **Broader change avoided:** No wildcard like `tail_*` or `*.db` to avoid hiding canonical assets; no change to existing patterns.

### Root prompt files → archive/planning

- **Paths changed:** `plan-artifactSegregation.prompt.md`, `plan-stage6c-ref-sanitizer.prompt.md`, `plan-stage6cPassToStage7Freeze.prompt.md` moved from root to `archive/planning/`.
- **Exact change:** Created `archive/planning/` and moved the three files with `git mv` so history is preserved.
- **Justification:** All three are non-canonical planning/temporary prompts; archive/ is an existing appropriate location; moving them improves root navigation clarity without touching path-contract-sensitive paths. Content references (e.g. OUT/stage6c_ledger in plan-stage6cPassToStage7Freeze) remain valid as logical paths, not repo paths to the prompt file itself.
- **Broader change avoided:** No new docs/planning at top level; no scattering into multiple archive subdirs; cuda-pytorch_test.py and root guide left for a later batch.

---

## 4. Root item classification results

| Item | Classification | Action taken | Rationale |
|------|----------------|-------------|-----------|
| `ledger.db` | Generated artifact; not path-sensitive at root (code uses tmp or env) | Added to .gitignore | Prevents commit; file left on disk; relocation deferred (docs/code may reference path generically). |
| `stage6c_ledger.jsonl` | Generated artifact | None | Already ignored by `**/stage6c_ledger*.jsonl`; no change. |
| `suite_traces.jsonl` | Generated artifact | None | Already ignored by `**/suite_traces*.jsonl`; no change. |
| `tail_stage6c_ledger.txt` | Generated artifact; debug output | Added to .gitignore | Prevents commit; file left on disk; explicit pattern safe. |
| `plan-artifactSegregation.prompt.md` | Temporary planning prompt | Moved to archive/planning/ | Non-canonical; reduces root clutter; archive is existing home. |
| `plan-stage6c-ref-sanitizer.prompt.md` | Temporary planning prompt | Moved to archive/planning/ | Same as above. |
| `plan-stage6cPassToStage7Freeze.prompt.md` | Temporary planning prompt; references OUT/stage6c_ledger in content | Moved to archive/planning/ | Content reference is to output path, not to this file; move is low risk. |
| `cuda-pytorch_test.py` | Unclear ownership | None | Left for later batch; not generated residue; classification only. |
| `motadata-coder-a-complete-guide_v1.7.md` | Root guide (Batch A clarified role) | None | Already clarified in Batch A; not touched. |

---

## 5. `.gitignore` remediation result

- **Patterns added:**  
  - `ledger.db`  
  - `tail_stage6c_ledger.txt`  
  With comment: `# Root-generated artifacts (do not commit; use .spool or ml/training/generated)`.

- **Safety:**  
  - Explicit filenames only; no broad `*.db` or `tail_*` that could hide canonical files.  
  - Existing Stage6C patterns (`**/suite_traces*.jsonl`, `**/stage6c_ledger*.jsonl`) unchanged and still cover root JSONL files.  
  - Code and docs use tmp paths or env `MOTADATA_EXECUTE_LEDGER_PATH` or generic `/path/to/ledger.db`; no repo-root path contract broken.

---

## 6. Root artifact handling result

| Artifact | Result |
|----------|--------|
| `ledger.db` | Added to .gitignore; **not** deleted or moved. Remains on disk; future commits will not include it. Relocation left to a later batch if needed. |
| `stage6c_ledger.jsonl` | Already ignored; no change. File left on disk. |
| `suite_traces.jsonl` | Already ignored; no change. File left on disk. |
| `tail_stage6c_ledger.txt` | Added to .gitignore; **not** deleted or moved. Remains on disk. |

No physical deletion or relocation of these four artifacts in this batch; preference was for ignore + classification over movement to avoid path-contract or reference risk.

---

## 7. Root prompt/planning file result

- **Action:** All three root `*.prompt.md` files were moved to `archive/planning/` via `git mv` (root → archive/planning/).
- **Reason:** They are non-canonical planning/temporary artifacts; `archive/` is an existing, appropriate location; one subdir `archive/planning/` keeps them grouped without a large new structure.
- **Path-contract:** No code or docs reference these files by path; one prompt mentions OUT/stage6c_ledger as an output path, not the prompt file location. Move is low risk.
- **Result:** Root no longer lists these three prompt files; they remain in repo under archive/planning/ with history preserved.

---

## 8. Path-contract safety check

- **Canonical paths:** No path-contract-sensitive canonical item was moved or renamed. README.md, AGENT_EXECUTION_RULES.md, docs/, governance/, runtime/, observation/, ml/, jetbrains-plugin/ were not modified in structure or name.
- **Artifacts:** ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt were not moved or deleted; only .gitignore was updated.
- **Prompt files:** Moved only from root to archive/planning/; no references to their path in code or canonical docs; safe.

---

## 9. Non-changes

The following were **intentionally not changed**:

- **No deletion** of any root artifact file (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt).
- **No relocation** of those artifacts (no move to .spool or ml/training/generated) in this batch.
- **No change** to cuda-pytorch_test.py (left for later batch).
- **No change** to root README, report dirs, observation split docs, or any other canonical doc.
- **No OUT convention** doc added (minimal batch; can be done in a later batch).
- **No new top-level dirs** other than archive/planning/ for the three prompt files.
- **No code or script** edits.

---

## 10. Validation

- **Minimal and safe:** Only .gitignore (two entries + comment) and one logical change (three prompt files moved to archive/planning/). No renames, no code changes, no report or spine edits.
- **Root clarity:** Generated artifacts are now ignored at root; prompt files no longer at root; canonical entrypoints unchanged.
- **Path-contract:** No canonical path moved or renamed; artifact files not moved; prompt move has no path-contract impact.
- **Ignore coverage:** ledger.db and tail_stage6c_ledger.txt are now ignored; stage6c_ledger and suite_traces were already covered.

---

## 11. Final status

**BATCH B COMPLETE**
