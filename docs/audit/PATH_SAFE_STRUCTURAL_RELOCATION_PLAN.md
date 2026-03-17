# Phase 12 — Path-Safe Structural Relocation Plan

**Repository:** m-coder  
**Phase:** 12 — Batch E planning (path-safe structural relocation)  
**Date:** 2026-03-15  
**Mode:** Planning only. No moves, renames, or structural execution.

---

## 1. Purpose and scope

This document is the **planning-only** deliverable for Phase 12. It does **not** execute any structural moves, renames, or relocations. It uses the completed audit phases (0–6) and completed remediation batches (A–D) as the governing baseline to determine: which remaining structural issues are worth fixing physically; which were solved by clarification alone; which path clusters are plausible move candidates vs dangerous; what order future execution batches should follow; what validation and rollback discipline apply. This is a **decision document** for future structural work, not a cleanup script.

---

## 2. Executive assessment

- **Whether more physical relocation is actually justified:** Yes in a **narrow** sense only. Most structural ambiguity was resolved by Batches A–D (spine clarification, .gitignore and prompt-file moves, naming/legacy clarification, report convention). The only remaining items that may justify physical relocation are: (1) root-generated artifact files still on disk at root (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt)—already gitignored where applicable in Batch B; (2) cuda-pytorch_test.py at root; (3) optionally the root long-form guide, only with a dedicated link-update migration. Any other relocation (report consolidation, observation/layer path changes, canonical doc moves) is **not** justified; clarification and convention are sufficient.

- **Biggest remaining structural issues:** (1) Root-generated artifacts (four files) still physically at root; .gitignore prevents commit but does not relocate them. (2) cuda-pytorch_test.py at root with unclear ownership. (3) Root long-form guide (motadata-coder-a-complete-guide_v1.7.md) still at root—role clarified in Batch A; optional move would require updating README and ARCHITECTURE_4_LAYER links.

- **Biggest relocation risks:** (1) **Path-contract density** — Many paths are referenced by code (profiles.py, observation/ingest/validate.py, prepare_exemplars.sh, conf_drift_pipeline, compile_stage7.py, plan_gate_service/tests, verify_artifact_hygiene.sh, stage6c orchestrator/freeze/reporting), docs, and CI. Moving any path-contract path without a full reference scan and synchronized update will break builds or contracts. (2) **Blast radius** — Relocating root artifacts requires confirming that no code assumes root path for ledger or stage6c outputs; tests use tmp paths but docs/milestones reference generic paths. (3) **Layer roots and canonical docs** — governance/, ml/, runtime/, observation/, docs/MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, LIVE_ROADMAP_TRACKER, and code-referenced paths (NON_NEGOTIABLE_INVARIANTS, runtime schemas, ml/training/generated, _build/exemplars) must not be moved without a migration-grade plan.

---

## 3. Structural issue inventory after Batches A–D

| Issue | Status after Batches A–D | Still warrants physical move? |
|-------|---------------------------|--------------------------------|
| Root-generated artifacts (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt) | .gitignore updated (Batch B); files still on disk at root | Optional relocate after reference scan; not required for correctness |
| Root prompt files (plan-*.prompt.md) | Moved to archive/planning/ (Batch B) | No; done |
| cuda-pytorch_test.py at root | Unchanged; ownership unclear | Optional move to scripts/tests/ml or reclassify |
| Root long-form guide (motadata-coder-a-complete-guide_v1.7.md) | Role clarified in Batch A (supplement; MASTER_SYSTEM_SPEC canonical) | Optional move only with dedicated link-update migration |
| Report/docs placement (docs/reports, status, status_reports, runtime/verification) | Convention defined in docs/README.md (Batch D); historical tolerance | No; convention only; no consolidation recommended |
| observation/ vs runtime/observation/ | Documented in LAYER4_OBSERVATION_SPEC (Batch A); dual index in Batch C | No; keep as-is |
| OBSERVATION vs observation naming | Clarified in Batch C; no case normalization | No move |
| plangate vs plan_gate_stub vs policies | Clarified in LAYER3_RUNTIME_SPEC (Batch C) | No move |
| Stage-7 vs sft/stage7 | Clarified in LAYER2_COMPILATION_SPEC (Batch C) | No move |
| Governance / ml / runtime / observation path-contract paths | Audited; do-not-touch register in Phase 6 | Never move without migration-grade plan |
| archive/planning | Batch B placed prompt files here | Sufficient; no further refinement needed |

---

## 4. Relocation candidacy matrix

| Item / cluster | Current role | Current problem | Structural action class | Risk | Recommended future action | Likely destination / handling | Notes |
|----------------|--------------|-----------------|-------------------------|------|----------------------------|-------------------------------|-------|
| ledger.db (root) | Runtime ledger artifact | At root; gitignored (Batch B) | MOVE_CANDIDATE | Medium | Relocate only after full reference scan; else leave on disk | .spool or runtime-owned dir if code/docs updated | Docs/milestones use generic paths; tests use tmp; env MOTADATA_EXECUTE_LEDGER_PATH |
| stage6c_ledger.jsonl (root) | Stage-6C output | At root; already gitignored by pattern | MOVE_CANDIDATE | Low | Optional relocate after scan; else leave | ml/training/generated/stage6c_runs or OUT | conf_drift_pipeline and stage6c code reference OUT/generated |
| suite_traces.jsonl (root) | Stage-6C traces | At root; already gitignored | MOVE_CANDIDATE | Low | Optional relocate; else leave | Same as stage6c_ledger | Same refs |
| tail_stage6c_ledger.txt (root) | Debug output | At root; gitignored (Batch B) | MOVE_CANDIDATE | Low | Optional relocate; else leave | Same as above or delete | No code refs found |
| cuda-pytorch_test.py (root) | One-off script | Unclear ownership at root | MOVE_CANDIDATE | Low | Reclassify or move to scripts/tests/ml in one small batch | scripts/tests/ml or keep with comment | No path contract in code |
| motadata-coder-a-complete-guide_v1.7.md (root) | Long-form Golden Exemplars guide | At root; role clarified (Batch A) | MOVE_ONLY_WITH_DEDICATED_MIGRATION | Medium | Only if explicit decision; then update README + ARCHITECTURE_4_LAYER links | docs/ or docs/governance/ | README and ARCHITECTURE_4_LAYER reference by name |
| docs/reports, docs/status, docs/status_reports, docs/runtime/verification | Report/convention locations | Convention defined (Batch D) | NO_MOVE_NEEDED | Low | Leave as-is; no consolidation | — | Historical tolerance; new docs follow convention |
| observation/ vs runtime/observation/ | Dual Layer-4 trees | Documented (Batch A, C) | KEEP_AS_IS | Low | No structural change | — | Documented dual role |
| governance/, CONSTITUTIONAL_MANIFEST, golden-exemplars | Layer-1 doctrine | Path-contract (profiles.py, prepare_exemplars) | NEVER_RECOMMEND_MOVE | Critical | Do not move | — | Code hardcodes paths |
| docs/NON_NEGOTIABLE_INVARIANTS, LAYER1_GOVERNANCE_SPEC | Governance restatement | profiles.py reads paths | NEVER_RECOMMEND_MOVE | Critical | Do not move | — | Code refs |
| ml/training/generated, _build/exemplars, compiler, stage6c, freeze, stage08, sft/stage7 | Layer-2 paths | Code/CI references | NEVER_RECOMMEND_MOVE | Critical | Do not move | — | compile_stage7, conf_drift_pipeline, verify_artifact_hygiene, prepare_exemplars |
| runtime/schemas, ide/schemas, state/schemas, shadow/schemas | Runtime schemas | observation/ingest/validate.py paths | NEVER_RECOMMEND_MOVE | Critical | Do not move | — | Code refs |
| runtime/plangate, sandbox, ledger, observation, plan_gate_stub, plan_gate_service | Runtime implementation | Imports and tests | NEVER_RECOMMEND_MOVE | Critical | Do not move | — | Core runtime |
| observation/, observation/ingest, baseline, judge_drift_suite | Layer-4 boundary | Docs and runtime schema refs | NEVER_RECOMMEND_MOVE | Critical | Do not move | — | Path contract |
| docs/MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, LIVE_ROADMAP_TRACKER, layer specs | Canonical spine | Many doc links | NEVER_RECOMMEND_MOVE | Critical | Do not move | — | Link targets |
| AGENT_EXECUTION_RULES.md (root), README.md, Makefile, .gitignore | Root canonical | Repo entry and contracts | NEVER_RECOMMEND_MOVE | Critical | Do not move | — | Root contract |
| archive/planning | Legacy prompts | Batch B moved prompt files here | KEEP_AS_IS | Low | No further change | — | Sufficient |

---

## 5. Root residuals assessment

- **ledger.db:** Generated runtime artifact; at root; gitignored (Batch B). **Classification:** MOVE_CANDIDATE. **Rationale:** Relocation would improve root clarity; code uses tmp or env; docs use generic paths. **Destination (if moved):** .spool or a runtime-owned directory; any doc/milestone that mentions "ledger.db" at root must be updated or made generic. **Precondition:** Full grep; update or document references. **Risk:** Medium (doc/milestone references). **Rollback:** Easy if single batch.

- **stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt:** Generated Stage-6C outputs; at root; gitignored. **Classification:** MOVE_CANDIDATE. **Rationale:** Optional relocate to ml/training/generated or OUT; conf_drift_pipeline and stage6c code reference OUT/generated paths—moving root copies does not change code behavior but removes root clutter. **Destination:** ml/training/generated/stage6c_runs or leave on disk. **Precondition:** Confirm no script assumes root path for these filenames. **Risk:** Low. **Rollback:** Easy.

- **cuda-pytorch_test.py:** One-off script at root; no path contract in code. **Classification:** MOVE_CANDIDATE. **Rationale:** Reclassify or move to scripts/tests/ml improves root clarity. **Destination:** scripts/tests/ml or keep with one-line comment. **Precondition:** None material. **Risk:** Low. **Rollback:** Easy.

- **motadata-coder-a-complete-guide_v1.7.md:** Long-form guide; role clarified in Batch A. **Classification:** MOVE_ONLY_WITH_DEDICATED_MIGRATION. **Rationale:** README and ARCHITECTURE_4_LAYER reference it; move requires updating those links and any other references. **Destination:** docs/ or docs/governance/ only after link-update plan. **Precondition:** Full link grep; coordinated update. **Risk:** Medium. **Rollback:** Medium (link updates must be reverted too).

- **AGENT_EXECUTION_RULES.md, README.md, Makefile, .gitignore, governance/, ml/, runtime/, observation/, docs/:** Canonical root and layer roots. **Classification:** NEVER_RECOMMEND_MOVE. **Rationale:** Path-contract supremacy; many references. No relocation justified for vanity.

---

## 6. Documentation placement assessment

- **docs/reports, docs/status, docs/status_reports, docs/runtime/verification:** Convention defined in docs/README.md (Batch D). Roles are: reports = milestone/integration/merge/freeze; status = snapshots/session summaries; status_reports = progress/findings/planning; runtime/verification = audits/E2E/constitutional reference. **Classification:** NO_MOVE_NEEDED. **Rationale:** Convention and historical tolerance remove ambiguity; physical consolidation would add risk (many internal links and references) with low structural benefit. **Recommendation:** Leave placement as-is; new documents follow convention. No batch for report consolidation.

- **Legacy or weakly placed docs elsewhere:** No specific doc was identified as both weakly placed and worth relocating in this plan. If discovered later, treat as MOVE_ONLY_WITH_DEDICATED_MIGRATION with link scan.

---

## 7. Layer-specific relocation assessment

### Layer-1 (governance)

- **Safe to leave:** governance/, CONSTITUTIONAL_MANIFEST_v1.0.md, REPOSITORY_CONSTITUTION.md, golden-exemplars/, README.md, docs/governance/ pointer layer. All are path-contract or canonical.
- **Might be moved later:** Nothing. No Layer-1 path is a move candidate.
- **Dangerous:** All of governance/ and docs references to it (profiles.py, prepare_exemplars.sh hardcode paths). Do not move without migration-grade plan.

### Layer-2 (ml)

- **Safe to leave:** ml/, ml/training/, compiler/, pipeline/stage6/stage6c/, freeze/, pipeline/stage08/, sft/stage7/, lineage/schemas/, freeze_manifests/, artifacts/, _build/exemplars (created by script), generated/ (output dir). All are code/CI-referenced.
- **Might be moved later:** Nothing under ml/ that is a safe move candidate; any move would require updating compile_stage7.py, conf_drift_pipeline, verify_artifact_hygiene, check_structure, ARTIFACT_POLICY, etc.
- **Dangerous:** ml/training/generated/, ml/training/_build/exemplars, ml/training/compiler/compile_stage7.py, ml/training/pipeline/stage6/stage6c/, ml/scripts/prepare_exemplars.sh. Never move without dedicated migration.

### Layer-3 (runtime)

- **Safe to leave:** runtime/, runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/, runtime/plangate/, runtime/sandbox/, runtime/ledger/, runtime/observation/, runtime/plan_gate_stub/, runtime/plan_gate_service/, runtime/context/, runtime/ask_service/, runtime/execute_service/. All are imports or path-referenced (observation/ingest uses schema paths).
- **Might be moved later:** Nothing. No runtime path is a casual move candidate.
- **Dangerous:** All paths listed above; observation/ingest/validate.py and tests reference runtime schema paths; orchestrator and execute_service use plangate, sandbox, ledger. Never move without migration-grade plan.

### Layer-4 (observation)

- **Safe to leave:** observation/, observation/ingest/, observation/baseline/, observation/judge_drift_suite/, runtime/observation/ (library). Dual structure is documented.
- **Might be moved later:** Nothing. observation/ is Layer-4 root; runtime/observation/ is library; both are path-contract.
- **Dangerous:** observation/ and observation/ingest (docs and plan_gate_stub reference; ingest uses runtime schema paths). Never move without migration-grade plan.

---

## 8. High-risk do-not-touch register

The following clusters must **not** be moved or renamed except under a **dedicated migration-grade plan** (full reference scan, synchronized updates, rollback plan, owner review):

1. **Root canonical:** AGENT_EXECUTION_RULES.md, README.md, Makefile, .gitignore.
2. **Layer-1:** governance/, governance/CONSTITUTIONAL_MANIFEST_v1.0.md, governance/golden-exemplars/, governance/REPOSITORY_CONSTITUTION.md, governance/README.md; docs/governance/README.md, docs/governance/AGENT_EXECUTION_RULES.md; docs/LAYER1_GOVERNANCE_SPEC.md, docs/NON_NEGOTIABLE_INVARIANTS.md (profiles.py reads path).
3. **Layer-2:** ml/, ml/training/, ml/training/generated/, ml/training/_build/exemplars/, ml/training/compiler/compile_stage7.py, ml/training/pipeline/stage6/stage6c/, ml/training/pipeline/stage6/stage6c/freeze/, ml/training/pipeline/stage08/, ml/training/sft/stage7/, ml/scripts/prepare_exemplars.sh, ml/lineage/schemas/, ml/training/freeze_manifests/, ml/artifacts/.
4. **Layer-3:** runtime/, runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/, runtime/plangate/, runtime/sandbox/, runtime/ledger/, runtime/observation/, runtime/plan_gate_stub/, runtime/plan_gate_service/, runtime/context/, runtime/ask_service/, runtime/execute_service/.
5. **Layer-4:** observation/, observation/ingest/, observation/baseline/, observation/judge_drift_suite/.
6. **Canonical docs:** docs/MASTER_SYSTEM_SPEC.md, docs/ARCHITECTURE_4_LAYER.md, docs/LIVE_ROADMAP_TRACKER.md, docs/LAYER2_COMPILATION_SPEC.md, docs/LAYER3_RUNTIME_SPEC.md, docs/LAYER4_OBSERVATION_SPEC.md, docs/OBSERVATION/README.md, observation/README.md, docs/runtime/README.md, docs/COMPILATION/README.md, docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md, docs/JETBRAINS_PLUGIN_FLOW_V0_1.md, docs/SHADOW_MODE_PROTOCOL_V0_1.md, docs/PHASE_ALIGNMENT_TABLE_V0_1.md.
7. **Cross-cutting:** .dvc, .spool (Makefile/scripts/runtime reference).

---

## 9. Recommended future execution batches

Only two execution batches are recommended; both are optional and preconditioned.

### Batch E-exec: Root artifact relocation (optional)

- **Name:** Root artifact relocation.
- **Purpose:** Physically relocate root-generated artifact files (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt) from repository root to an agreed artifact home, or remove from repo if they are local-only, after confirming no references assume root path.
- **Scope:** Only these four files. Optionally include cuda-pytorch_test.py move in same batch if desired.
- **Excluded:** Root guide; all path-contract paths; docs/ and layer dirs; .gitignore (already updated in Batch B).
- **Prerequisite checks:** Full grep for ledger.db, stage6c_ledger, suite_traces, tail_stage6c in code, docs, scripts; list all references; update or document any that assume root path; run tests and verify_artifact_hygiene before move.
- **Success criteria:** No broken references; tests pass; verify_artifact_hygiene passes; root no longer contains these artifact files (or they are explicitly documented as local-only and ignored).

### Batch E-exec-2: Optional cuda-pytorch and/or root guide (only with explicit decision)

- **Name:** Optional root script and guide relocation.
- **Purpose:** Move cuda-pytorch_test.py to scripts/tests/ml (or reclassify in place) and/or move motadata-coder-a-complete-guide_v1.7.md to docs/ or docs/governance/ with link updates.
- **Scope:** Only these items; only if explicitly decided.
- **Excluded:** Everything else.
- **Prerequisite checks:** For root guide: full link grep (README, ARCHITECTURE_4_LAYER, any other refs); plan link updates in one commit; for cuda-pytorch: confirm no imports or scripts assume root path.
- **Success criteria:** All links updated; tests pass; no broken references.

No other batches are recommended. Report consolidation, observation/layer path changes, and canonical doc moves are **not** recommended; clarification and convention are sufficient.

---

## 10. Validation and rollback framework

### Pre-move validation

For any future relocation batch:

1. **Path reference scan:** Grep code, docs, tests, scripts, CI configs, schemas, and runbooks for the path(s) to be moved. Produce a list of all references.
2. **Import/build/test impact check:** Identify any imports, build targets, or test fixtures that use the path. Run full test suite and build before change.
3. **Docs link / runbook reference scan:** Identify all doc links and runbook steps that reference the path. Plan updates.
4. **Git move feasibility:** Prefer `git mv` to preserve history; confirm no uncommitted changes that would conflict.
5. **Owner review:** For path-contract or cross-cutting paths, require explicit review before execution.

### Post-move validation

1. **Targeted tests:** Run tests that touch the moved area (e.g. runtime tests if ledger path changed, stage6c tests if stage6c outputs moved).
2. **Grep/path-reference verification:** Re-grep for old path; confirm no remaining references (or that remaining refs are intentional generics).
3. **Documentation link validation:** Check that updated links resolve; run link checker if available.
4. **Build/runtime checks:** Run full build and, if applicable, runtime smoke checks.

### Rollback rule

- **Single-batch rollback expectation:** Every execution batch must be reversible in one logical step. If the batch spans multiple commits, rollback means reverting those commits or applying a single reverse-move commit.
- **Preferred rollback method:** `git revert` of the batch commit(s), or a single commit that reverses all moves (git mv back to original paths and restores any updated references).
- **Failed move batch:** A batch is failed if, after the move, any reference is broken, any test fails that passed before, or any build/runtime check fails. On failure, roll back the entire batch immediately; do not partial-fix forward.

---

## 11. Immediate conclusions

- **What should never be moved:** All paths in the high-risk do-not-touch register (§8): root canonical files, governance/, ml/ critical paths (generated, _build/exemplars, compiler, stage6c, freeze, stage08, sft/stage7, prepare_exemplars.sh), runtime/ (schemas, plangate, sandbox, ledger, observation, plan_gate_stub, plan_gate_service), observation/ and observation/ingest, canonical docs (MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, LIVE_ROADMAP_TRACKER, layer specs, OBSERVATION/README, observation/README, runtime/README, COMPILATION/README, and other linked specs). Moving any of these without a dedicated migration-grade plan is not justified.

- **Best first actual move batch (if any):** **Batch E-exec (root artifact relocation)** — but only after the prerequisite reference scan and precondition checks. Relocate the four root-generated artifact files (and optionally cuda-pytorch_test.py) in one small batch; validate; then stop. If the scan reveals hardcoded root assumptions, do not move; leave artifacts on disk with .gitignore (current state).

- **Areas that should remain clarified-only indefinitely:** Report/document locations (docs/reports, docs/status, docs/status_reports, docs/runtime/verification)—convention only, no consolidation. Observation dual tree (observation/ and runtime/observation/)—documented, no structural change. Layer roots and canonical spine paths—no move. Naming (OBSERVATION vs observation, plangate vs stub, Stage-7 vs sft/stage7)—clarified only, no renames.

---

## 12. Non-goals

This phase did **not**:

- Move or rename any file or directory.
- Edit any existing documentation except by creating this plan artifact.
- Update .gitignore.
- Delete anything.
- Propose broad repo redesign.
- Reopen or rewrite Batches A–D.
- Execute any structural relocation.
- Change imports, scripts, tests, or links.
- Relocate reports or archive material.
- Normalize naming or path casing.

---

## Phase 12 result

### 1. Artifact created
- **path:** docs/audit/PATH_SAFE_STRUCTURAL_RELOCATION_PLAN.md

### 2. Executive assessment
- **relocation still justified:** Yes in a narrow sense only—optional root artifact relocation and optional cuda-pytorch/root-guide moves; most structure is clarified-only.
- **biggest remaining issue:** Root-generated artifacts (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt) still on disk at root; cuda-pytorch_test.py and root guide as optional later moves.
- **biggest risk:** Path-contract density; moving any code-referenced path without full scan and synchronized update will break builds or contracts.

### 3. Main relocation classifications
- **item 1:** Root artifact files (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt) — MOVE_CANDIDATE; optional relocate after reference scan; risk Low–Medium.
- **item 2:** cuda-pytorch_test.py — MOVE_CANDIDATE; reclassify or move to scripts/tests/ml; risk Low.
- **item 3:** governance/, ml/ critical paths, runtime/ schemas and implementation, observation/, canonical docs — NEVER_RECOMMEND_MOVE; risk Critical.

### 4. Best future execution batch
- **batch name:** Root artifact relocation (Batch E-exec).
- **purpose:** Relocate the four root-generated artifact files (and optionally cuda-pytorch_test.py) after prerequisite reference scan and precondition checks; no path-contract paths touched.

### 5. High-risk do-not-touch examples
- **example 1:** governance/CONSTITUTIONAL_MANIFEST_v1.0.md and docs/NON_NEGOTIABLE_INVARIANTS.md — profiles.py and prepare_exemplars.sh hardcode paths.
- **example 2:** runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/ — observation/ingest/validate.py and ingest/cli use these paths; ml/training/generated/, ml/training/compiler/compile_stage7.py, ml/training/pipeline/stage6/stage6c/ — compile_stage7, conf_drift_pipeline, verify_artifact_hygiene, CI reference.

### 6. Validation / rollback result
- **validation framework:** Pre-move: path reference scan, import/build/test impact check, docs link/runbook scan, git move feasibility, owner review when appropriate. Post-move: targeted tests, grep/path verification, doc link validation, build/runtime checks.
- **rollback rule:** Single-batch rollback; prefer git revert or one reverse-move commit; failed batch = any broken reference or failing test after move → roll back entire batch.

### 7. Final status
**BATCH E PLAN READY**
