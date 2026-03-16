# Phase 0 — Root Project Directory Audit Report

**Repository:** m-coder  
**Audit phase:** Phase 0 only (root-only, read-only structural audit)  
**Date:** 2026-03-15  
**Scope:** Top-level directories and files only. No moves, renames, refactors, or remediation performed.

---

## 1. Purpose and scope

This document is the deliverable for **Phase 0** of the m-coder structural audit. It is a **read-only structural audit** of the **repository root only**. It does not inspect layer internals beyond what is needed to classify root-level ownership, does not start Phase 1 or later, and does not perform any file moves, renames, deletions, or doc/code changes. The audit inventories every top-level item, classifies ownership and root suitability, assesses path-contract sensitivity, runs the stable canonical path test, and records preliminary keep/move/archive/clarify recommendations without executing them.

---

## 2. Executive assessment

- **Overall root structural health:** Moderate. The root reflects the 4-layer architecture in that the four layer directories (`governance/`, `ml/`, `runtime/`, `observation/`) and cross-cutting dirs (`docs/`, `scripts/`, `tests/`, `archive/`) are present and named consistently. Canonical entry paths are documented in README and MASTER_SYSTEM_SPEC. However, root is cluttered with runtime/training artifacts, ad-hoc prompt files, and a large standalone guide, which weakens the “root as contract” signal and creates ambiguity about what is canonical vs temporary.

- **Does root currently reflect the 4-layer architecture clearly?** Partially. The four layer dirs are present and README points to `docs/MASTER_SYSTEM_SPEC.md` and `docs/ARCHITECTURE_4_LAYER.md`. Competing or ambiguous root-level docs (e.g. `motadata-coder-a-complete-guide_v1.7.md`, `plan-*.prompt.md`) and artifact files at root reduce clarity.

- **Major immediate concerns:** (1) Artifact leakage at root: `ledger.db`, `stage6c_ledger.jsonl`, `suite_traces.jsonl`, `tail_stage6c_ledger.txt` are runtime/training outputs and should not live at root. (2) Root-level prompt/planning files (`plan-artifactSegregation.prompt.md`, `plan-stage6c-ref-sanitizer.prompt.md`, `plan-stage6cPassToStage7Freeze.prompt.md`) and the large guide (`motadata-coder-a-complete-guide_v1.7.md`) create competing “start here” or working-doc signals. (3) `ledger.db` is not in `.gitignore`; root JSONL files are gitignored by pattern but still present. (4) One-off script `cuda-pytorch_test.py` at root has unclear ownership (test vs dev harness).

---

## 3. Root inventory

Complete list of top-level items. Type: `dir` or `file`. Ownership: Layer-1/2/3/4, cross-cutting, generated/artifact, archive/temporary, or unclear. Root suitability: `appropriate at root` / `questionable` / `should not live at root`. Path-contract sensitivity: `yes` / `no` / `unknown`.

| Item | Type | Preliminary ownership | One-line role | Root suitability | Path-contract sensitivity |
|------|------|------------------------|---------------|------------------|----------------------------|
| `.cursor` | dir | cross-cutting | Cursor IDE/plans state | appropriate at root | no |
| `.dvc` | dir | cross-cutting | DVC config and pointer metadata | appropriate at root | yes (scripts/docs) |
| `.git` | dir | cross-cutting | Git metadata | appropriate at root | no |
| `.gitignore` | file | cross-cutting | Ignore rules for repo | appropriate at root | yes (CI, scripts) |
| `.pytest_cache` | dir | cross-cutting | Pytest cache (generated) | questionable | no |
| `.spool` | dir | Layer-3 | Runtime plan-gate spool output | appropriate at root (documented) | yes (runtime, .gitignore) |
| `.venv` | dir | cross-cutting | Python venv | appropriate at root | no |
| `AGENT_EXECUTION_RULES.md` | file | Layer-1 | Canonical agent rules; branch discipline, file safety | appropriate at root | yes (docs, verification) |
| `Hardware-Profile.md` | file | cross-cutting | Hardware/deployment profile | questionable | unknown |
| `Makefile` | file | cross-cutting | DVC artifact topology targets | appropriate at root | yes (scripts, docs) |
| `README.md` | file | cross-cutting | Main repo entry; points to MASTER_SYSTEM_SPEC | appropriate at root | yes (docs, canonical) |
| `archive` | dir | cross-cutting | Archived docs/reorg/OKR | appropriate at root | no |
| `cuda-pytorch_test.py` | file | unclear | One-off CUDA/PyTorch test script | should not live at root | unknown |
| `docs` | dir | cross-cutting | Canonical specs, guides, reports | appropriate at root | yes (all layers) |
| `governance` | dir | Layer-1 | Constitution, phases, GREG, golden exemplars | appropriate at root | yes (docs) |
| `jetbrains-plugin` | dir | Layer-3 | IDE plugin (Plan-Gate client) | appropriate at root | yes (docs, runtime) |
| `ledger.db` | file | Layer-3 (artifact) | Runtime sandbox ledger DB (generated) | should not live at root | yes (docs/examples, env) |
| `ml` | dir | Layer-2 | Compilation, training, lineage, artifacts | appropriate at root | yes (docs, Makefile) |
| `motadata-coder-a-complete-guide_v1.7.md` | file | cross-cutting | Large Golden Exemplars guide; README points to it | questionable | yes (README, docs) |
| `observation` | dir | Layer-4 | Observation CLIs, baseline, ingest, judge_drift_suite | appropriate at root | yes (docs, runtime) |
| `plan-artifactSegregation.prompt.md` | file | cross-cutting | Prompt/planning doc (artifact segregation) | should not live at root | no |
| `plan-stage6c-ref-sanitizer.prompt.md` | file | cross-cutting | Prompt/planning doc (stage6c ref sanitizer) | should not live at root | no |
| `plan-stage6cPassToStage7Freeze.prompt.md` | file | cross-cutting | Prompt/planning doc (stage6c→freeze) | should not live at root | yes (references OUT/stage6c_ledger.jsonl) |
| `runtime` | dir | Layer-3 | Enforcement, plan-gate, sandbox, ledger, observation lib | appropriate at root | yes (docs, plugin) |
| `scripts` | dir | cross-cutting | Setup, CI, utilities | appropriate at root | yes (Makefile, docs) |
| `stage6c_ledger.jsonl` | file | Layer-2/3 (artifact) | Stage6C ledger output (generated) | should not live at root | no (gitignored) |
| `suite_traces.jsonl` | file | Layer-2/3 (artifact) | Suite traces output (generated) | should not live at root | no (gitignored) |
| `tail_stage6c_ledger.txt` | file | generated/artifact | Debug/tail output of ledger | should not live at root | no |
| `tests` | dir | cross-cutting | Top-level tests | appropriate at root | yes (CI) |

**Counts:**  
- Top-level directories: **14** (including `.cursor`, `.dvc`, `.git`, `.pytest_cache`, `.spool`, `.venv`, `archive`, `docs`, `governance`, `jetbrains-plugin`, `ml`, `observation`, `runtime`, `scripts`, `tests`).  
- Top-level files: **14**.

---

## 4. Root-level structural findings

Each finding is stated separately with: Finding; Why it is a problem; Severity; Recommended action; Action timing.

**Finding 1 — Runtime/training artifacts at repository root**  
- **Why it is a problem:** `ledger.db`, `stage6c_ledger.jsonl`, `suite_traces.jsonl`, and `tail_stage6c_ledger.txt` are generated outputs. Root should express structure and canonical entrypoints, not runtime or pipeline outputs. This creates ambiguity and risks committing local state; `.gitignore` already ignores `**/suite_traces*.jsonl` and `**/stage6c_ledger*.jsonl`, but `ledger.db` and `tail_stage6c_ledger.txt` are not ignored.  
- **Severity:** High (artifact leakage; one file not gitignored).  
- **Recommended action:** (1) Add `ledger.db` and `tail_stage6c_ledger.txt` (or a root-level artifact pattern) to `.gitignore` if root outputs are not intended in repo. (2) In a later remediation phase, relocate or document that these files are local-only and should be produced under a designated dir (e.g. `.spool`, `runtime`, or `ml/training/generated`).  
- **Action timing:** `.gitignore` update: `later` (after audit approval). Relocation: `later` (remediation phase).

**Finding 2 — Prompt/planning markdown files at root**  
- **Why it is a problem:** `plan-artifactSegregation.prompt.md`, `plan-stage6c-ref-sanitizer.prompt.md`, and `plan-stage6cPassToStage7Freeze.prompt.md` are working/prompt docs. Root is documented as the place for canonical entrypoints (README, AGENT_EXECUTION_RULES); mixing in prompt files blurs the line between canonical and temporary.  
- **Severity:** Medium (clutter; not path-contract critical).  
- **Recommended action:** Move to a dedicated location (e.g. `docs/planning/` or `archive/planning/`) in a later remediation phase; do not treat as canonical.  
- **Action timing:** `later` (remediation phase).

**Finding 3 — Large standalone guide at root**  
- **Why it is a problem:** `motadata-coder-a-complete-guide_v1.7.md` (~82 KB) is referenced by README as “Golden Exemplars guide” and by ARCHITECTURE_4_LAYER. It functions as a secondary entrypoint. Having it at root competes with the documented canonical chain (README → MASTER_SYSTEM_SPEC → layer indices).  
- **Severity:** Medium (competing entrypoint; path is referenced).  
- **Recommended action:** Clarify only: document in MASTER_SYSTEM_SPEC or README that this file is the Golden Exemplars long-form guide and that MASTER_SYSTEM_SPEC remains the single canonical spec entry. Optionally move to `docs/` or `governance/` in a later phase.  
- **Action timing:** `clarify only` now (document role); optional move `later`.

**Finding 4 — One-off test script at root**  
- **Why it is a problem:** `cuda-pytorch_test.py` at root has unclear ownership (Layer-2 dev/hardware check vs ad-hoc). Root should not accumulate one-off scripts; they belong under `scripts/` or `ml/` or `tests/`.  
- **Severity:** Low (clutter; no evidence of path contract).  
- **Recommended action:** Reclassify or move to `scripts/` or `tests/` or `ml/` in a later phase.  
- **Action timing:** `later`.

**Finding 5 — Dual copy of AGENT_EXECUTION_RULES (documented)**  
- **Why it is a problem:** Root holds the canonical `AGENT_EXECUTION_RULES.md`; `docs/governance/AGENT_EXECUTION_RULES.md` is a pointer to root. Drift between the two would be a consistency risk.  
- **Severity:** Low (already documented; pointer is intentional).  
- **Recommended action:** No structural change at root. Phase 1 (docs audit) can confirm pointer target and alignment.  
- **Action timing:** `never touch without dedicated plan` for root copy; pointer alignment in Phase 1.

**Finding 6 — Observation layer path case in docs**  
- **Why it is a problem:** MASTER_SYSTEM_SPEC and MIGRATION_NOTE reference `OBSERVATION/README.md` (uppercase); the actual directory is `observation/` (lowercase). This is a docs/link issue, not a root layout issue, but affects “canonical observation entrypoint” clarity.  
- **Severity:** Medium (link/location mismatch; affects canonical path test).  
- **Recommended action:** Fix doc links to use `observation/README.md` in Phase 1 (docs audit).  
- **Action timing:** `later` (Phase 1).

---

## 5. Stable canonical path test

For each canonical entrypath we state: current path; whether it is obvious from root; whether it competes with another path; confidence (`clear`, `partially clear`, `unclear`).

| Entrypoint | Current path | Obvious from root? | Competes with another? | Confidence |
|------------|--------------|--------------------|------------------------|------------|
| **Canonical architecture** | `docs/MASTER_SYSTEM_SPEC.md` (TOC); `docs/ARCHITECTURE_4_LAYER.md` (directory philosophy) | Yes — README “Canonical spec entry point” and “4-layer architecture” point to these | Slightly: root `motadata-coder-a-complete-guide_v1.7.md` is also a referenced “guide” | **clear** |
| **Canonical roadmap / tracker** | `docs/LIVE_ROADMAP_TRACKER.md` | Yes — README “Live execution tracker” and “single source of truth” | No | **clear** |
| **Canonical governance** | `governance/` (content); root `AGENT_EXECUTION_RULES.md` (canonical rules); `docs/governance/README.md` (pointer to root rules) | Yes — README points to MASTER_SYSTEM_SPEC and governance; AGENT_EXECUTION_RULES at root is documented canonical | No; docs copy is explicit pointer | **clear** |
| **Canonical runtime** | `runtime/` (code); `docs/LAYER3_RUNTIME_SPEC.md`; `docs/runtime/README.md` (layer index) | Yes — README Layer-3 and “runtime/README” referenced in MASTER_SYSTEM_SPEC | No | **clear** |
| **Canonical observation** | `observation/` (Layer-4 CLIs); `observation/README.md` | Partially — README links to `observation/README.md`; MASTER_SYSTEM_SPEC and MIGRATION_NOTE use `OBSERVATION/README.md` (case mismatch) | Case mismatch in docs only | **partially clear** |

---

## 6. Path Contract Register

Root items that are path-sensitive, with: Path; Why path-sensitive; Referenced by; Risk if moved; Recommendation note.

| Path | Why path-sensitive | Referenced by | Risk if moved | Recommendation note |
|------|--------------------|---------------|---------------|--------------------|
| `AGENT_EXECUTION_RULES.md` | Canonical agent rules; governance and verification audits assume root | docs (SYSTEM_GOVERNANCE_AUDIT, RUNTIME_CONSTITUTIONAL_REFERENCE, governance README), .cursor plans | High — many docs and audits reference root path | Keep at root; do not move without dedicated plan |
| `README.md` | Main repo entry; points to MASTER_SYSTEM_SPEC and layer indices | All users; docs (MIGRATION_NOTE, MASTER_SYSTEM_SPEC) | High | Keep at root |
| `Makefile` | DVC targets; REPO_ROOT = git root | scripts (setup_dvc_local.sh), docs (DVC_ARTIFACTS_README, REGISTRY) | Medium — scripts assume repo root | Keep at root |
| `.gitignore` | Ignore rules; artifact hygiene | CI (verify_artifact_hygiene.sh), docs (plan-artifactSegregation) | High if changed incorrectly | Keep at root; add ledger.db/tail pattern in later phase |
| `docs/` | Canonical specs and reports | README, MASTER_SYSTEM_SPEC, all layer docs | High | Keep at root |
| `governance/` | Layer-1 content | README, MASTER_SYSTEM_SPEC, MIGRATION_NOTE | High | Keep at root |
| `runtime/` | Layer-3 code and runtime/observation | README, docs, jetbrains-plugin | High | Keep at root |
| `observation/` | Layer-4 CLIs | README, MASTER_SYSTEM_SPEC (as OBSERVATION in docs), plan_gate_stub README | Medium — doc case mismatch | Keep at root; fix doc links to observation/ |
| `ml/` | Layer-2 content; Makefile ARTIFACTS paths | README, Makefile, docs | High | Keep at root |
| `scripts/` | Setup and CI | Makefile, docs (CI_EXECUTION_MODEL, verify_artifact_hygiene) | Medium | Keep at root |
| `jetbrains-plugin/` | IDE plugin | docs (JETBRAINS_PLUGIN_FLOW, runtime README) | Medium | Keep at root |
| `.dvc` | DVC config | scripts (setup_dvc_local.sh), Makefile | Medium | Keep at root |
| `.spool` | Runtime spool output | .gitignore, runtime | Low if moved to runtime-owned path | Document or relocate in remediation only |
| `ledger.db` | Example path in docs; env MOTADATA_EXECUTE_LEDGER_PATH | Docs (milestones, verification report) use “ledger.db” or “path/to/ledger.db”; tests use tmp paths | Low for repo root (file should not be at root); high if code assumed root ledger | Do not rely on root; add to .gitignore; relocate in remediation |
| `motadata-coder-a-complete-guide_v1.7.md` | README “Golden Exemplars guide” | README, ARCHITECTURE_4_LAYER, SYSTEM_EXECUTION_ROADMAP | Medium if moved — links would break | Clarify role; optional move later |
| `plan-stage6cPassToStage7Freeze.prompt.md` | References OUT/stage6c_ledger.jsonl, suite_traces | Internal prompt content | Low | Move later; not a public contract |

---

## 7. Preliminary keep / move / archive / clarify classification

| Item | Preliminary classification | Short rationale |
|------|----------------------------|------------------|
| `.cursor` | keep | IDE state; standard at root. |
| `.dvc` | keep | DVC config; referenced by Makefile/scripts. |
| `.git` | keep | Git metadata. |
| `.gitignore` | keep | Repo-wide ignore; consider adding ledger.db/tail pattern later. |
| `.pytest_cache` | keep | Cache; often gitignored. |
| `.spool` | keep | Documented runtime spool; relocation only with dedicated plan. |
| `.venv` | keep | Standard venv location. |
| `AGENT_EXECUTION_RULES.md` | do not touch without dedicated plan | Canonical; many doc/audit references to root path. |
| `Hardware-Profile.md` | clarify only | Document purpose or move in later phase. |
| `Makefile` | keep | DVC and repo root contract. |
| `README.md` | keep | Canonical repo entry. |
| `archive` | keep | Intentional archive. |
| `cuda-pytorch_test.py` | move later | One-off script; belongs under scripts/tests/ml. |
| `docs` | keep | Canonical docs root. |
| `governance` | keep | Layer-1 root. |
| `jetbrains-plugin` | keep | Layer-3 plugin. |
| `ledger.db` | move later | Artifact; add to .gitignore; relocate to runtime/spool or similar. |
| `ml` | keep | Layer-2 root. |
| `motadata-coder-a-complete-guide_v1.7.md` | clarify only (optional move later) | Document as long-form guide; optional move to docs/governance. |
| `observation` | keep | Layer-4 root. |
| `plan-artifactSegregation.prompt.md` | move later | Prompt/planning; move to docs/planning or archive. |
| `plan-stage6c-ref-sanitizer.prompt.md` | move later | Prompt/planning; move to docs/planning or archive. |
| `plan-stage6cPassToStage7Freeze.prompt.md` | move later | Prompt/planning; move to docs/planning or archive. |
| `runtime` | keep | Layer-3 root. |
| `scripts` | keep | Cross-cutting scripts. |
| `stage6c_ledger.jsonl` | move later | Generated; already gitignored; relocate or delete from root. |
| `suite_traces.jsonl` | move later | Generated; already gitignored; relocate or delete from root. |
| `tail_stage6c_ledger.txt` | move later | Debug output; add to .gitignore or relocate. |
| `tests` | keep | Top-level tests. |

---

## 8. Immediate conclusions

- **Does the root tell the truth about the system architecture?** Partially. The four layer directories and README → MASTER_SYSTEM_SPEC → layer indices are correct and documented. Truth is weakened by artifact files, prompt files, and a large guide at root that are not part of the documented “canonical entry” set.

- **Biggest structural risks at root:** (1) Artifact leakage (`ledger.db`, `stage6c_ledger.jsonl`, `suite_traces.jsonl`, `tail_stage6c_ledger.txt`) and `ledger.db` not gitignored. (2) Prompt/planning files at root blur canonical vs temporary. (3) Competing “guide” entrypoint (`motadata-coder-a-complete-guide_v1.7.md`) without explicit subordination to MASTER_SYSTEM_SPEC.

- **Items dangerous to touch:** `AGENT_EXECUTION_RULES.md` (canonical at root; many references). `README.md`, `Makefile`, `.gitignore`, and the four layer dirs (`governance/`, `ml/`, `runtime/`, `observation/`) and `docs/` — all are path-contract sensitive; change only with a dedicated plan.

- **Items most likely not belonging at root:** `ledger.db`, `stage6c_ledger.jsonl`, `suite_traces.jsonl`, `tail_stage6c_ledger.txt`, `plan-*.prompt.md` (3 files), `cuda-pytorch_test.py`. Optional: `motadata-coder-a-complete-guide_v1.7.md` (clarify or move to docs).

- **Next audit phase:** Phase 1 — Canonical docs / spec placement audit (docs entrypoints, canonical vs explanatory vs temporary, duplicate and link consistency, including OBSERVATION vs observation).

---

## 9. Non-goals

This phase did **not**:

- Move, rename, or delete any file or directory.
- Change any code or documentation content.
- Add or modify `.gitignore` or Makefile.
- Perform a full subtree or layer-internal audit.
- Start Phase 1 or any later phase.
- Produce a remediation plan beyond preliminary classifications above.
- Resolve duplicate docs or fix link targets (e.g. OBSERVATION vs observation).

---

## Phase 0 result summary

### 1. Artifact created
- **path:** `docs/audit/ROOT_LAYOUT_AUDIT_REPORT.md`

### 2. Root items audited
- **number of top-level directories:** 14  
- **number of top-level files:** 14  

### 3. Major findings
- **finding 1:** Runtime/training artifacts at root (`ledger.db`, `stage6c_ledger.jsonl`, `suite_traces.jsonl`, `tail_stage6c_ledger.txt`); `ledger.db` not in .gitignore.  
- **finding 2:** Three prompt/planning `.prompt.md` files at root blur canonical vs temporary.  
- **finding 3:** Large standalone guide at root (`motadata-coder-a-complete-guide_v1.7.md`) acts as competing entrypoint; observation doc links use `OBSERVATION/` (case mismatch with `observation/`).  

### 4. Path-sensitive root items identified
- **number:** 16 (items in Path Contract Register).  
- **notable examples:** `AGENT_EXECUTION_RULES.md`, `README.md`, `Makefile`, `.gitignore`, `docs/`, `governance/`, `runtime/`, `observation/`, `ml/`, `scripts/`, `jetbrains-plugin/`, `.dvc`, `ledger.db`, `motadata-coder-a-complete-guide_v1.7.md`.  

### 5. Stable canonical path test result
- **architecture:** clear — `docs/MASTER_SYSTEM_SPEC.md`, `docs/ARCHITECTURE_4_LAYER.md`.  
- **roadmap/tracker:** clear — `docs/LIVE_ROADMAP_TRACKER.md`.  
- **governance:** clear — root `AGENT_EXECUTION_RULES.md`, `governance/`, `docs/governance/README.md` (pointer).  
- **runtime:** clear — `runtime/`, `docs/LAYER3_RUNTIME_SPEC.md`, `docs/runtime/README.md`.  
- **observation:** partially clear — `observation/README.md` (actual path); docs reference `OBSERVATION/README.md`.  

### 6. Final status
**PHASE 0 ROOT AUDIT READY**
