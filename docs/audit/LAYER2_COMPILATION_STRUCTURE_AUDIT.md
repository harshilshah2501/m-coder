# Phase 3 — Layer-2 Compilation / Training Structure Audit Report

> **Program status:** Layer-2 is **LOCKED** per [`LIVE_ROADMAP_TRACKER.md`](../LIVE_ROADMAP_TRACKER.md) §2.1.1. This audit inventories **structure** as of 2026-03-15; pair it with [`LAYER2_COMPILATION_SPEC.md`](../LAYER2_COMPILATION_SPEC.md) for doctrine and tracker §6.1 for closure evidence.

**Repository:** m-coder  
**Audit phase:** Phase 3 only (Layer-2 compilation/training structural audit, read-only)  
**Date:** 2026-03-15  
**Scope:** Layer-2 layout, canonical ownership, stage structure, artifact boundaries, governance-consumption discipline, runtime overlap, path contracts. No moves, renames, edits, or remediation performed.

---

## 1. Purpose and scope

This document is the deliverable for **Phase 3** of the m-coder structural audit. It is a **read-only structural audit** of **Layer-2** (ML compilation and training) only. It does not move or rename files, edit docs or code, refactor, clean up artifacts, fix inconsistencies, or perform remediation. The audit inventories Layer-2 anchors, classifies material by role, assesses stage coherence, artifact-boundary separation, governance-consumption and runtime-coupling boundaries, path-contract sensitivity, and root leakage.

---

## 2. Executive assessment

- **Overall Layer-2 structural health:** Good. Layer-2 is canonically anchored under `ml/` with a clear doc spine (docs/COMPILATION/README.md, docs/LAYER2_COMPILATION_SPEC.md, docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md, ml/training/pipeline/STAGE6_MUTATION_TAXONOMY.md). The stage model (Stage-1 through Stage-8) is reflected in the filesystem: pipeline/stage6/stage6a, stage6b, stage6c; compiler/; stage6c/freeze/; pipeline/stage08/; plus Stage-7 forwarding under pipeline/stage7/. Canonical inputs (governance mirror at `ml/training/_build/exemplars` per REPOSITORY_CONSTITUTION), generated outputs (`ml/training/generated/`), freeze manifests (`ml/training/freeze_manifests/stage6c/`), and artifact policy (ARTIFACT_POLICY.md, verify_artifact_hygiene.sh) are documented and enforced by CI. Governance consumption is contract-bound (read-only mirror; constitution injection from governance + docs paths in profiles.py). Main risks: (1) **Dual “stage7” naming** — canonical Stage-7 is compiler + stage6c/freeze; `ml/training/sft/stage7/` is a CONF-drift workflow bundle; both use “stage7” and can confuse. (2) **Missing _build** — `ml/training/_build/exemplars` is the contractually required mirror but `_build` is absent until prepare_exemplars.sh is run; placement is clear, existence is build-time. (3) **Root leakage** — Phase 0–identified root artifacts (stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt) are Layer-2/3 outputs; they indicate pipeline/output-dir discipline (e.g. OUT) not always directing outputs under ml/training/generated.

- **Does Layer-2 have a clear canonical anchor?** Yes. Primary anchor is `ml/`; doc spine in docs/COMPILATION/README.md and LAYER2_COMPILATION_SPEC points to ml/ and to compiler, pipeline/stage6, stage6c/freeze, stage08, lineage, and artifacts. MASTER_SYSTEM_SPEC and ARCHITECTURE_4_LAYER assign Layer-2 to ml/ and list Stage-1–Stage-8 and DAG/lineage specs.

- **Biggest Layer-2 structural risks:** (1) Naming overlap between pipeline Stage-7 (compiler + freeze) and sft/stage7 (CONF drift bundle). (2) Root-level Layer-2/3 artifact leakage already flagged in Phase 0. (3) Two evaluation locations (ml/evaluation/ and ml/training/evaluation/) and scattered “stage7” references require a new contributor to read STAGE_LAYOUT_CANONICAL and LAYER2_COMPILATION_SPEC to avoid confusion.

---

## 3. Layer-2 canonical spine

For each major Layer-2 anchor we state: path; role; canonical / pointer / supporting; whether it competes; confidence.

| Anchor | Path | Role | Canonical / pointer / supporting | Competes? | Confidence |
|--------|------|------|----------------------------------|-----------|-------------|
| Layer-2 index (docs) | docs/COMPILATION/README.md | Layer-2 index; DAG, lineage, Stage-6, freeze | canonical pointer | No | **clear** |
| Layer-2 comprehensive spec | docs/LAYER2_COMPILATION_SPEC.md | Stage axis, Stage-6C, Stage-7 compiler/freeze, Stage-8, determinism, freeze manifest contract | canonical | No | **clear** |
| DAG and lineage spec | docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md | Node types, R-L1..R-L5, schema locations under ml/lineage/ | canonical | No | **clear** |
| Stage-6 mutation taxonomy | ml/training/pipeline/STAGE6_MUTATION_TAXONOMY.md | Mutation classes; doctrine-locked; linked from MASTER_SYSTEM_SPEC | canonical | No | **clear** |
| ML namespace index | ml/README.md | ml/datasets, lineage, training, evaluation, scripts; layer boundaries | canonical index | No | **clear** |
| Stage-7 compiler | ml/training/compiler/compile_stage7.py | Doctrine → JSONL; DEFAULT_OUT_DIR = …/generated | canonical | No | **clear** |
| Stage-7 compiler README | ml/training/compiler/README.md | Outputs: generated/golden_exemplars_v1.jsonl, dataset_manifest.json | supporting | No | **clear** |
| Freeze orchestration | ml/training/pipeline/stage6/stage6c/freeze/ | freeze.py, cli.py; gates, manifest, split determinism | canonical | No | **clear** |
| Stage-7 forwarding | ml/training/pipeline/stage7/ | Re-exports compile_doctrine, run_freeze; discoverability only | pointer | No (documents split) | **clear** |
| Stage layout canonical | docs/STAGE_LAYOUT_CANONICAL.md | Stage-7 compiler vs freeze location; stage08 dataset discovery; stage7 forwarding | supporting | No | **clear** |
| SFT/stage7 bundle | ml/training/sft/stage7/ | CONF drift pipeline (conf_drift_pipeline.py, golden_exemplars_v1.jsonl, conf_to_des_*); not the Stage-7 compiler | supporting (workflow bundle) | Naming overlap with Stage-7 | **partially clear** |
| Exemplar mirror contract | governance/REPOSITORY_CONSTITUTION §3 | Mirror at ml/training/_build/exemplars; prepare_exemplars.sh | canonical (contract) | No | **clear** |
| Artifact policy | ml/training/ARTIFACT_POLICY.md | Control-plane vs data-plane; artifact store; hygiene | supporting | No | **clear** |

---

## 4. Layer-2 inventory by role

Structured inventory of major Layer-2 files/clusters. Classification and placement quality as defined in the task.

| Path | Role / topic | Classification | Canonical status | Placement quality | Notes |
|------|----------------|----------------|------------------|-------------------|-------|
| ml/ | Layer-2 root | canonical | canonical | good | README, artifacts, datasets, evaluation, lineage, scripts, training |
| ml/README.md | ML namespace index | canonical pointer/index | canonical | good | Points to datasets, lineage, training, evaluation, scripts |
| ml/artifacts/ | Checkpoints, datasets, exports, LAYER2_RELEASE_VERIFICATION | runtime-consumed output / reporting | non-canonical (output) | good | Makefile ARTIFACTS; REGISTRY, MODEL_RELEASE |
| ml/datasets/ | Dataset specs, generation | canonical stage asset | canonical | good | Includes cpt/ |
| ml/lineage/ | DAG/provenance schemas | canonical stage asset | canonical | good | Schemas, examples; referenced by COMPILATION_DAG_AND_LINEAGE |
| ml/evaluation/ | Top-level evaluation (analysis, diffs, reports) | canonical stage asset | canonical | good | Separate from ml/training/evaluation |
| ml/scripts/ | prepare_exemplars.sh, shared ML scripts | canonical stage asset | canonical | good | prepare_exemplars mirrors governance → _build |
| ml/training/ | Training, pipeline, compiler, SFT | canonical | canonical | good | Core Layer-2 tree |
| ml/training/compiler/ | compile_stage7.py, schemas | canonical stage asset | canonical | good | Deterministic doctrine → JSONL |
| ml/training/generated/ | stage6c_runs, compiler outputs (golden_exemplars_v1.jsonl, dataset_manifest) | generated artifact | non-canonical | good | Append-only; CI forbids committing; DEFAULT_OUT_DIR |
| ml/training/freeze_manifests/stage6c/ | Freeze manifests, pointers | frozen output | non-canonical | good | stage6c_import_demo.* |
| ml/training/pipeline/stage6/ | stage6a, stage6b, stage6c, mutation, stage6c_report | canonical stage asset | canonical | good | Mutation harness; STAGE6_* docs |
| ml/training/pipeline/stage6/stage6a/ | Single-step mutation | canonical stage asset | canonical | good | README, layout doc |
| ml/training/pipeline/stage6/stage6b/ | Systemic hardening | canonical stage asset | canonical | good | README; placeholder/systemic |
| ml/training/pipeline/stage6/stage6c/ | Agent-loop mutation, injections, freeze, config, seeds | canonical stage asset | canonical | good | profiles.py reads governance + docs |
| ml/training/pipeline/stage6/stage6c/freeze/ | freeze.py, cli.py | canonical stage asset | canonical | good | Freeze orchestration |
| ml/training/pipeline/stage7/ | Forwarding only | canonical pointer | canonical | good | Re-exports compiler + freeze |
| ml/training/pipeline/stage08/ | SFT training, dataset, checkpoints, configs | canonical stage asset | canonical | good | train.py, train_stage08D, enforce_split, FREEZE_CERTIFICATE |
| ml/training/sft/ | Exemplars, guides, stage7 bundle, config, assets | canonical training guide / exemplar reference | mixed | good | sft/stage7 = CONF drift bundle (not Stage-7 compiler) |
| ml/training/sft/stage7/ | CONF drift pipeline (tools, golden_exemplars_v1.jsonl, conf_to_des_*) | generated artifact / validation output | non-canonical | questionable | Naming overlap with pipeline Stage-7 |
| ml/training/sft/exemplars/ | Guides, status, categories; not Phases (Phases in governance → _build) | governance-consumed input / training guide | non-canonical | good | CI forbids ml/training/sft/exemplars/Phases |
| ml/training/_build/exemplars/ | Mirror of governance/golden-exemplars/Phases | governance-consumed input | canonical (mirror) | good | Created by prepare_exemplars.sh; may be absent until build |
| ml/training/datasets/sft/ | SFT dataset discovery | canonical config | canonical | good | Sentinel-based discovery |
| ml/training/src/ | Finetuning, dataset_creation, evaluation, config, utils, sources | canonical stage asset / experiment residue | mixed | good | v12–v17 train/eval scripts; some versioned experiment scripts |
| ml/training/results/ | Results output | generated artifact | non-canonical | good | Generated |
| ml/training/models/ | Trained models (e.g. qwen_stage8_conf_patch1) | generated artifact / frozen output | non-canonical | good | Training outputs |
| ml/training/evaluation/ | Pipeline-level evaluation | canonical stage asset | canonical | good | Under training/ vs ml/evaluation/ |
| docs/COMPILATION/README.md | Layer-2 index | canonical pointer | canonical | good | Links to DAG, archive/ROADMAP_L2_L3_L4 (historical), STAGE6_MUTATION_TAXONOMY |
| docs/LAYER2_COMPILATION_SPEC.md | Full Layer-2 spec | canonical | canonical | good | Stages, Stage-6C, Stage-7, Stage-8, freeze manifest |
| docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md | DAG, R-L1..R-L5, schema paths | canonical | canonical | good | ml/lineage/schemas/* |
| docs/STAGE_LAYOUT_CANONICAL.md | Stage-7 split, stage08 discovery, stage7 forwarding | supporting | non-canonical | good | Explains compiler vs freeze vs sft/stage7 |
| docs/PHASE_ALIGNMENT_TABLE_V0_1.md | Phase ↔ stage alignment | supporting | non-canonical | good | Stage-6 ≠ Phase-6 |

---

## 5. Layer-2 structural findings

Each finding uses: Finding; Why it is a problem; Severity; Recommended action; Action timing.

**Finding 1 — Dual “stage7” naming (pipeline Stage-7 vs sft/stage7)**  
- **Why it is a problem:** Canonical Stage-7 is the deterministic compiler (ml/training/compiler/compile_stage7.py) plus freeze orchestration (ml/training/pipeline/stage6/stage6c/freeze/). A separate directory `ml/training/sft/stage7/` hosts the CONF drift pipeline (conf_drift_pipeline.py, golden_exemplars_v1.jsonl, conf_to_des_drift.jsonl, etc.). Both use the name “stage7.” New contributors or scripts might assume sft/stage7 is the Stage-7 compiler or that the compiler lives under sft/stage7. REPOSITORY_STRUCTURE_AUDIT and ML_PIPELINE_AUDIT already note the split; STAGE_LAYOUT_CANONICAL explains forwarding. The overlap is naming-only but can cause confusion.  
- **Severity:** Medium (documented but naming overlap).  
- **Recommended action:** In docs (e.g. LAYER2_COMPILATION_SPEC or STAGE_LAYOUT_CANONICAL), add one sentence: “The directory ml/training/sft/stage7/ is the CONF-drift correction workflow bundle (tools and outputs); it is not the Stage-7 deterministic compiler, which lives in ml/training/compiler/ and ml/training/pipeline/stage6/stage6c/freeze/.” Optionally rename sft/stage7 to sft/conf_drift_bundle or similar in a later remediation phase.  
- **Action timing:** `later`.

**Finding 2 — Root-level Layer-2/3 artifact leakage**  
- **Why it is a problem:** Phase 0 identified `stage6c_ledger.jsonl`, `suite_traces.jsonl`, and `tail_stage6c_ledger.txt` at repository root. These are Stage-6C suite outputs that should be written under a designated output dir (e.g. ml/training/generated/stage6c_runs/<run_id>/ or an OUT variable). Their presence at root indicates that some invocations do not set or respect the output directory, or that docs/prompts (e.g. plan-stage6cPassToStage7Freeze.prompt.md) reference OUT without enforcing it. This is a pipeline/output-discipline issue, not a missing directory.  
- **Severity:** Medium (already in Phase 0; root leakage).  
- **Recommended action:** (1) Ensure all stage6c-run invocations and docs use a single OUT convention (e.g. ml/training/generated/stage6c_runs/<run_id>). (2) Add root-level artifact patterns to .gitignore if not already; relocate or remove root copies in a later phase.  
- **Action timing:** `later`.

**Finding 3 — ml/training/_build missing until prepare_exemplars.sh**  
- **Why it is a problem:** REPOSITORY_CONSTITUTION and prepare_exemplars.sh define the exemplar mirror at `ml/training/_build/exemplars/`. The directory does not exist until the script is run. Code that expects the mirror to exist (e.g. training or evaluation that reads from _build/exemplars) will fail until the script is executed. This is by design (mirror is build-time) but could be clarified in ml/README or training README so that “Layer-2 canonical inputs” explicitly state “exemplar mirror: ml/training/_build/exemplars (created by ml/scripts/prepare_exemplars.sh).”  
- **Severity:** Low (contract is clear; existence is build-time).  
- **Recommended action:** Add one line to ml/README or a Layer-2 “Getting started” note: “Before training, run ml/scripts/prepare_exemplars.sh to create ml/training/_build/exemplars from governance/golden-exemplars/Phases.”  
- **Action timing:** `later`.

**Finding 4 — Two evaluation roots (ml/evaluation/ and ml/training/evaluation/)**  
- **Why it is a problem:** ml/README lists ml/evaluation/; ML_PIPELINE_AUDIT notes evaluation under both ml/evaluation/ and ml/training/evaluation/ (and pipeline/stage6/stage6a POST_SFT_EVALUATION_PROTOCOL). The split is intentional (top-level vs pipeline-internal) but a new contributor may not know which to use for what.  
- **Severity:** Low (both documented; no conflict).  
- **Recommended action:** In ml/README or LAYER2_COMPILATION_SPEC, one sentence: “Evaluation: ml/evaluation/ for top-level analysis and reports; ml/training/evaluation/ for pipeline-internal evaluation scripts.”  
- **Action timing:** `later`.

**Finding 5 — Stage-7 compiler output path hardcoded**  
- **Why it is a problem:** compile_stage7.py uses DEFAULT_OUT_DIR = SCRIPT_DIR.parent / "generated" (i.e. ml/training/generated/). CI check_structure.py enforces that compiler output is generated/. Scripts and docs (e.g. conf_drift_pipeline.py, CONF_DES_DRIFT_AUDIT_v1.md) reference ml/training/generated/stage6c_runs and ml/training/pipeline/stage08/dataset. Changing ml/training/generated/ would require updating compiler, CI, and multiple doc/script references.  
- **Severity:** Low (path is stable and enforced; risk is future change).  
- **Recommended action:** None for this phase. If relocating generated outputs is ever planned, treat ml/training/generated/ as a path contract and update all references in a single change.  
- **Action timing:** `never touch without dedicated plan` for the path itself.

---

## 6. Layer-2 anchor clarity test

- **Is Layer-2 canonically anchored in one clear spine?** Yes. The spine is: docs/COMPILATION/README.md (Layer-2 index) → docs/LAYER2_COMPILATION_SPEC.md (full spec) and docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md (DAG/lineage); ml/ (directory); ml/README.md (namespace); compiler (Stage-7); pipeline/stage6 (Stage-6), stage6c/freeze (freeze), stage08 (Stage-8); lineage (schemas). MASTER_SYSTEM_SPEC and ARCHITECTURE_4_LAYER point to COMPILATION/README and ml/.

- **Do ml/, docs, and stage guides agree?** Yes. LAYER2_COMPILATION_SPEC describes Stage-1–Stage-8; pipeline has STAGE1_* through STAGE6_* docs and stage6a, stage6b, stage6c, stage08 dirs; compiler README and STAGE_LAYOUT_CANONICAL describe Stage-7 split. The only ambiguity is sft/stage7 vs pipeline Stage-7 (see Finding 1).

- **Are there multiple apparent “sources of truth”?** No. Stage definitions and DAG/lineage live in docs; implementation lives under ml/. No competing Layer-2 spec claims a different stage list or directory mapping.

- **Is the current structure understandable to a new contributor?** Largely yes, if they start from README → MASTER_SYSTEM_SPEC → docs/COMPILATION/README or LAYER2_COMPILATION_SPEC. They need to read STAGE_LAYOUT_CANONICAL or equivalent to understand Stage-7 (compiler + freeze) vs sft/stage7 and where evaluation lives.

---

## 7. Stage structure coherence test

- **Stage visibility:** Stage-1–Stage-5 are documented by STAGE1_*..STAGE5_* markdown under ml/training/pipeline/. Stage-6 is visible as pipeline/stage6/ with stage6a, stage6b, stage6c subdirs and mutation/ and stage6c_report. Stage-7 is split: compiler in ml/training/compiler/, freeze in stage6/stage6c/freeze/, forwarding in pipeline/stage7/. Stage-8 is pipeline/stage08/ with dataset, checkpoints, configs, logs, tests. All eight stages have corresponding surfaces and/or docs (per ML_PIPELINE_AUDIT).

- **Stage naming:** Directory names use lowercase and digits (stage6, stage08, stage6a, stage6b, stage6c). Docs use “Stage-6”, “Stage-6C”, “Stage-7”, “Stage-8”. NOMENCLATURE_AUDIT notes this as a minor inconsistency (dirs no hyphen, prose with hyphen); it does not affect ownership.

- **Substage visibility:** Stage-6 substages are clear: stage6a (single-step), stage6b (systemic), stage6c (agent-loop). Stage-8 sub-phases (08A–08H) are described in LAYER2_COMPILATION_SPEC; directory structure under stage08 is configs, dataset, checkpoints, logs, tests.

- **Input/output separation:** Compiler outputs go to ml/training/generated/ (golden_exemplars_v1.jsonl, dataset_manifest.json). Stage-6C run outputs go to ml/training/generated/stage6c_runs/<run_id>/ (or OUT). Freeze manifests under ml/training/freeze_manifests/stage6c/. Stage-8 dataset and checkpoints under pipeline/stage08/dataset and stage08/checkpoints. ARTIFACT_POLICY and verify_artifact_hygiene.sh forbid committing generated/, stage6c_ledger*.jsonl, suite_traces*.jsonl. Separation is clear; root leakage is the exception.

- **Filesystem reflects documented stage model:** Yes. The documented Stage-1–Stage-8 model is reflected in pipeline docs and dirs; Stage-7 is the only split (compiler + freeze + forwarding), and that split is documented.

**Conclusion:** Stage structure is **clear** with one **partially clear** area: sft/stage7 naming vs pipeline Stage-7.

---

## 8. Artifact-boundary separation test

- **Canonical assets vs generated outputs:** Canonical assets: governance exemplars (consumed via mirror _build/exemplars), lineage schemas (ml/lineage/schemas/), compiler and pipeline code, stage docs, configs (e.g. gating_config.yaml, stage08 configs). Generated: ml/training/generated/ (compiler JSONL/manifest, stage6c_runs), stage6c_ledger.jsonl, suite_traces.jsonl, freeze manifests under freeze_manifests/stage6c/, pipeline/stage08/checkpoints, ml/artifacts/checkpoints, ml/training/models/. Separation is clear; generated/ is explicitly append-only and gitignored-by-policy (verify_artifact_hygiene.sh).

- **Frozen outputs vs temporary experiment residue:** Frozen: freeze_manifests/stage6c/, FREEZE_CERTIFICATE* under pipeline and stage08, LAYER2_RELEASE_VERIFICATION.json. Temporary/experiment: ml/training/generated/stage6c_runs/<run_id> (per-run), ml/training/src/* (versioned train/eval scripts like v12–v17), sft/stage7 conf_drift outputs. ARTIFACT_POLICY distinguishes control-plane (tracked) vs data-plane (not tracked); stage6c ledgers/traces and checkpoints are data-plane. Placement is good; “experiment residue” in src/ is a mix of canonical scripts and versioned experiment code but does not blur artifact ownership.

- **Ledgers / traces / logs placement:** Ledgers and traces are intended under ml/training/generated/stage6c_runs/<run_id>/ or artifact store. Root-level stage6c_ledger.jsonl and suite_traces.jsonl are leakage. Logs: pipeline/stage08/logs/, and per-run logs in generated. Placement policy is clear; root is the only violation.

- **Artifact placement confusion:** No co-location of canonical and generated in the same directory in a confusing way. The only confusion risk is sft/stage7 holding both scripts and generated files (e.g. golden_exemplars_v1.jsonl, conf_to_des_drift.jsonl) in one bundle; this is a workflow bundle, not a canonical-source dir.

**Conclusion:** Artifact-boundary separation is **clear**; canonical vs generated vs frozen is documented and enforced. Root leakage is the main exception.

---

## 9. Governance-consumption boundary test

- **Are governance assets consumed by Layer-2 without duplicating doctrine ownership?** Yes. Layer-2 reads governance only: (1) profiles.py loads governance/CONSTITUTIONAL_MANIFEST_v1.0.md and docs/NON_NEGOTIABLE_INVARIANTS.md for constitution_v1 injection; (2) prepare_exemplars.sh copies governance/golden-exemplars/Phases to ml/training/_build/exemplars. No governance content is authored under ml/. REPOSITORY_CONSTITUTION states that training consumes the mirror, not governance directly.

- **Are governance exemplars mirrored in a disciplined way?** Yes. Single mirror path: ml/training/_build/exemplars. Script: ml/scripts/prepare_exemplars.sh. CI (check_no_exemplar_phases_under_ml.py) fails if ml/training/sft/exemplars/Phases exists, enforcing that Phases come from the mirror. sft/exemplars contains guides, status, and categories, not the Phases tree.

- **Do training assets risk becoming accidental governance source-of-truth competitors?** No. Training does not write to governance/. Golden exemplars in sft/stage7 (e.g. golden_exemplars_v1.jsonl) are Stage-7/Stage-8 dataset artifacts derived from the compiler or drift corrections, not the canonical Golden Exemplars doctrine in governance/golden-exemplars/.

**Conclusion:** Governance consumption is **clean reference** and **acceptable coupling**; no ambiguous overlap or structural concern.

---

## 10. Runtime-coupling boundary test

- **Does Layer-2 contain runtime-serving or runtime-enforcement concerns that do not belong to training/compilation?** No. Layer-2 contains compilation (doctrine → JSONL), mutation harness (Stage-6), freeze orchestration, and SFT training. Runtime enforcement (plan gate, authority validator, sandbox, ledger) lives in runtime/. Layer-2 produces artifacts (datasets, checkpoints, adapters) that may be consumed by runtime or observation; it does not implement enforcement. Code under ml/ does not implement plan-gate logic, sandbox execution, or ledger emission; it may reference phase labels (REF, CONF, DES) or dominance for injection/testing only.

**Conclusion:** Runtime overlap is **absent**; Layer-2 is compilation/training only. Boundary output (e.g. model artifacts) is acceptable.

---

## 11. Layer-2 Path Contract Register

| Path | Why path-sensitive | Referenced by | Risk if moved/renamed | Recommendation note |
|------|--------------------|---------------|------------------------|---------------------|
| ml/ | Layer-2 root | README, MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, Makefile ARTIFACTS | High | Do not move |
| ml/training/ | Training root | profiles.py (parents[6]), conf_drift_pipeline (parents[2]), compiler, pipeline, CI | High | Do not move |
| ml/training/generated/ | Compiler DEFAULT_OUT_DIR; stage6c_runs | compile_stage7.py, check_structure.py, verify_artifact_hygiene.sh, conf_drift_pipeline, CONF_DES_DRIFT_AUDIT | High | Do not move; CI enforces |
| ml/training/_build/exemplars/ | Exemplar mirror per REPOSITORY_CONSTITUTION | prepare_exemplars.sh, check_no_exemplar_phases_under_ml | High | Do not change path; create via script only |
| ml/training/compiler/compile_stage7.py | Stage-7 compiler | LAYER2_COMPILATION_SPEC, STAGE_LAYOUT_CANONICAL, freeze.py, stage7/__init__.py, check_structure.py | High | Do not move |
| ml/training/pipeline/stage6/stage6c/ | Stage-6C code, config, seeds, freeze | LAYER2_COMPILATION_SPEC, conf_drift_pipeline (config, seeds), freeze | High | Do not move |
| ml/training/pipeline/stage6/stage6c/freeze/ | Freeze orchestration | STAGE7_FREEZE_REFINEMENTS_PATCH, ML_PIPELINE_AUDIT, stage7 forwarding | High | Do not move |
| ml/training/pipeline/stage08/ | Stage-8 training, dataset discovery | LAYER2_COMPILATION_SPEC, conf_drift_pipeline (dataset path), STAGE_LAYOUT_CANONICAL | High | Do not move |
| ml/training/sft/stage7/ | CONF drift bundle | conf_drift_pipeline.py (all paths relative to _stage7_dir()), run_conf_drift_pipeline.sh, CONF_DES_DRIFT_AUDIT | Medium | Do not move without updating conf_drift_pipeline and docs |
| ml/training/freeze_manifests/stage6c/ | Freeze manifests | ARTIFACT_POLICY, ML_PIPELINE_AUDIT | Medium | Do not move |
| ml/lineage/schemas/ | Lineage schemas | COMPILATION_DAG_AND_LINEAGE_V0_1 | Medium | Do not move |
| ml/scripts/prepare_exemplars.sh | Exemplar mirror script | REPOSITORY_CONSTITUTION | Medium | Do not move; path to governance and _build is contract |
| governance/CONSTITUTIONAL_MANIFEST_v1.0.md | Read by profiles.py | profiles.py (repo_root / "governance/...") | High (L1 contract) | Do not move (Layer-1) |
| docs/NON_NEGOTIABLE_INVARIANTS.md | Read by profiles.py | profiles.py (repo_root / "docs/...") | High (L1 contract) | Do not move (Layer-1) |
| ml/artifacts/ | Makefile ARTIFACTS | Makefile | Medium | Do not move without updating Makefile |

---

## 12. Preliminary keep / clarify / move-later / do-not-touch classification

| Item / cluster | Preliminary classification | Rationale |
|----------------|----------------------------|------------|
| ml/ | do not touch without dedicated plan | Layer-2 root; path contract |
| ml/training/compiler/, pipeline/stage6/, stage6c/freeze/, pipeline/stage08/ | do not touch without dedicated plan | Canonical stage implementation |
| ml/training/generated/ | do not touch (path); do not commit (content) | DEFAULT_OUT_DIR; hygiene gate |
| ml/training/_build/exemplars/ | do not touch path | Mirror contract |
| ml/lineage/schemas/ | keep | Lineage contract |
| ml/scripts/prepare_exemplars.sh | keep | Mirror contract |
| ml/training/sft/stage7/ | clarify later | Name vs pipeline Stage-7; document or rename |
| ml/evaluation/ vs ml/training/evaluation/ | clarify later | Document which is for what |
| Root stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt | move later | Relocate to generated/ or delete; Phase 0 |

---

## 13. Root leakage back-reference

| Root artifact | Likely origin | Structural leakage? | Severity | Note |
|---------------|---------------|---------------------|----------|------|
| stage6c_ledger.jsonl | Stage-6C suite run (ledger output) | Yes — should be under ml/training/generated/stage6c_runs/<run_id>/ or OUT | Medium | Phase 0; gitignored by pattern |
| suite_traces.jsonl | Stage-6C suite run (traces) | Yes — same as above | Medium | Phase 0; gitignored |
| tail_stage6c_ledger.txt | Debug tail of ledger | Yes — same run output | Low | Phase 0 |
| ledger.db | Runtime sandbox ledger (Layer-3) | Yes — runtime artifact at root | Medium | Phase 0; not Layer-2 but often grouped with stage6c outputs |
| plan-stage6cPassToStage7Freeze.prompt.md | References OUT/stage6c_ledger.jsonl | Indirect — prompt assumes OUT; if OUT is root, outputs land at root | Low | Document OUT convention |

**Interpretation:** Root leakage indicates that some Stage-6C (or runtime) runs did not direct outputs into ml/training/generated/ or a dedicated OUT directory. The Layer-2 structure itself (generated/, artifact policy, hygiene script) is correct; the issue is invocation/output-dir discipline and possibly default behavior when OUT is unset. Remediation: enforce OUT in all invocations and docs; add root patterns to .gitignore; relocate or remove root copies in a later phase.

---

## 14. Immediate conclusions

- **Does Layer-2 have a clean canonical structure?** Yes. Layer-2 is anchored under ml/ with a clear doc spine and stage-aligned layout. Stage-1–Stage-8 are represented; compiler and freeze locations are documented; artifact boundaries and governance consumption are contract-bound.

- **What are the biggest Layer-2 structural risks?** (1) Naming overlap between pipeline Stage-7 and sft/stage7. (2) Root-level artifact leakage (Phase 0). (3) _build missing until prepare_exemplars.sh (clarification only).

- **Which Layer-2 items are dangerous to touch?** ml/ root; ml/training/generated/ path; ml/training/_build/exemplars path; ml/training/compiler/compile_stage7.py; ml/training/pipeline/stage6/stage6c/ and freeze/; ml/training/pipeline/stage08/; governance and docs paths read by profiles.py; prepare_exemplars.sh.

- **What must be clarified later?** (1) Explicit sentence that sft/stage7 is CONF drift bundle, not Stage-7 compiler. (2) Exemplar mirror: create with prepare_exemplars.sh. (3) Evaluation: ml/evaluation/ vs ml/training/evaluation/ one-liner.

- **What should the next audit phase be?** Per the approved plan, **Phase 4 — Layer-3 runtime structure audit** (runtime/ layout, enforcement surfaces, plan/ledger, IDE/shadow, governance boundary enforcement).

---

## 15. Non-goals

This phase did **not**:

- Move, rename, or edit any file under ml/ or docs.
- Change code, configs, or training pipelines.
- Archive or delete generated artifacts.
- Fix path inconsistencies or root leakage.
- Propose repo-wide cleanup or remediation.
- Audit Layer-1, Layer-3, or Layer-4 internals beyond references needed to assess boundaries and path contracts.

---

## Phase 3 result summary

### 1. Artifact created
- **path:** `docs/audit/LAYER2_COMPILATION_STRUCTURE_AUDIT.md`

### 2. Canonical Layer-2 spine assessment
- **primary anchor:** ml/ (directory) and docs/LAYER2_COMPILATION_SPEC.md (full Stage-1–Stage-8 and freeze spec).
- **main Layer-2 directory:** ml/ — contains artifacts, datasets, evaluation, lineage, scripts, training; README defines namespace and boundaries.
- **stage docs/guides:** docs/COMPILATION/README.md, docs/LAYER2_COMPILATION_SPEC.md, docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md, docs/STAGE_LAYOUT_CANONICAL.md; ml/training/pipeline/STAGE* docs; ml/training/compiler/README.md; ml/training/pipeline/stage6/README.md and stage6a/6b/6c READMEs.
- **governance-consumed inputs:** governance/golden-exemplars/Phases (via prepare_exemplars.sh → ml/training/_build/exemplars); governance/CONSTITUTIONAL_MANIFEST_v1.0.md and docs/NON_NEGOTIABLE_INVARIANTS.md (read by ml/training/pipeline/stage6/stage6c/injections/profiles.py).
- **overall clarity:** clear — one spine; ml/ and docs agree; only sft/stage7 vs pipeline Stage-7 naming is partially clear.

### 3. Major findings
- **finding 1:** Dual “stage7” naming — pipeline Stage-7 (compiler + stage6c/freeze) vs ml/training/sft/stage7/ (CONF drift bundle); document or rename later.
- **finding 2:** Root-level Layer-2/3 artifact leakage (stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt); enforce OUT and relocate later.
- **finding 3:** ml/training/_build/exemplars missing until prepare_exemplars.sh is run; add one-line “getting started” note later.

### 4. Stage coherence result
- **status:** Clear; all eight stages have surfaces and/or docs; Stage-7 split (compiler + freeze + forwarding) is documented.
- **key evidence:** ML_PIPELINE_AUDIT stage table; pipeline/stage6/stage6a, stage6b, stage6c; compiler/compile_stage7.py; stage6c/freeze/; pipeline/stage08/; docs/STAGE_LAYOUT_CANONICAL.md.
- **conclusion:** Stage structure is coherent; only sft/stage7 naming is partially clear.

### 5. Artifact-boundary result
- **status:** Clear separation of canonical assets, generated outputs, and frozen outputs; policy and CI enforce.
- **key evidence:** ml/training/generated/ (DEFAULT_OUT_DIR; verify_artifact_hygiene.sh); ARTIFACT_POLICY.md; freeze_manifests/stage6c/; lineage schemas; _build/exemplars as mirror only.
- **conclusion:** Artifact boundaries are well defined; root leakage is the only violation.

### 6. Governance/runtime boundary result
- **governance:** Clean reference — Layer-2 reads governance and docs only; mirror contract; no doctrine authored under ml/.
- **runtime:** Absent — Layer-2 has no runtime-serving or runtime-enforcement code; boundary output (artifacts) only.

### 7. Path-sensitive Layer-2 items identified
- **number:** 15 (paths in Path Contract Register, including governance/docs paths consumed by Layer-2).
- **notable examples:** ml/, ml/training/generated/, ml/training/_build/exemplars, ml/training/compiler/compile_stage7.py, ml/training/pipeline/stage6/stage6c/, ml/training/pipeline/stage6/stage6c/freeze/, ml/training/pipeline/stage08/, ml/training/sft/stage7/, ml/scripts/prepare_exemplars.sh, governance/CONSTITUTIONAL_MANIFEST_v1.0.md, docs/NON_NEGOTIABLE_INVARIANTS.md.

### 8. Root leakage back-reference
- **notable root artifacts:** stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt (Layer-2/3); ledger.db (Layer-3).
- **interpretation:** Pipeline/output-dir discipline (OUT or generated/stage6c_runs) not always applied; structure and policy are correct; remediation is to enforce OUT and relocate or remove root copies.

### 9. Final status
**PHASE 3 LAYER2 AUDIT READY**
