# Phase 6 — Cross-Layer Inconsistency and Path-Contract Consolidation Audit Report

**Repository:** m-coder  
**Audit phase:** Phase 6 only (cross-layer inconsistency and path-contract consolidation, read-only)  
**Date:** 2026-03-15  
**Scope:** Consolidation of Phases 0–5 into a single cross-layer view of naming inconsistencies, duplicate structural truth, report sprawl, layer-boundary shadowing, root leakage, and path-contract risk. No moves, renames, edits, or remediation performed.

**Update (2026-03):** `docs/status_reports/` was **removed** from the repository. Mentions of that path describe layout at audit time.

---

## 1. Purpose and scope

This document is the deliverable for **Phase 6** of the m-coder structural audit. It is a **read-only cross-layer structural audit** that consolidates evidence from Phases 0–5. It does not move or rename files, edit docs or code, refactor, clean up artifacts, fix inconsistencies, or start remediation. The audit identifies cross-layer structural inconsistencies, naming conflicts, duplicate-truth and report-sprawl patterns, canonical-entry competition, layer-boundary shadowing, root-leakage consolidation, and path-contract risk; it groups findings into preliminary remediation-affinity batches without producing a final remediation plan.

---

## 2. Executive assessment

- **Overall cross-layer structural health:** Moderate. Each layer (governance, ml, runtime, observation) is structurally coherent in isolation (Phases 2–5). The **remaining problems are mostly cross-cutting**: (1) **Canonical docs spine** does not document the observation/ vs runtime/observation/ split; (2) **Naming and path conventions** are inconsistent across docs and code (OBSERVATION vs observation, mixed-case docs dirs, dual indices); (3) **Report/verification sprawl** across docs/reports, docs/status, docs/status_reports, docs/runtime/verification with no single stated convention; (4) **Root artifact leakage** and prompt-file clutter weaken root-as-contract; (5) **Duplicate structural truth** in governance restatements (LAYER1_GOVERNANCE_SPEC, NON_NEGOTIABLE_INVARIANTS) and in milestone docs carrying architecture truth (M4.x for runtime/observation/). No single issue is **critical** in the sense of conflicting ownership or broken contracts; the risks are **drift**, **discovery**, and **remediation accidents** if changes are made without a consolidated view.

- **Are the repo’s remaining problems mostly local or cross-cutting?** **Cross-cutting.** Local issues exist (e.g. runtime/README.md incomplete, policies/ vs plangate clarification) but the themes that affect multiple layers are: canonical spine clarity (docs + L4), naming/index consistency (docs + L4 + root), report convention (docs), path contracts (root, L1, L2, L3, L4, docs), and root hygiene (root + L2/L3 outputs).

- **Biggest cross-layer structural risks:** (1) **Observation split and dual index** — Layer-4 has two trees (observation/, runtime/observation/) and two index paths (docs/OBSERVATION/README, observation/README) with case mismatch; spine does not state the split; touching one without the other risks link/ownership confusion. (2) **Path-contract density** — Many paths are referenced by code, docs, tests, scripts, or CI; moving or renaming without updating all references will break builds or contracts. (3) **Duplicate structural truth** — Governance phase semantics restated in LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS; runtime/observation/ ownership stated only in M4.x milestones; later edits could drift. (4) **Root leakage and artifact-home** — Generated artifacts at root (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt) indicate missing artifact-home convention across L2/L3; remediation must align with ml/training/generated and runtime spool discipline.

---

## 3. Consolidated cross-layer issue inventory

Structured inventory of issues that cut across layers or appear in multiple phases. Category, severity, and remediation affinity are from the classification model.

| Issue / pattern | Category | Layers / areas involved | Severity | Why it matters | Likely remediation affinity | Notes |
|-----------------|----------|-------------------------|----------|----------------|-----------------------------|-------|
| observation/ vs runtime/observation/ split not in spine | canonical ambiguity | L4, docs | High | Readers cannot infer two-tree Layer-4 structure; M4.x carries truth | observation split clarification | Phase 1, 4, 5 |
| Dual observation index (docs/OBSERVATION/README vs observation/README) | naming inconsistency | L4, docs, root | Medium | Case mismatch; two “Layer-4 index” locations; link drift risk | naming consistency; observation split | Phase 1, 5 |
| OBSERVATION vs observation case | naming inconsistency | docs, root | Medium | Case-sensitive systems; MASTER_SYSTEM_SPEC links to OBSERVATION | naming consistency | Phase 0, 1 |
| Report sprawl (reports, status, status_reports, runtime/verification) | report / verification sprawl | docs | Medium | No single convention for completion/verification reports | report convention consolidation | Phase 1 |
| Root artifact leakage (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_*) | root artifact leakage | root, L2, L3 | High | Root should not hold generated outputs; ledger.db not gitignored | root hygiene; artifact-home | Phase 0, 3 |
| Root prompt/planning files (plan-*.prompt.md) | root artifact leakage | root | Medium | Blur canonical vs temporary at root | root hygiene | Phase 0 |
| Competing root guide (motadata-coder-a-complete-guide_v1.7.md) | canonical-entry competition | root, docs | Medium | Secondary entrypoint; clarify subordination to MASTER_SYSTEM_SPEC | canonical docs spine | Phase 0, 1 |
| docs/README.md as broad index | canonical-entry competition | docs | Medium | May be mistaken for canonical entry; one line cites MASTER_SYSTEM_SPEC | canonical docs spine | Phase 1 |
| Governance restatement (LAYER1_GOVERNANCE_SPEC, NON_NEGOTIABLE_INVARIANTS) | duplicate structural truth | L1, docs | Medium | Drift risk if edited without updating manifest | canonical docs spine; governance | Phase 2 |
| Dual AGENT_EXECUTION_RULES (root vs docs/governance) | duplicate structural truth | L1, docs | Low | Pointer intentional; content drift risk if docs copy updated | legacy/clarification | Phase 0, 2 |
| Milestone docs (M4.x) carry runtime/observation/ structural truth | duplicate structural truth | L4, docs/runtime | Medium | Architecture should live in spine, not only in milestones | observation split; canonical docs | Phase 1, 4, 5 |
| plangate vs plan_gate_stub vs plan_gate_service naming | naming inconsistency | L3 | Low | Intentional (stub/service vs implementation); one-sentence clarification helps | legacy/stub clarification | Phase 4 |
| policies/ vs plangate (two authority/irreversibility surfaces) | legacy residue / scaffolding ambiguity | L3 | Medium | policies used only by tests; plangate is production; role unclear | legacy/stub clarification | Phase 4 |
| Stage-7 vs sft/stage7 (pipeline Stage-7 vs CONF drift bundle) | naming inconsistency | L2 | Medium | Same “stage7” name; different roles; document or rename | naming consistency | Phase 3 |
| runtime/README.md omits subpackages | convention gap | L3 | Medium | New contributors miss plangate, sandbox, observation, etc. | canonical docs spine | Phase 4 |
| Mixed-case docs dirs (OBSERVATION, COMPILATION, CONTRACTS vs governance, runtime) | naming inconsistency | docs | Low | Path/link consistency on case-sensitive systems | naming consistency | Phase 1 |
| governance/ status/report files (PHASE_STATUS_REPORT, etc.) | convention gap | L1 | Low | Could be mistaken for doctrine; clarify as non-doctrine | governance clarification | Phase 2 |
| _build/exemplars missing until prepare_exemplars.sh | convention gap | L2 | Low | Contract clear; existence is build-time; one-line note helps | canonical docs / L2 clarify | Phase 3 |
| Path contracts: governance, ml, runtime schemas, observation ingest | path-contract risk | L1, L2, L3, L4 | High | Many paths hardcoded in code or docs; move/rename breaks contracts | do-not-touch path-contract cluster | All phases |

---

## 4. Cross-layer naming inconsistency test

- **Major naming inconsistencies:**
  - **OBSERVATION vs observation:** MASTER_SYSTEM_SPEC and MIGRATION_NOTE link to docs/OBSERVATION/README.md (uppercase). Root README and SHADOW_MODE_PROTOCOL reference observation/README.md (lowercase package). On case-sensitive systems these are different paths. **Where:** docs, root. **Contract-risky:** Yes for link resolution; cosmetic for semantics.
  - **plangate vs plan_gate_stub vs plan_gate_service:** Runtime uses `plangate` (one word) for the implementation package and `plan_gate_stub` / `plan_gate_service` (underscore) for stub and HTTP service. NOMENCLATURE_AUDIT notes this. **Where:** L3. **Contract-risky:** No; intentional. **Confusing:** Slightly — which is “the” plan-gate for production vs protocol is documented but could be one sentence in spine.
  - **status vs status_reports vs reports vs runtime/verification:** Completion/verification/status docs live in docs/reports, docs/status, docs/status_reports, docs/runtime/verification. No single convention. **Where:** docs. **Contract-risky:** No for code; **convention gap** for future report placement.
  - **Stage-7 vs sft/stage7:** Pipeline Stage-7 is compiler + stage6c/freeze; ml/training/sft/stage7/ is CONF drift bundle. Same “stage7” name. **Where:** L2, docs. **Contract-risky:** No; **confusing** until documented.
  - **COMPILATION, CONTRACTS, OBSERVATION (uppercase) vs governance, runtime (lowercase):** Mixed-case docs subdirs. **Where:** docs. **Contract-risky:** Only if links assume case; **cosmetic** otherwise.

- **Assessment:** Naming inconsistencies are **not critical**; they are **confusing** or **convention-weak**. The only one that is **contract-risky** is OBSERVATION vs observation if links or scripts assume a specific case. Remediation: document relationship, optionally normalize case in links; add one-sentence clarifications for stub/plangate and Stage-7/sft/stage7.

---

## 5. Cross-layer duplicate-truth test

- **Where structural truth is duplicated:**
  - **Governance phase semantics:** Defined in governance/CONSTITUTIONAL_MANIFEST_v1.0.md. Restated (phase table, dominance, boundary) in docs/LAYER1_GOVERNANCE_SPEC.md and docs/NON_NEGOTIABLE_INVARIANTS.md. Both reference the manifest; neither claims to be the source. **Verdict:** **Acceptable restatement** with **drift risk** if LAYER1_SPEC or NON_NEGOTIABLE is edited without updating the manifest. Recommendation: add “source of truth: governance/CONSTITUTIONAL_MANIFEST_v1.0.md” at top of restating docs.
  - **AGENT_EXECUTION_RULES:** Root is canonical; docs/governance/AGENT_EXECUTION_RULES.md is pointer. **Verdict:** **Acceptable pointering**; content drift risk if someone edits the docs copy. Low severity.
  - **Observation split (observation/ = boundary, runtime/observation/ = library):** Truth appears **only** in M4.1–M4.6 and branch_execution_notes, not in LAYER4_OBSERVATION_SPEC, ARCHITECTURE_4_LAYER, observation/README, or docs/OBSERVATION/README. **Verdict:** **Drift-prone** — structural truth in milestone docs, not spine. Add one sentence to spine.
  - **Runtime/observation/ module list:** Only in M4.x milestone docs. **Verdict:** Same as above; **milestone docs carrying architecture’s job**.

- **Assessment:** Duplicate structural truth is **mostly harmless restatement or pointering** (governance, AGENT_EXECUTION_RULES). The **drift-prone** case is the observation split and runtime/observation/ ownership living only in milestone docs. Remediation: add canonical sentence to spine; optionally add “source of truth” labels to governance restating docs.

---

## 6. Report / verification sprawl test

- **Report clusters:**
  - **docs/reports/:** M4X merge, readiness, verification, freeze reports (e.g. M4X_MAIN_MERGE_READINESS.md, M4X_INTEGRATION_VERIFICATION_REPORT.md).
  - **docs/status/:** Progress, session summaries (e.g. status/README.md).
  - **docs/status_reports/:** Findings, planning (e.g. JANUARY_2_2026_PROGRESS.md).
  - **docs/runtime/verification/:** Audits, constitutional reference, completion (e.g. SYSTEM_MASTER_AUDIT_REPORT.md, ML_PIPELINE_AUDIT.md, NOMENCLATURE_AUDIT.md, REPOSITORY_STRUCTURE_AUDIT.md).

- **Are they cleanly separable by role?** Partially. **docs/reports/** tends toward merge/verification/freeze; **docs/runtime/verification/** is runtime/structure audits; **docs/status/** and **docs/status_reports/** are progress/session. Overlap: “verification” and “report” are used in multiple places; no single rule like “all completion reports go to X.”

- **Conventions missing?** Yes. No canonical doc states “completion reports live in docs/reports” or “verification audits live in docs/runtime/verification” or “status/session summaries live in docs/status.” So **placement** is observable but **convention** is implicit.

- **Problem: placement, convention, or both?** **Both.** Placement is scattered; convention is unstated. Remediation could: (1) document a single convention (e.g. “completion/verification → docs/reports or docs/runtime/verification by scope”); (2) or leave placement as-is and only add a **classification** note in MASTER_SYSTEM_SPEC or a docs README. Consolidation (moving files) is **not** required for this phase; **clarification** is.

---

## 7. Path-contract consolidation register

Consolidated from Phases 0–5. Deduplicated; contract type and affinity group added. **Risk** and **recommendation** preserved from phase registers.

| Path / cluster | Why path-sensitive | Referenced by | Contract type | Risk if moved/renamed | Affinity group | Recommendation note |
|----------------|--------------------|---------------|---------------|------------------------|----------------|----------------------|
| AGENT_EXECUTION_RULES.md (root) | Canonical execution rules; protected surfaces §3 | docs/governance, verification, M4.5 | docs, code | High | do-not-touch | Do not move; many references assume root |
| governance/ | Layer-1 root; protected §3 | MASTER_SYSTEM_SPEC, docs/governance, ml profiles, prepare_exemplars.sh | docs, code | High | do-not-touch | Do not move |
| governance/CONSTITUTIONAL_MANIFEST_v1.0.md | Canonical phase doctrine | MASTER_SYSTEM_SPEC, LAYER1_SPEC, ml profiles.py, stage6a | docs, code | High | do-not-touch | Hardcoded in profiles.py |
| governance/golden-exemplars/ | Golden Exemplars; consumption contract | REPOSITORY_CONSTITUTION, prepare_exemplars.sh (Phases) | docs, code | High | do-not-touch | Mirror contract |
| governance/REPOSITORY_CONSTITUTION.md | Structural governance | SYSTEM_GOVERNANCE_AUDIT, REPOSITORY_STRUCTURE_AUDIT | docs | Medium | do-not-touch | Do not move |
| governance/README.md | Layer-1 index | MASTER_SYSTEM_SPEC, spine | docs | Medium | canonical spine | Do not move |
| docs/governance/README.md, docs/governance/AGENT_EXECUTION_RULES.md | Layer-1 pointer layer | MASTER_SYSTEM_SPEC, audits | docs | Medium / Low | canonical spine | Pointer only; do not move without updating link |
| docs/LAYER1_GOVERNANCE_SPEC.md, docs/NON_NEGOTIABLE_INVARIANTS.md | Governance spec; invariants; ml profiles.py | MASTER_SYSTEM_SPEC, profiles.py | docs, code | High (NON_NEGOTIABLE) / Medium | do-not-touch, canonical spine | profiles.py reads NON_NEGOTIABLE path |
| README.md (root) | Repo entry | All users, docs | docs | High | do-not-touch | Do not move |
| docs/MASTER_SYSTEM_SPEC.md | Canonical spec entry | README, verification, E2E-flow, ARCHITECTURE_4_LAYER | docs | High | do-not-touch | Link target for many docs |
| docs/ARCHITECTURE_4_LAYER.md | Layer mapping | MASTER_SYSTEM_SPEC, README, verification | docs | High | do-not-touch | Do not move |
| docs/LIVE_ROADMAP_TRACKER.md | Live milestone source of truth | README, verification, reports | docs | High | do-not-touch | Do not move |
| docs/LAYER2_COMPILATION_SPEC.md, docs/LAYER3_RUNTIME_SPEC.md, docs/LAYER4_OBSERVATION_SPEC.md | Layer specs | MASTER_SYSTEM_SPEC | docs | High | do-not-touch | Do not move |
| docs/OBSERVATION/README.md | Layer-4 index (docs) | MASTER_SYSTEM_SPEC, MIGRATION_NOTE, E2E-flow | docs | Medium | observation split; naming | Case-sensitive; clarify vs observation/README |
| observation/README.md | Layer-4 package README | Root README, SHADOW_MODE_PROTOCOL, plan_gate_stub | docs | Medium | observation split | Do not move |
| docs/runtime/README.md | Layer-3 index | MASTER_SYSTEM_SPEC, runtime docs | docs | High | do-not-touch | Do not move |
| docs/COMPILATION/README.md | Layer-2 index | MASTER_SYSTEM_SPEC, MIGRATION_NOTE | docs | Medium | do-not-touch | Uppercase; do not rename without plan |
| docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md, docs/JETBRAINS_PLUGIN_FLOW_V0_1.md, docs/SHADOW_MODE_PROTOCOL_V0_1.md | Plan/ledger, IDE, shadow | MASTER_SYSTEM_SPEC, runtime README | docs | High | do-not-touch | Do not move |
| docs/PHASE_ALIGNMENT_TABLE_V0_1.md, docs/NON_NEGOTIABLE_INVARIANTS.md | Phase alignment; invariants | MASTER_SYSTEM_SPEC | docs | Medium | do-not-touch | Do not move |
| ml/ | Layer-2 root | README, MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, Makefile | docs, code, CI | High | do-not-touch | Do not move |
| ml/training/ | Training root | profiles.py, conf_drift_pipeline, compiler, pipeline, CI | code | High | do-not-touch | Do not move |
| ml/training/generated/ | DEFAULT_OUT_DIR; stage6c_runs | compile_stage7.py, check_structure.py, verify_artifact_hygiene.sh, conf_drift_pipeline | code, CI | High | do-not-touch | CI enforces |
| ml/training/_build/exemplars/ | Exemplar mirror | prepare_exemplars.sh, check_no_exemplar_phases_under_ml | code, CI | High | do-not-touch | Create via script only |
| ml/training/compiler/compile_stage7.py | Stage-7 compiler | LAYER2_SPEC, STAGE_LAYOUT_CANONICAL, freeze.py, stage7/__init__.py, check_structure.py | docs, code, CI | High | do-not-touch | Do not move |
| ml/training/pipeline/stage6/stage6c/, stage6c/freeze/ | Stage-6C, freeze | LAYER2_SPEC, conf_drift_pipeline, freeze, ML_PIPELINE_AUDIT | docs, code | High | do-not-touch | Do not move |
| ml/training/pipeline/stage08/ | Stage-8 | LAYER2_SPEC, conf_drift_pipeline, STAGE_LAYOUT_CANONICAL | docs, code | High | do-not-touch | Do not move |
| ml/training/sft/stage7/ | CONF drift bundle | conf_drift_pipeline.py, run_conf_drift_pipeline.sh, CONF_DES_DRIFT_AUDIT | code, docs | Medium | naming / L2 clarify | Do not move without updating conf_drift_pipeline |
| ml/scripts/prepare_exemplars.sh | Exemplar mirror script | REPOSITORY_CONSTITUTION | code | Medium | do-not-touch | Path to governance and _build is contract |
| ml/lineage/schemas/, ml/training/freeze_manifests/stage6c/, ml/artifacts/ | Lineage; freeze; Makefile ARTIFACTS | COMPILATION_DAG_AND_LINEAGE, ARTIFACT_POLICY, Makefile | docs, code | Medium | do-not-touch | Do not move without updating refs |
| runtime/ | Layer-3 root | ARCHITECTURE_4_LAYER, MASTER_SYSTEM_SPEC, all runtime imports | docs, code | High | do-not-touch | Do not move |
| runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/ | Plan/ledger/IDE/state/shadow schemas; AGENT_EXECUTION_RULES §3 | observation/ingest/validate.py, docs, verification | code, docs, schemas | High | do-not-touch | Protected; observation/ingest path refs |
| runtime/plangate/, runtime/sandbox/, runtime/ledger/, runtime/state/, runtime/orchestrator/ | Core runtime loop | orchestrator, execute_service, sandbox, ledger, observation (trace_builder, etc.), tests | code | High | do-not-touch | Do not move |
| runtime/plan_gate_stub/ | Stub + golden_outputs | plan_gate_service/handlers, plan_gate_service/tests | code, tests | High | do-not-touch | Golden paths in tests |
| runtime/plan_gate_service/ | HTTP daemon | runtime/README, docs, plugin | docs, code | Medium | do-not-touch | Do not move |
| runtime/observation/ | Layer-4 library | runtime/tests, trace_builder, summary_queries, reconciliation, report_runtime_summary | code | High | do-not-touch; observation split | Document in spine |
| runtime/context/, runtime/ask_service/, runtime/execute_service/ | Context engine; services | ask_service, tests | code | Medium | do-not-touch | Do not move |
| observation/ | Layer-4 boundary root | README, MASTER_SYSTEM_SPEC (as OBSERVATION in docs), plan_gate_stub | docs | High | do-not-touch | Keep at root |
| observation/ingest/, observation/baseline/, observation/judge_drift_suite/ | Layer-4 CLIs | docs/OBSERVATION/README, observation/README, SHADOW_MODE_PROTOCOL | docs, code | High | do-not-touch | observation/ingest uses runtime schema paths |
| Makefile, .gitignore | DVC targets; ignore rules | scripts, CI, docs | scripts, CI | High | do-not-touch | REPO_ROOT, artifact hygiene |
| .dvc, .spool | DVC config; runtime spool | Makefile, scripts, .gitignore, runtime | scripts, code | Medium | do-not-touch | Do not move without plan |
| ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt | Root leakage (generated) | Docs/examples reference ledger.db; gitignore patterns | mixed | High if at root | root hygiene | Relocate or .gitignore; do not rely on root |
| motadata-coder-a-complete-guide_v1.7.md (root) | Golden Exemplars guide | README, ARCHITECTURE_4_LAYER | docs | Medium if moved | canonical spine | Clarify role; optional move later |

**Count:** 45+ path/cluster entries (consolidated; some paths appear in multiple phases and are merged above). **Most dangerous:** Root AGENT_EXECUTION_RULES.md; governance/ and governance/CONSTITUTIONAL_MANIFEST_v1.0.md and governance/golden-exemplars/; docs/NON_NEGOTIABLE_INVARIANTS.md (code ref in profiles.py); runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/ (code ref in observation/ingest); ml/training/generated/, ml/training/_build/exemplars; ml/training/compiler/compile_stage7.py; runtime/plangate/, runtime/sandbox/, runtime/ledger/; docs/MASTER_SYSTEM_SPEC.md, docs/ARCHITECTURE_4_LAYER.md, docs/LIVE_ROADMAP_TRACKER.md.

---

## 8. Canonical-entry competition test

- **Where multiple entrypoints compete:**
  - **Root guide vs canonical spec:** motadata-coder-a-complete-guide_v1.7.md at root is referenced by README as “Golden Exemplars guide” and by ARCHITECTURE_4_LAYER. It functions as a **secondary entrypoint**. The documented canonical chain is README → MASTER_SYSTEM_SPEC → layer indices. **Harmful?** Medium — competes for “start here”; clarify that MASTER_SYSTEM_SPEC is the single spec entry.
  - **docs/README.md vs canonical spine:** docs/README.md is titled “Documentation Index” and describes a broad directory structure; it has one line referencing MASTER_SYSTEM_SPEC. **Harmful?** Medium — readers opening docs/ first may treat it as the doc entry. **Remediation theme:** canonical docs spine clarifications (add “canonical entry: root README → MASTER_SYSTEM_SPEC”).
  - **Dual observation indices:** docs/OBSERVATION/README.md (Layer-4 index in docs) and observation/README.md (Layer-4 package README). MASTER_SYSTEM_SPEC links to OBSERVATION/README; root README links to observation/README. **Harmful?** Medium — two “Layer-4 index” locations; case mismatch. **Remediation theme:** observation split clarification; naming consistency.
  - **Verification docs vs canonical layer specs:** docs/runtime/verification/* contains audits and completion reports that reference canonical spine. They do **not** compete as entrypoints; they **reference** them. **Harmful?** No. **Remediation theme:** report convention (where verification reports live).
  - **Milestone docs vs canonical docs:** M4.x milestones list runtime/observation/ modules and thus carry **structural truth** that should live in LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER. **Harmful?** Yes — architecture ownership inferred from milestones, not spine. **Remediation theme:** observation split clarification; canonical docs spine.

- **Assessment:** Canonical-entry competition is **moderate**. No **critical** conflict (no two docs claim to be the canonical authority for the same contract). Clarification and one-sentence additions to spine resolve the issues.

---

## 9. Layer-boundary shadowing test

- **runtime/observation/:** Layer-4 implementation library colocated under runtime/. **Classification:** **Acceptable but under-documented.** Code and ownership are clear (Layer-4 library consuming runtime ledger/sandbox). The name “runtime/observation” does not imply wrong ownership; the **docs** do not state that it is Layer-4. Phases 4 and 5 concluded: legitimate Layer-4 library; split clean in code; add one sentence to spine.
- **Governance materials mirrored into Layer-2:** governance/golden-exemplars/Phases → ml/training/_build/exemplars via prepare_exemplars.sh. **Classification:** **Acceptable and well-signaled.** REPOSITORY_CONSTITUTION states the mirror contract; training consumes mirror, not governance directly. No ambiguity.
- **Runtime schemas consumed by Layer-4:** observation/ingest/validate.py and ingest/cli.py use runtime/schemas, runtime/ide/schemas, runtime/shadow/schemas as **file paths** (read-only) for validation. **Classification:** **Acceptable and well-signaled.** Layer-4 does not import runtime packages; it only loads schema JSON files. Disciplined coupling.
- **Governance manifest + invariants read by Layer-2:** ml/training/pipeline/stage6/stage6c/injections/profiles.py reads governance/CONSTITUTIONAL_MANIFEST_v1.0.md and docs/NON_NEGOTIABLE_INVARIANTS.md. **Classification:** **Acceptable and well-signaled.** Read-only; no doctrine authored in ml/.

**Conclusion:** No **structurally ambiguous** or **structural concern** shadowing. All cases are **acceptable**; the only one **under-documented** is runtime/observation/.

---

## 10. Root-leakage consolidation test

- **Root clutter items (from Phase 0 and later):**
  - **ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt:** Generated outputs. **Local residue only?** No — they are **symptoms of missing artifact-home convention**. Phase 3: pipeline/output-dir discipline (OUT or ml/training/generated/stage6c_runs) not always applied. Phase 0: ledger.db not in .gitignore. **Deeper layout ambiguity?** No — the **correct** homes (ml/training/generated, runtime spool) exist; the issue is invocation/default OUT. **Remediation batch:** root hygiene; artifact-home cleanup (enforce OUT, add .gitignore, relocate or remove root copies).
  - **plan-artifactSegregation.prompt.md, plan-stage6c-ref-sanitizer.prompt.md, plan-stage6cPassToStage7Freeze.prompt.md:** Prompt/planning working docs. **Local residue only.** **Remediation batch:** root hygiene (move to docs/planning or archive).
  - **cuda-pytorch_test.py:** One-off script; unclear ownership. **Local residue only.** **Remediation batch:** root hygiene (reclassify or move to scripts/tests/ml).
  - **motadata-coder-a-complete-guide_v1.7.md:** Long-form guide; competing entrypoint. **Symptom of canonical-entry competition**, not artifact leakage. **Remediation batch:** canonical docs spine (clarify role); optional move later.

- **Assessment:** Root leakage is **partly local residue** (prompt files, cuda-pytorch_test) and **partly missing artifact-home convention** (ledger, stage6c_ledger, suite_traces, tail_*). Remediation should **batch** root hygiene (gitignore, relocate artifacts, move prompt files) with **artifact-home** documentation (OUT convention, where generated outputs must go).

---

## 11. Preliminary remediation affinity map

Do **not** treat this as the final remediation plan. Group findings into **likely future batches** for when remediation is approved.

| Affinity batch | Kinds of issues that belong there | Source phases |
|----------------|-----------------------------------|----------------|
| **Canonical docs spine clarifications** | Add observation/ vs runtime/observation/ sentence to LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER; add “source of truth: governance/CONSTITUTIONAL_MANIFEST” to LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS; add “canonical entry: README → MASTER_SYSTEM_SPEC” to docs/README.md; clarify root guide vs MASTER_SYSTEM_SPEC; runtime/README.md add missing subpackages or pointer to docs | 1, 2, 4, 5 |
| **Root hygiene / artifact-home cleanup** | Add ledger.db and tail_* to .gitignore; relocate or remove ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt from root; move plan-*.prompt.md to docs/planning or archive; reclassify or move cuda-pytorch_test.py; document OUT convention for stage6c runs | 0, 3 |
| **Report convention consolidation** | Document where completion vs status vs verification reports live (e.g. in MASTER_SYSTEM_SPEC or docs README); optionally consolidate or leave placement as-is with classification only | 1 |
| **Naming consistency clarification** | Document or fix OBSERVATION vs observation (link target and case); document dual observation index relationship; optionally normalize docs dir case; add one sentence for stub vs plangate and for Stage-7 vs sft/stage7 | 1, 4, 5, 3 |
| **Observation split clarification** | Add one canonical sentence: observation/ = boundary/CLI, runtime/observation/ = runtime-consumed library; ensure spine (not only M4.x) records runtime/observation/ as Layer-4; dual index clarification | 1, 4, 5 |
| **Legacy / stub clarification** | policies/ vs plangate role (legacy, alternate, or test-only); plan_gate_stub vs plangate one-sentence in runtime or LAYER3 spec | 4 |
| **Governance clarification** | Document PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, AI-Session-Progress-Tracker as status/reporting, not doctrine | 2 |
| **Do-not-touch path-contract cluster** | All paths in §7 Path-Contract Consolidation Register with “do-not-touch” or “High” risk: do not move or rename without a dedicated plan that updates all references (code, docs, tests, scripts, CI) | All |

---

## 12. Immediate conclusions

- **What are the biggest cross-layer structural risks?** (1) **Observation split and dual index** — Layer-4 two-tree structure and two index paths not in spine; link/case inconsistency. (2) **Path-contract density** — Many paths referenced by code or docs; moving/renaming without a consolidated update plan will break contracts. (3) **Duplicate structural truth** — Governance restatements and runtime/observation/ ownership in milestone docs only; drift risk. (4) **Root leakage and artifact-home** — Generated artifacts at root; missing convention for where L2/L3 outputs go.

- **Which issues are truly structural vs merely untidy?** **Truly structural:** Observation split not in spine (affects layer-boundary understanding); path contracts (affect builds and imports); root artifact leakage as symptom of artifact-home (affects repo hygiene and .gitignore). **Merely untidy:** Mixed-case docs dirs; docs/README as broad index; governance status files in governance/; policies/ vs plangate (clarification only). **Borderline:** Report sprawl (convention gap, not wrong placement); dual observation index (structural in that two indices exist, but fix is one sentence + optional link normalization).

- **Which path contracts are most dangerous?** Those **referenced by code** (not only docs): AGENT_EXECUTION_RULES.md (root), governance/CONSTITUTIONAL_MANIFEST_v1.0.md, governance/golden-exemplars/, docs/NON_NEGOTIABLE_INVARIANTS.md (profiles.py); ml/training/generated/, ml/training/_build/exemplars, ml/training/compiler/compile_stage7.py, ml/training/pipeline/stage6/stage6c/, ml/scripts/prepare_exemplars.sh; runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/ (observation/ingest/validate.py); runtime/plangate/, runtime/sandbox/, runtime/ledger/, runtime/observation/. Moving or renaming any of these without updating **all** code and doc references is **high risk**.

- **Which themes are ready for future remediation batching?** **Ready:** canonical docs spine clarifications (add sentences, no file moves); observation split clarification (add one sentence); naming consistency (document, optionally fix links); root hygiene (gitignore, relocate artifacts, move prompt files); report convention (document); legacy/stub clarification (document). **Do-not-touch:** Path-contract cluster — any move/rename only with dedicated plan.

- **What should the next audit phase be?** Phase 6 completes the **cross-layer consolidation** of Phases 0–5. The next phase should be **remediation planning**: prioritized actions derived from this consolidation, with explicit batches (e.g. “Batch A: spine clarifications only”; “Batch B: root hygiene and .gitignore”; “Batch C: report convention doc”), dependency order, and a **path-contract checklist** before any move/rename. No further structural audit phase is required unless the user defines Phase 7.

---

## 13. Non-goals

This phase did **not**:

- Move, rename, or edit any file.
- Fix naming, links, or conventions.
- Consolidate or relocate reports.
- Merge observation trees or change package structure.
- Produce the final remediation plan (only remediation affinity map).
- Execute any remediation batch.

---

## Phase 6 result summary

### 1. Artifact created
- **path:** `docs/audit/CROSS_LAYER_INCONSISTENCY_AND_PATH_CONTRACT_AUDIT.md`

### 2. Biggest cross-layer risks
- **risk 1:** Observation split and dual index — Layer-4 two-tree structure and two index paths (docs/OBSERVATION/README vs observation/README) not stated in canonical spine; case mismatch; structural truth for runtime/observation/ only in M4.x milestones.
- **risk 2:** Path-contract density — Many paths referenced by code (profiles.py, observation/ingest/validate.py, prepare_exemplars.sh, compile_stage7.py, conf_drift_pipeline, plan_gate_service/tests, etc.) and docs; moving or renaming without a consolidated update plan will break contracts or builds.
- **risk 3:** Root leakage and duplicate structural truth — Generated artifacts at root (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_*); governance phase semantics restated in LAYER1_SPEC and NON_NEGOTIABLE without “source of truth” label; observation split only in milestone docs.

### 3. Naming inconsistency result
- **status:** Present but not critical; confusing or convention-weak.
- **key examples:** OBSERVATION vs observation (docs vs root); plangate vs plan_gate_stub vs plan_gate_service; status vs status_reports vs reports vs runtime/verification; Stage-7 vs sft/stage7; COMPILATION, CONTRACTS, OBSERVATION (uppercase) vs governance, runtime (lowercase).
- **conclusion:** Add one-sentence clarifications and optionally normalize link case; no mandatory renames for this phase.

### 4. Duplicate-truth / report-sprawl result
- **duplicate-truth:** Governance phase semantics in manifest + LAYER1_GOVERNANCE_SPEC + NON_NEGOTIABLE_INVARIANTS (acceptable restatement; add “source of truth” to avoid drift). Observation split and runtime/observation/ ownership only in M4.x (drift-prone; add to spine).
- **report-sprawl:** docs/reports, docs/status, docs/status_reports, docs/runtime/verification with no single stated convention; placement observable but convention implicit.
- **conclusion:** Add canonical sentence for observation split; add “source of truth” to governance restating docs; document report convention (or classify only).

### 5. Path-contract consolidation result
- **number of path-sensitive clusters:** 45+ (consolidated from Phases 0–5; deduplicated).
- **most dangerous examples:** AGENT_EXECUTION_RULES.md (root), governance/, governance/CONSTITUTIONAL_MANIFEST_v1.0.md, governance/golden-exemplars/, docs/NON_NEGOTIABLE_INVARIANTS.md (code ref in profiles.py); runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/ (observation/ingest); ml/training/generated/, ml/training/_build/exemplars, ml/training/compiler/compile_stage7.py; runtime/plangate/, runtime/sandbox/, runtime/ledger/, runtime/observation/; docs/MASTER_SYSTEM_SPEC.md, docs/ARCHITECTURE_4_LAYER.md, docs/LIVE_ROADMAP_TRACKER.md.
- **conclusion:** Do not move or rename path-contract items without a dedicated plan that updates all code and doc references; use §7 register as checklist.

### 6. Layer-boundary shadowing result
- **notable examples:** runtime/observation/ (acceptable but under-documented); governance mirror in ml (_build/exemplars) (acceptable and well-signaled); runtime schemas consumed by observation/ingest (acceptable and well-signaled); governance manifest + invariants read by ml profiles.py (acceptable and well-signaled).
- **conclusion:** No structurally ambiguous or structural-concern shadowing; only runtime/observation/ needs one sentence in spine.

### 7. Remediation affinity result
- **strongest future batch themes:** canonical docs spine clarifications; observation split clarification; root hygiene / artifact-home cleanup; naming consistency clarification; report convention consolidation; legacy/stub clarification; do-not-touch path-contract cluster (checklist for any move/rename).
- **conclusion:** Issues group cleanly into spine, root, report, naming, observation, legacy, and path-contract batches; next phase should be remediation planning with prioritized batches and path-contract checklist.

### 8. Final status
**PHASE 6 CROSS-LAYER AUDIT READY**
