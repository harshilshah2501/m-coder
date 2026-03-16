# Phase 13 — Batch E-exec-1 Execution Report

**Repository:** m-coder  
**Batch:** E-exec-1 — Root Artifact Relocation (ultra-tight scope)  
**Date:** 2026-03-16  
**Governing plans:** [PATH_SAFE_STRUCTURAL_RELOCATION_PLAN.md](PATH_SAFE_STRUCTURAL_RELOCATION_PLAN.md), [STRUCTURAL_REMEDIATION_PLAN.md](STRUCTURAL_REMEDIATION_PLAN.md)

---

## 1. Purpose

This batch covered **only** the four root-generated artifact files identified in prior audits: `ledger.db`, `stage6c_ledger.jsonl`, `suite_traces.jsonl`, and `tail_stage6c_ledger.txt`. No other root files, directories, code, or docs were in scope. The objective was to determine whether each of these artifacts could be safely relocated from the repository root to an existing artifact home, with a per-file safety decision and no relocation when hardcoded root-path dependency or ambiguous destination existed.

---

## 2. Files inspected

| Target file | Existed at root |
|-------------|-----------------|
| `ledger.db` | Yes |
| `stage6c_ledger.jsonl` | Yes |
| `suite_traces.jsonl` | Yes |
| `tail_stage6c_ledger.txt` | Yes |

All four files were present at repository root before execution.

---

## 3. Reference scan results

### ledger.db

- **Where references were found:** Audit/planning docs (PATH_SAFE, STRUCTURAL_REMEDIATION, BATCH_B, ROOT_LAYOUT, CROSS_LAYER, LAYER2, etc.) describe it as being at root or as a relocation candidate. Runtime code: `runtime/observation/drift_baseline.py` uses generic `ledger_path="/path/to/ledger.db"`; `runtime/observation/report_runtime_summary.py` uses `MOTADATA_EXECUTE_LEDGER_PATH` or `--ledger-path`; `runtime/execute_service/handlers.py` uses `ledger_path` from payload or env. Runtime tests use `Path(tmpdir) / "ledger.db"` or `Path(tmp) / "ledger.db"` only. Milestone docs (M4_1, M4_2) use `/path/to/ledger.db`; M4_4 had one code example `SandboxLedgerStore("ledger.db")` (relative path; minimal doc update applied).
- **Hardcoded / generic / absent:** No hardcoded repo-root path. All code uses tmp, env, or generic paths. Doc references are generic or descriptive except one example updated.
- **Blocked or allowed:** Relocation allowed. No blocker.

### stage6c_ledger.jsonl

- **Where references were found:** Audit/planning docs list it as root artifact. Code: `ml/training/pipeline/stage6/stage6c/` (orchestrator, reporting, cli, freeze) and `ml/training/artifacts/cli.py` use `out_dir / "stage6c_ledger.jsonl"`, `out_path / "stage6c_ledger.jsonl"`, or `run_dir / "stage6c_ledger.jsonl"` — i.e. under an output directory, never repo root. `conf_drift_pipeline.py` references `"$OUT"/stage6c_ledger.jsonl`. Tests use `out_dir` or `out_path`. Script `verify_artifact_hygiene.sh` forbids *tracking* these names (git ls-files); no path assumption.
- **Hardcoded / generic / absent:** No hardcoded root path. All references are under OUT/out_dir/run_dir.
- **Blocked or allowed:** Relocation allowed. No blocker.

### suite_traces.jsonl

- **Where references were found:** Audit docs; `conf_drift_pipeline.py` uses `stage7 / "suite_traces.jsonl"` (stage7 dir); stage6c orchestrator/executor and artifacts CLI use `out_path/out_dir/run_dir` + filename. Tests use `out_dir / "suite_traces.jsonl"`.
- **Hardcoded / generic / absent:** No hardcoded root path. All references are under a designated output or stage directory.
- **Blocked or allowed:** Relocation allowed. No blocker.

### tail_stage6c_ledger.txt

- **Where references were found:** Audit docs only (listed as root artifact). No code, script, or test references.
- **Hardcoded / generic / absent:** Absent in code/scripts/tests. Purely descriptive in docs.
- **Blocked or allowed:** Relocation allowed. No blocker.

---

## 4. Per-file decision

| File | Decision | Rationale |
|------|----------|-----------|
| `ledger.db` | **RELOCATED** | No code assumes root; runtime uses tmp/env/generic paths; one doc example updated to `.spool/ledger.db`. Destination `.spool/` is the documented runtime artifact home. |
| `stage6c_ledger.jsonl` | **RELOCATED** | No root-path dependency; all code uses OUT/out_dir/run_dir. Root copy is generated residue. Destination `ml/training/generated/` is the justified artifact home for stage6c outputs. |
| `suite_traces.jsonl` | **RELOCATED** | Same as stage6c_ledger; code uses output directories only. Relocated to `ml/training/generated/`. |
| `tail_stage6c_ledger.txt` | **RELOCATED** | No references in code/scripts/tests; audit docs only. Relocated to `ml/training/generated/` for consistency with other stage6c artifacts. |

---

## 5. Relocations performed

| Old path | New path | Why destination | Why safe |
|----------|----------|------------------|-----------|
| `ledger.db` | `.spool/ledger.db` | Governing plan designates `.spool` (or runtime-owned dir) for runtime ledger artifact. | Code uses tmp/env/generic paths; one minimal doc example updated in M4_4 to `.spool/ledger.db`. |
| `stage6c_ledger.jsonl` | `ml/training/generated/stage6c_ledger.jsonl` | Existing artifact home for stage6c outputs; no new directory. | No code reads from repo root; all references are under OUT/out_dir/run_dir. |
| `suite_traces.jsonl` | `ml/training/generated/suite_traces.jsonl` | Same as above. | Same; no root-path dependency. |
| `tail_stage6c_ledger.txt` | `ml/training/generated/tail_stage6c_ledger.txt` | Same artifact home as other stage6c outputs. | No references in code/scripts/tests. |

---

## 6. Non-changes

- **No code edits** — No Python, shell, or other code was modified (except the minimal doc update below).
- **No non-target file moves** — Only the four target artifacts were moved.
- **No canonical path changes** — No moves of README, AGENT_EXECUTION_RULES, docs/, governance/, runtime/, observation/, ml/, jetbrains-plugin/, or any canonical root file.
- **No cuda-pytorch / root-guide handling** — `cuda-pytorch_test.py` and `motadata-coder-a-complete-guide_v1.7.md` were not touched.
- **No broad root cleanup** — No other root files or directories were relocated; no second cleanup in this batch.

**Minimal doc update (strictly required by relocation):** `docs/runtime/milestones/M4_4_LEDGER_RECONCILIATION.md` — code example `SandboxLedgerStore("ledger.db")` was changed to `SandboxLedgerStore(".spool/ledger.db")` so the example matches the new artifact home. Single line; no broader doc edits.

---

## 7. Validation

- **Relocated files:** Verified present at `.spool/ledger.db` and `ml/training/generated/stage6c_ledger.jsonl`, `ml/training/generated/suite_traces.jsonl`, `ml/training/generated/tail_stage6c_ledger.txt`. Verified absent at former root paths.
- **Reference safety:** No file had a hardcoded root-path dependency; all relocations were safe. The only doc reference that assumed a relative `ledger.db` was updated.
- **Scope discipline:** Only the four target artifacts were relocated; one minimal doc update; no other files or directories changed.

---

## 8. Final status

**BATCH E-EXEC-1 COMPLETE**

All four existing target files were safely resolved in-batch (relocated to the agreed artifact homes). No blockers; no files left in place due to path dependency.
