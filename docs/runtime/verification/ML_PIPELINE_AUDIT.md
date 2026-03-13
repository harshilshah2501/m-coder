# ML Pipeline Audit

**Report date:** 2026-03-13  
**Canonical state reference:** [SYSTEM_CANONICAL_STATE_AUDIT.md](SYSTEM_CANONICAL_STATE_AUDIT.md)  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## 1. Scope

Audit Layer-2 stage structure (Stage-1 through Stage-8), freeze artifacts, training artifacts, evaluation artifacts, and compiler/pipeline structure. Verify stage surfaces, Stage-6 family, Stage-7 compile/freeze, Stage-8 training/validation, and release verification artifacts.

---

## 2. Stage-by-Stage Presence Check

| Stage | Expected | Found | Path / notes |
|-------|----------|-------|--------------|
| Stage-1 | Structural mapping | Yes | `ml/training/pipeline/STAGE1_STRUCTURAL_MAPPING.md`, `STAGE1A_BOUNDARY_DETECTION.md` |
| Stage-2 | Artifact extraction | Yes | `STAGE2_ARTIFACT_EXTRACTION.md` |
| Stage-3 | Base exemplar mapping | Yes | `STAGE3_BASE_EXEMPLAR_MAPPING.md` |
| Stage-4 | Variant generation | Yes | `STAGE4_VARIANT_GENERATION.md` |
| Stage-5 | Variant stability | Yes | `STAGE5_VARIANT_STABILITY_REPORT.md` |
| Stage-6 | Mutation harness (6A/6B/6C) | Yes | `stage6/stage6a/`, `stage6/stage6b/`, `stage6/stage6c/`; STAGE6_* docs, mutation reports |
| Stage-7 | Compiler + freeze | Yes | `ml/training/compiler/compile_stage7.py`; `stage6/stage6c/freeze/` (freeze.py, cli.py); `stage7/` forwarding |
| Stage-8 | SFT training | Yes | `stage08/` — train.py, train_stage08D.py, enforce_split_stage08D.py, _path_utils.py, tests |

All eight stages have corresponding surfaces and/or docs.

---

## 3. Artifact Findings

- **LAYER2_RELEASE_VERIFICATION.json:** Present at `ml/artifacts/LAYER2_RELEASE_VERIFICATION.json`.
- **Freeze manifests:** `ml/training/freeze_manifests/stage6c/` contains pointer, manifest, summary (stage6c_import_demo.*). Stage6c freeze code: `ml/training/pipeline/stage6/stage6c/freeze/`.
- **Pipeline certificates:** `ml/training/pipeline/FREEZE_CERTIFICATE_v1.json`; stage08 FREEZE_CERTIFICATE_STAGE8_* observed in directory listing.
- **Artifacts dir:** `ml/artifacts/` — checkpoints, datasets, exports, REGISTRY.md, MODEL_RELEASE*.json.

---

## 4. Freeze and Evaluation Findings

- **Freeze:** Compiler in `ml/training/compiler/`; freeze orchestration in `stage6/stage6c/freeze/` (freeze.py, cli). Freeze manifests under `ml/training/freeze_manifests/stage6c/`. Determinism and dataset discovery documented in STAGE_LAYOUT_CANONICAL.
- **Evaluation:** `ml/evaluation/` contains analysis, diffs, reports, results, and test scripts (e.g. comprehensive_model_evaluation.py, kpi2_truncation_test.py, phase_c_completion_probe.py). Pipeline-level evaluation also under `ml/training/evaluation`, `ml/training/pipeline/stage6/stage6a/` (POST_SFT_EVALUATION_PROTOCOL).

---

## 5. Structural Risks

- **Stage-6B:** Directory present with README only; placeholder/systemic hardening. Documented in plan; no missing artifact claim.
- **Stage-7 logic split:** Compiler in `ml/training/compiler/`, freeze in `stage6/stage6c/freeze/`; STAGE_LAYOUT_CANONICAL documents this. No structural violation.

---

## 6. Pass/Fail Verdict

**PASS.** Stage-1 through Stage-8 surfaces and docs present; Stage-6 family (6A, 6B, 6C) and mutation harness present; Stage-7 compiler and freeze artifacts present; Stage-8 training entry points and tests present; LAYER2_RELEASE_VERIFICATION.json and freeze manifests present; evaluation surfaces under ml/evaluation and pipeline.
