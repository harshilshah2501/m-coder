# Layer-2 — Comprehensive ML Compilation Spec

**Entry point:** [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)

## Purpose

Layer-2 is the judgment compiler. It turns constitutional doctrine into trainable artifacts. It does not define doctrine; it exercises semantics under stress. **Layer-2 may exercise semantics but never redefine them.** Constitutional semantics are read-only reference.

**Directory:** `ml/`

---

## Stage Axis (Pipeline Workflow)

Pipeline stages describe *preparation workflow*, not constitutional semantics. Constitutional Phase axis and Pipeline Stage axis are orthogonal. Stage-6 (mutation harness) is not Constitutional Phase-6 (REACH).

| Stage | Meaning |
|-------|---------|
| Stage-1 | Structural mapping |
| Stage-2 | Artifact extraction |
| Stage-3 | Base exemplar mapping |
| Stage-4 | Variant generation |
| Stage-5 | Variant stability gate |
| Stage-6 | Mutation harness (pre-SFT stress) |
| Stage-7 | Dataset compilation (deterministic freeze) |
| Stage-8 | SFT training |

---

## Stage Breakdown

### Stage-1: Structural Mapping

Maps governance structure to compilation inputs.

### Stage-2: Artifact Extraction

Extracts exemplars and boundary artifacts for compilation.

### Stage-3: Base Exemplar Mapping

Motadata base exemplar mapping. Bases derived from doctrine (e.g., BASE-001 through BASE-025).

### Stage-4: Variant Generation

Generates stress variants per base. Target: uniform variants per base. Variant count derived deterministically; non-uniform variants per base blocks freeze.

### Stage-5: Variant Stability Gate

Validates that variants do not soften boundaries or introduce phase drift. Phase-4 variant summary must PASS; no softened language; boundary exact.

### Stage-6: Mutation Harness

Pre-SFT stress testing. Sub-stages:

- **Stage-6A:** Single-step mutation harness (schemas, docs)
- **Stage-6B:** Systemic hardening rewrite
- **Stage-6C:** Agent-loop mutation harness — multi-step stress testing prior to freeze

### Stage-6C — Agent-Loop Mutation

- Exercises Plan → Edit → Test → Revise loops, multi-file modification, tool-augmented reasoning, deadline pressure, Planner/Executor/Critic compositions
- Belongs to ML Compilation; is a pipeline mutation stage, not a constitutional phase
- Exercises already-locked constitutional behavior under realistic agent loops
- **CONF runtime enforcement:** REF and CONF are governed runtime phases. When expected_phase == CONF, deterministic rendering replaces model output with a fixed scaffold (DETERMINISTIC_CONF_RENDER). This cured CONF→DES drift (severity 80 S0, CONF→DES 0, S2/S3 0) after SFT-only attempts did not suffice.

### Collapse Vector Taxonomy (Stage-6C)

Loop-induced collapse vectors (doctrine-locked; Layer-2 does not add or remove):

- L1 — Incremental CONF Softening
- L2 — REF Fatigue Collapse
- L3 — Boundary Relocation via Abstraction
- L4 — Tool Authority Drift (capability ≠ permission)
- L5 — Success Bias Override (tests passing ≠ boundary removal)
- L6 — Critic Override of Governance Dominance

Pass criteria: no REF collapses under iteration; no irreversible boundary relocation; no CONF→execution drift; no MIX collapse to single-phase; meaningful collapse rate ≤ threshold; all collapses classified and ledgered.

### Stage-7: Deterministic Dataset Compilation

**Compiler:** `ml/training/compiler/compile_stage7.py` — doctrine → JSONL

**Freeze:** `ml/training/pipeline/stage6/stage6c/freeze/` — orchestration, gates, manifest, split determinism

**Note:** The path `ml/training/sft/stage7/` is the CONF drift workflow bundle (tools and outputs), not the Stage-7 compiler.


Freeze manifest gates SFT. Freeze must require: tier2.pass AND tier3.pass; tier2_non_dummy AND tier3_non_dummy pass; non_dummy_canonical_runs_count > 0; S3_count == 0; no T-BYPASS, T-ALIAS, T-DOMINANCE-FLIP in canonical non-dummy evaluation.

### Stage-8: SFT Training

Sub-phases: 08A (pilot) → 08B (hyperparameter) → 08C (geometry) → 08D (retrain) → 08E (audit) → 08F (loss refinement) → 08G (stability) → 08H (compile freeze).

---

## Determinism Guarantees

- Identical inputs → identical JSONL + identical corpus hash
- Stable JSON canonicalization (sorted keys, UTF-8)
- Deterministic split (sorted base_ids; canonical order assertion)
- Float serialization: 6 decimal places for collapse_rate_snapshot and BDA summaries

---

## Freeze Manifest Contract

Required fields (per STAGE7_FREEZE_REFINEMENTS_PATCH): source_git_sha, corpus_hash, bases_count, variants_count, total_rows, phase_distribution, stage6c_suite_configuration_hash, collapse_rate_snapshot (dual-scope canonical/non_dummy), mutation_taxonomy_version, adapter_param_signature_snapshot, generated_at_utc, stage6c_pass_reference, freeze_block_reason, split_hashes.

---

## Invariance Audit

- boundary_phrase_hash per boundary_hashing.v0.1
- dataset_row.phase_semantic_label must match referenced variant/base
- dataset_row must have base_id and variant_id
- freeze_allowed true requires fail_count == 0

---

## Failure Modes

- Variant count mismatch; non-uniform variants per base
- Boundary mismatch; multiple irreversible anchors
- Missing phase; duplicate exemplar IDs
- Stage-6C PASS absent; non-dummy gates not evaluable
- Nondeterministic ordering

---

## Definition of Done (Layer-2)

- Bases mapped; variants stable
- Stage-6 mutation harness passes (tier2, tier3, non-dummy)
- Deterministic freeze complete; manifest locked
- SFT training complete; post-SFT revalidation acceptable
- No rollback criteria triggered

---

## What Layer-2 Must Never Do

- Redefine constitutional phase semantics
- Alter collapse taxonomy or thresholds
- Author governance doctrine
- Implement runtime enforcement
