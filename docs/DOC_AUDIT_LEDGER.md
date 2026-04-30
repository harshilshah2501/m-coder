# Documentation Audit Ledger

**Status:** active (append-only decisions log)  
**Audit mode:** controlled demolition + reconstruction  
**Started:** 2026-04-17

---

## 1) Authority order (frozen for this audit)

Non-negotiable precedence for contradiction resolution:

1. `docs/LIVE_ROADMAP_TRACKER.md` (live program truth and closure state)
2. `docs/SYSTEM_TRUTH.md` (navigation anchor and contradiction resolver)
3. `docs/PROGRAM_STATE_SNAPSHOT.md` (portable continuity summary, not full truth source)
4. `docs/PRODUCT_SLICE.md` (in/out scope for this validation pass, CLI/HTTP-first stance)

If a document conflicts with this order, it is **suspect by default** until explicitly reconciled here.

---

## 2) Classification taxonomy

- `Canonical`
- `Active working`
- `Reference`
- `Compatibility`
- `Partially stale`
- `Archive candidate`
- `Delete candidate`
- `Unknown`

Dispositions (decision column):

- `keep`
- `merge_into:<path>`
- `archive`
- `deprecate_with_stub`
- `delete_candidate`
- `pending_batch`

---

## 3) Inventory status

- Total markdown files discovered in workspace: **639**
- Batch A (control plane + known contradiction set) audited in this ledger: **12**
- Batch B (runtime/spec contracts) audited in this ledger: **18**
- Batch C (product/validation) audited in this ledger: **25**
- Batch D tranche 1 (guides/reference/mvp_declaration) audited in this ledger: **34**
- Batch D tranche 2A (runtime verification/reports/status) audited in this ledger: **26**
- Batch D tranche 2B (audit set — high-signal subset) audited in this ledger: **8**
- Batch D tranche 2C (audit set — remaining files) audited in this ledger: **33**
- Batch D tranche 3A (archive directory inventory) audited in this ledger: **11**
- Batch D tranche 3B (milestones/iterations/training/layer5) audited in this ledger: **33**
- Batch D tranche 3C (demo/design/datasets/benchmark + residual top-level) audited in this ledger: **29**
- Batch D tranche 3D (architecture/contracts/observation/governance + runtime long-tail) audited in this ledger: **37**
- Batch D tranche 3E (uncategorized long-tail residual set) audited in this ledger: **53**
- Batch D tranche 3F (runtime/observation/governance-root + external residuals) audited in this ledger: **44**
- Batch D tranche 3G (governance phase corpus + review packages) audited in this ledger: **76**
- Batch D tranche 3H (ml + archive corpus sweep) audited in this ledger: **208**
- Batch D tranche 3I (recount + duplicate normalization + residual closure) audited in this ledger: **68**
- Remaining for full classification: **0 (in normalized audit scope)**

Normalized scope recount (3I):
- Scope roots: `docs/`, `governance/`, `runtime/`, `observation/`, `packaging/`, `ml/`, `archive/`, `validation/` + root `README.md`, `MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md`, `plan-stage25AssistLayerV1.prompt.md`
- Unique markdown files in normalized scope: **710**
- Unique markdown files classified in ledger after 3I: **710**
- Residual unclassified in normalized scope: **0**

---

## 4) Batch A — control plane + first contradiction set

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/LIVE_ROADMAP_TRACKER.md` | Live program state, closure, follow-on tracks | Critical | Canonical | `PROGRAM_STATE_SNAPSHOT.md`, closure handbooks, validation docs | keep | Canonical winner for gate/closure posture. |
| `docs/SYSTEM_TRUTH.md` | Contradiction resolver and navigation index | Critical | Canonical | Tracker, snapshot, README, closure handbook | keep | Already tags known stale narratives; should remain contradiction index. |
| `docs/PROGRAM_STATE_SNAPSHOT.md` | Portable continuity summary | Critical | Canonical (secondary to tracker) | Tracker, post-closure maintenance | keep | Must stay concise and subordinate to tracker for full status. |
| `docs/PRODUCT_SLICE.md` | Validation-slice boundary (CLI/HTTP-first) | Critical | Canonical (scope boundary) | `PRODUCT_SLICE_CHARTER.md`, tracker section 1.x | keep | Defines in/out proof burden for this pass. |
| `docs/MASTER_SYSTEM_SPEC.md` | Architectural canonical entry point | Critical | Canonical | Layer specs, architecture map | keep | Must remain sole architecture entry gate. |
| `docs/ARCHITECTURE_4_LAYER.md` | Layer boundary map | High | Canonical | master spec, layer specs | keep | Canonical boundary reference. |
| `docs/LAYER1_GOVERNANCE_SPEC.md` | Layer 1 doctrine/runtime governance contract | High | Canonical | constitutional manifest | keep | Control-plane spec; no drift allowed. |
| `docs/LAYER2_COMPILATION_SPEC.md` | Layer 2 compilation discipline | High | Canonical | compilation docs | keep | Keep as normative layer spec. |
| `docs/LAYER3_RUNTIME_SPEC.md` | Layer 3 runtime architecture contract | High | Canonical | runtime verification docs | keep | Keep as normative layer spec. |
| `docs/LAYER4_OBSERVATION_SPEC.md` | Layer 4 observability contract | High | Canonical | validation/observability reports | keep | Keep as normative layer spec. |
| `docs/NON_NEGOTIABLE_INVARIANTS.md` | Program invariants contract | High | Canonical | tracker + master spec | keep | Invariants doc; must align with tracker/system truth. |
| `docs/production_closure_handbook_corrected_canonical_version.md` | Historical/supporting closure narrative | Medium | Partially stale | tracker closure tables, system truth tags | deprecate_with_stub | Known contradiction pattern: carries open/blocking closure language while tracker states closed post-closure mode. Canonical winner = tracker/system truth. |

---

## 5) Contradictions logged (explicit)

### C-001
- **Topic:** Production closure posture
- **Conflicting docs:** `docs/production_closure_handbook_corrected_canonical_version.md` vs `docs/LIVE_ROADMAP_TRACKER.md`
- **Canonical winner:** `docs/LIVE_ROADMAP_TRACKER.md` (reinforced by `docs/SYSTEM_TRUTH.md`)
- **Action:** mark handbook as `Partially stale`; keep as narrative/supporting only; plan `deprecate_with_stub` in later batch.

---

## 6) Next queued batches

- **Batch D tranche 3J (optional outer-scope sweep):** classify markdown outside normalized audit scope (e.g. `OKR/**`, `notebooklm_engineer_bundle/**`, root singleton docs) only if we decide to expand scope beyond current charter.

---

## 7) Batch B — runtime/spec contracts

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md` | Plan/ledger contract rules | High | Canonical | runtime schemas, layer-3 docs | keep | Contract-level rules; preserve as primary spec. |
| `docs/SHADOW_MODE_PROTOCOL_V0_1.md` | Shadow enforcement protocol | High | Canonical | shadow schemas, runtime verification | keep | Canonical for shadow contract behavior. |
| `docs/COMPILATION_DAG_AND_LINEAGE_V0_1.md` | Lineage/DAG contract | High | Canonical | layer-2 specs, compilation docs | keep | Contract spec; do not duplicate in narrative docs. |
| `docs/PHASE_ALIGNMENT_TABLE_V0_1.md` | Crosswalk table across layers | Medium | Reference | governance + runtime + compilation specs | keep | Useful mapping table; not primary truth source. |
| `docs/JETBRAINS_PLUGIN_FLOW_V0_1.md` | Plugin request/response flow contract | High | Compatibility | plugin bridge docs, runtime ask/plan APIs | keep | Compatibility contract; must defer to tracker for program state. |
| `docs/CONTRACTS/README.md` | Contract/schema index | High | Reference | runtime schemas + v0.1 contract docs | keep | Keep as index; avoid embedding independent truth. |
| `docs/api/README.md` | API surface index / splits | Medium | Compatibility | plan-gate readmes, schema dirs | keep | Compatibility navigator; explicitly non-single-openapi. |
| `docs/runtime/README.md` | Layer-3 runtime index | High | Reference | runtime specs + v0.1 contracts | keep | Good entrypoint; maintain links only, minimal narrative. |
| `docs/runtime/RUNTIME_STATE_TRANSITIONS.md` | Deterministic state machine contract | High | Canonical | layer-3 spec + runtime schemas | keep | Runtime control-plane contract. |
| `docs/runtime/RUNTIME_AGENT_ARCHITECTURE.md` | Runtime-governed agent architecture | High | Canonical | state transitions, layer-3 spec | keep | Architectural runtime contract (model proposes/runtime decides). |
| `docs/runtime/REPOSITORY_CONTEXT_ENGINE.md` | M3.0 context engine contract | Medium | Reference | M3.12 narrow spec, context code | keep | Historical but still contract-relevant for engine semantics. |
| `docs/runtime/M3_12_NARROW_CONTEXT_ENGINE_SPEC.md` | Narrow manifest/selector spec | Medium | Reference | tracker M3.12 status, context engine docs | keep | Keep as milestone-scoped implementation spec. |
| `docs/runtime/WORKSPACE_INTELLIGENCE_LAYER_SPEC.md` | Layer-5 anchor pointer | High | Canonical | architecture workspace intelligence final spec | keep | Anchor/pointer by design; keep concise. |
| `docs/runtime/JETBRAINS_PLUGIN_RUNTIME_BRIDGE.md` | Plugin bridge behavior and outcomes | Medium | Compatibility | plugin flow v0.1, demo guides | keep | Compatibility and implementation guidance; avoid status authority drift. |
| `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md` | Operator demo runbook | Medium | Active working | production verification guide, plugin flow | keep | Active operational guide, not truth source. |
| `docs/runtime/CANONICAL_EXECUTION_INTENT_v1.md` | Design freeze for execution intent | Medium | Active working | architecture freeze, pre-gate design | keep | Design-only; track as pending implementation alignment. |
| `docs/runtime/PRE_GATE_DESIGN_v1.md` | Deterministic pre-gate design proposal | Low | Partially stale | architecture freeze, plan-gate behavior | deprecate_with_stub | Design-only proposal; likely superseded by current runtime chain docs. |
| `docs/runtime/ARCHITECTURE_FREEZE_v1.md` | Post-M3.11 architecture freeze snapshot | Medium | Reference | runtime architecture + tracker evolution | keep | Frozen snapshot; retain as historical architectural baseline. |

---

## 8) Batch C — product/validation docs

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/validation/POST_CLOSURE_MAINTENANCE.md` | Operational lock + post-closure process | Critical | Canonical | tracker §0/§1.4, baseline policy | keep | Canonical operational process for post-closure mode. |
| `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` | Baseline artifact policy (§5) | Critical | Canonical | behavior verification closure, maintenance | keep | Canonical regression guardrail policy. |
| `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md` | Core closure evidence narrative | High | Reference | Action 14 report, tracker closure rows | keep | Proof record; tracker remains live state authority. |
| `docs/validation/artifacts/action14_final_acceptance/ACTION14_FINAL_ACCEPTANCE_REPORT.md` | Action 14 acceptance authority | Critical | Canonical | tracker closure status, system truth | keep | Formal acceptance artifact; retain prominently. |
| `docs/validation/B5_HOST_READINESS.md` | Host readiness closure report | High | Reference | tracker B5 closure references | keep | Closure evidence doc, non-live status source. |
| `docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md` | Plugin truth-proof closure | High | Reference | plugin artifacts + tracker §6.22 references | keep | Closure artifact, not operational source of truth. |
| `docs/validation/PLUGIN_UI_TRUTH_CERTIFICATION.md` | Plugin UI truthfulness certification | Medium | Reference | phase1 truth proof closure | keep | Keep as supporting certification evidence. |
| `docs/validation/STAGE3_BURN_IN_REPORT.md` | Stage3 burn-in evidence | Medium | Reference | tracker §6.20 evidence | keep | Historical validation evidence. |
| `docs/validation/RETRIEVAL_REDESIGN_V1_EVAL.md` | Retrieval redesign evaluation snapshot | Medium | Partially stale | retrieval baseline policy + B1 follow-through | keep | Useful context but not current control source. |
| `docs/validation/RETRIEVAL_USEFULNESS_HARDENING_PASS.md` | Retrieval hardening pass report | Medium | Reference | retrieval redesign + B1 reports | keep | Keep as evidence history. |
| `docs/validation/SNAPSHOT_IDENTITY_CORRECTNESS_NOTE_2026-04-06.md` | Snapshot identity note | Medium | Reference | baseline policy + maintenance process | keep | Narrow proof note; retained for traceability. |
| `docs/validation/LOW_CORE_RATIO_DECISION.md` | Retrieval quality decision note | Medium | Reference | retrieval policy + B1 docs | keep | Decision log; non-canonical for live state. |
| `docs/validation/MVP_PRODUCTION_CLOSURE_NOTE.md` | MVP closure summary note | Medium | Partially stale | tracker closed-gate posture | keep | Historical note; ensure no conflict with tracker wording. |
| `docs/validation/AIOPS_MVP_USEFULNESS_GROUND_TRUTH_CAPTURE.md` | Ground-truth capture method | Low | Reference | scenario pack + eval docs | keep | Methodology reference. |
| `docs/validation/AIOPS_MVP_SCENARIO_PACK.md` | MVP scenario definitions | Medium | Reference | behavior verify scenarios + policy | keep | Still useful as scenario narrative. |
| `docs/validation/AIOPS_MVP_FINAL_REPORT_TEMPLATE.md` | Report template | Low | Archive candidate | active closure reports | archive | Template value is low now; archive unless reused. |
| `docs/validation/DEBUG_DEPTH_CHARTER_CLOSURE_REPORT.md` | Debug-depth charter closure | High | Active working | debug charter + tracker §1.4 | keep | Recently active closure artifact. |
| `docs/validation/L57_DIRTY_BUFFER_CHARTER_CLOSURE_REPORT.md` | L5.7 charter closure | High | Active working | L5.7 charter + tracker §1.4 | keep | Recently active closure artifact. |
| `docs/validation/artifacts/b5_wsl_backend_gpu/README.md` | B5 artifact package index (WSL backend) | Medium | Reference | B5 host readiness report | keep | Artifact navigation only. |
| `docs/validation/artifacts/b5_linux_backend_gpu/SUMMARY.md` | B5 Linux artifact summary | Medium | Reference | B5 readiness + closure docs | keep | Evidence summary doc. |
| `docs/validation/artifacts/b1_retrieval_validation/B1_GENERALIZATION_SUMMARY.md` | B1 retrieval generalization summary | Medium | Reference | B1/l58 reports + tracker follow-through | keep | Follow-through evidence, not gate authority. |
| `docs/validation/artifacts/b1_retrieval_validation/l58_grounded_report.md` | L5.8 grounded report | Medium | Reference | L5.8 closure statements | keep | Historical proof for closed harness scope. |
| `docs/validation/artifacts/plugin_phase1_truth_proof/proof_matrix.md` | Plugin proof matrix | Medium | Reference | phase1 truth proof closure | keep | Supporting matrix artifact. |
| `docs/validation/artifacts/assist_layer_v1_integration_proof/summary.md` | Assist v1 integration proof summary | Medium | Reference | assist evaluation docs | keep | Evidence artifact for assist slice. |
| `docs/validation/artifacts/assist_layer_v2_eval/README.md` | Assist v2 eval artifact index | Medium | Reference | assist evaluation artifacts | keep | Index for evaluation evidence set. |

---

## 9) Batch D tranche 1 — guides/reference/mvp declaration

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/guides/MOTADATA_VERIFICATION_GUIDE.md` | Single Motadata runbook: WSL+GPU setup (Pass A/B/C), production contract verify, **§5.2** `run_v1_ask`, developer utility + batch reports, troubleshooting | Critical | Canonical | post-closure maintenance, baseline policy, `PASS_*` / `MOTADATA_*` redirect stubs in same folder | keep | Merges former AIOPS + Pass A/B/C + developer-utility guides; redirects preserve old paths. |
| `docs/guides/mapping_request_ids.md` | Trace mapping runbook | High | Active working | Host-A mapping docs | keep | Operationally useful and current. |
| `docs/guides/STAGE2_REAL_AIOPS_TESTING_GUIDE.md` | Stage2 test procedure | Medium | Reference | production verification guide | keep | Historical but still useful context. |
| `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md` | Stage3 burn-in/e2e demo runbook | Medium | Active working | stage3 burn-in report | keep | Active demo/verification aid. |
| `docs/guides/HOST_A_PROOF_PACK_CLOSURE.md` | Host-A proof pack closure instructions | Medium | Reference | post-closure maintenance | keep | Supporting ops guide. |
| `docs/guides/HOST_A_PLAN_GATE_LOG_MAPPING.md` | Host-A request-id mapping example | Medium | Reference | mapping_request_ids.md | keep | Example-focused guide. |
| `docs/guides/JETBRAINS_PLUGIN_UI_FINAL_DEMO_RUNBOOK.md` | Plugin UI demo guide | Medium | Compatibility | plugin demo guide, tracker plugin closure | keep | Compatibility/demo support. |
| `docs/guides/ORCHESTRATOR_SERVICE_GUIDE.md` | Governed services startup guide | Medium | Active working | orchestrator guide, demo setup | keep | Current service operation doc. |
| `docs/guides/ORCHESTRATOR_GUIDE.md` | Systemd/ops wrapper guidance | Medium | Compatibility | orchestrator service guide | keep | Complementary ops guidance. |
| `docs/guides/ACTION_7_TRUST_AUDIT.md` | Action 7 trust audit runbook | Medium | Reference | execute trust closure evidence | keep | Historical action-focused reference. |
| `docs/guides/ACTION_11_LINUX_TEST_RUNBOOK.md` | Action 11 validation runbook | Medium | Reference | compatibility hardening closure | keep | Action-specific historical runbook. |
| `docs/guides/ACTION_5_OBSERVABILITY_CORRELATION.md` | Observability correlation runbook | Medium | Reference | action 5 closure docs | keep | Historical runbook reference. |
| `docs/guides/RETRIEVAL_PHILOSOPHY_AND_CONTRACT.md` | Retrieval philosophy and contract notes | Medium | Reference | baseline policy + retrieval validation docs | keep | Conceptual companion; non-authoritative. |
| `docs/guides/SANDBOX_SETUP.md` | Sandbox setup instructions | Medium | Compatibility | runtime sandbox docs | keep | Compatibility setup guide. |
| `docs/guides/Dominance_Grammar.md` | Non-canonical dominance explanation | Low | Reference | constitutional manifest, master spec | keep | Explicitly non-canonical explanatory doc. |
| `docs/guides/QnA.md` | Narrative Q&A companion for dominance grammar | Low | Archive candidate | Dominance_Grammar.md | archive | Large conversational companion; secondary. |
| `docs/guides/Pre-GREG.md` | Narrative pre-GREG discussion | Low | Archive candidate | invariants + governance specs | archive | Non-canonical long-form narrative. |
| `docs/guides/E2E-flow.md` | Legacy narrative walkthrough | Low | Archive candidate | master spec + layer specs | archive | Very long non-canonical walkthrough. |
| `docs/guides/INTEGRATION_GUIDE.md` | Legacy enhanced-RAG integration plan | Low | Partially stale | current Plan-Gate slice docs | deprecate_with_stub | References old Continue.dev/Qdrant-era architecture. |
| `docs/guides/Agents.md` | Legacy multi-agent integration analysis | Low | Partially stale | current runtime-governed architecture | deprecate_with_stub | Legacy orchestration analysis not aligned with current runtime control model. |
| `docs/guides/KPI-Implementation-Quick-Start.md` | KPI quick-start narrative | Low | Archive candidate | robust evaluation framework docs | archive | Secondary methodology note. |
| `docs/guides/HowTo_Robust_Evaluation_Finetuned_Coding_Assistant.md` | Evaluation how-to | Low | Archive candidate | robust evaluation comprehensive doc | merge_into:`docs/guides/Robust_Evaluation_Framework_LLM_Coding_Assistants_Comprehensive.md` | Consolidate with the comprehensive framework document. |
| `docs/guides/Robust_Evaluation_Framework_LLM_Coding_Assistants_Comprehensive.md` | Comprehensive evaluation methodology | Medium | Reference | developer utility validation guide | keep | Keep as methodology reference. |
| `docs/archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md` | Temporary archived integration guide | Low | Archive candidate | production verification guide | archive | Already under archive; retain as archived only. |
| `docs/reference/DIRECTORY_STRUCTURE_ANALYSIS.md` | Structure analysis reference | Low | Reference | repo reality map | keep | Reference-only, not control-plane. |
| `docs/reference/DEPENDENCY_REPRODUCIBILITY.md` | Dependency reproducibility note | Medium | Reference | verification guides | keep | Useful supporting reference. |
| `docs/reference/MODEL_VERIFICATION_REPORT.md` | Model verification report | Medium | Reference | evaluation framework docs | keep | Historical verification evidence. |
| `docs/reference/NAMING_CONVENTIONS.md` | Naming convention reference | Medium | Reference | tracker nomenclature notes | keep | Useful style/reference doc. |
| `docs/reference/CI_EXECUTION_MODEL.md` | CI execution model reference | Medium | Reference | system CI audit docs | keep | Supporting CI behavior reference. |
| `docs/mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md` | Formal production closure declaration | Critical | Canonical | tracker closure state, action14 report | keep | Formal declaration artifact. |
| `docs/mvp_declaration/MVP_DECLARATION.md` | MVP declaration narrative | Medium | Reference | closure declaration + tracker | keep | Secondary declaration text. |
| `docs/mvp_declaration/MVP_EVIDENCE_INDEX.md` | Evidence index for declaration | High | Reference | validation artifacts | keep | Helpful evidence navigator. |
| `docs/mvp_declaration/MVP_SUMMARY_1_PAGE.md` | One-page MVP summary | Medium | Reference | declarations + tracker | keep | Executive summary artifact. |

---

## 10) Batch D tranche 2A — runtime verification/reports/status

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/runtime/verification/RUNTIME_CONSTITUTIONAL_REFERENCE.md` | Full-system audit planning reference | Low | Archive candidate | system/master audits, tracker, system truth | archive | Planning artifact; not live truth source. |
| `docs/runtime/verification/SYSTEM_CANONICAL_STATE_AUDIT.md` | Canonical-state audit report | Medium | Reference | system master audit + tracker | keep | Useful historical evidence. |
| `docs/runtime/verification/SYSTEM_DEPENDENCY_SUPPLY_CHAIN_AUDIT.md` | Dependency/supply-chain audit | Medium | Reference | governance + CI audits | keep | Reference audit, non-control-plane. |
| `docs/runtime/verification/LAYER3_RUNTIME_AUDIT.md` | Layer-3 runtime audit | Medium | Reference | layer3 completion/merge reports | keep | Historical integrity evidence. |
| `docs/runtime/verification/SYSTEM_CONFIGURATION_ENVIRONMENT_AUDIT.md` | Runtime env/config audit | Medium | Reference | production verification runbooks | keep | Supporting environment evidence. |
| `docs/runtime/verification/SYSTEM_GOVERNANCE_AUDIT.md` | Governance consistency audit | Medium | Reference | layer1 governance spec + system truth | keep | Supporting governance evidence. |
| `docs/runtime/verification/SYSTEM_CI_AUTOMATION_AUDIT.md` | CI automation audit | Medium | Reference | CI execution model ref | keep | Supporting CI evidence. |
| `docs/runtime/verification/NOMENCLATURE_AUDIT.md` | Naming/nomenclature audit | Low | Reference | naming conventions docs | keep | Supporting consistency artifact. |
| `docs/runtime/verification/SYSTEM_E2E_VALIDATION.md` | E2E validation record | Medium | Reference | production verification guide + closure docs | keep | Historical validation evidence. |
| `docs/runtime/verification/SYSTEM_NAMING_CONVENTION_AUDIT.md` | Naming convention audit | Low | Reference | nomenclature audit + naming ref | keep | Potential merge target later if duplicated. |
| `docs/runtime/verification/SYSTEM_MASTER_AUDIT_REPORT.md` | Master audit summary | Medium | Reference | subordinate verification audit docs | keep | High-level historical aggregation. |
| `docs/runtime/verification/REPOSITORY_STRUCTURE_AUDIT.md` | Repository structure audit | Medium | Reference | repo reality map + architecture map | keep | Historical structure evidence. |
| `docs/runtime/verification/GIT_PROVENANCE_AUDIT.md` | Git provenance audit | Medium | Reference | tracker history and release tags | keep | Provenance support artifact. |
| `docs/runtime/verification/LAYER3_PARALLEL_BRANCH_AUDIT_REPORT.md` | Parallel branch audit | Low | Archive candidate | layer3 merge/completion reports | archive | Branch-era snapshot; likely archival-only value now. |
| `docs/runtime/verification/ML_PIPELINE_AUDIT.md` | ML pipeline audit | Medium | Reference | layer2 compilation docs | keep | Supporting Layer-2 evidence. |
| `docs/runtime/verification/DOCS_ALIGNMENT_AUDIT.md` | Docs alignment audit snapshot | Medium | Reference | doc audit ledger | keep | Historical baseline for current doc audit. |
| `docs/runtime/verification/LAYER3_INTEGRATION_MERGE_READINESS_REPORT.md` | Layer3 merge-readiness report | Low | Archive candidate | completion reports + tracker history | archive | Milestone-era report; archival value mostly. |
| `docs/runtime/verification/LAYER3_RUNTIME_COMPLETION_REPORT.md` | Layer3 completion report | Medium | Reference | tracker §6 + milestone docs | keep | Historical completion evidence. |
| `docs/runtime/verification/LAYER3_MILESTONE_NORMALIZATION_REPORT.md` | Milestone normalization report | Medium | Reference | tracker canonical table | keep | Historical normalization evidence. |
| `docs/reports/M3_12_COMPLETION_REPORT.md` | M3.12 completion report | Medium | Reference | tracker M3.12 closure entries | keep | Historical completion artifact. |
| `docs/reports/M3_12_INTEGRATION_VERIFICATION_REPORT.md` | M3.12 integration verification | Medium | Reference | M3.12 completion report | keep | Supporting integration evidence. |
| `docs/reports/M4X_MAIN_MERGE_COMPLETION.md` | M4.x merge completion | Medium | Reference | m4x verification/readiness reports | keep | Historical merge evidence. |
| `docs/reports/M4X_INTEGRATION_FREEZE_REPORT.md` | M4.x integration freeze report | Medium | Reference | M4X readiness/verification | keep | Historical stabilization record. |
| `docs/reports/M4X_INTEGRATION_VERIFICATION_REPORT.md` | M4.x integration verification | Medium | Reference | M4X completion/freeze reports | keep | Historical verification evidence. |
| `docs/reports/M4X_MAIN_MERGE_READINESS.md` | M4.x readiness report | Low | Archive candidate | merge completion report | archive | Pre-merge planning artifact; archival value now. |
| `docs/status/README.md` | Status folder policy/index | Medium | Active working | archive policy docs | keep | Living ops journal policy doc. |

---

## 11) Batch D tranche 2B — audit set (high-signal subset)

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md` | Broad repo/system mapping audit | Medium | Reference | repo reality map, tracker, verification reports | keep | Useful snapshot evidence; branch-specific context limits authority. |
| `docs/audit/SURGICAL_NEXT_STEPS_PLAN.md` | Follow-on planning from prior audit | Medium | Partially stale | current tracker prioritization + active charters | keep | Planning snapshot; not current canonical roadmap. |
| `docs/audit/DEBUG_PATH_VALIDATION_REPORT.md` | Debug path scenario capture analysis | Medium | Reference | debug charter closure + validation artifacts | keep | Useful evidence set for debug behavior. |
| `docs/audit/CANONICAL_DOCS_PLACEMENT_AUDIT.md` | Documentation placement audit | High | Active working | current doc audit ledger | keep | Relevant predecessor to current cleanup pass. |
| `docs/audit/DOCUMENTATION_FRESHNESS_AND_ARTIFACT_GOVERNANCE_ANCHORING_REPORT.md` | Documentation freshness governance report | High | Active working | system truth + current doc audit | keep | High-signal for ongoing audit/reconstruction. |
| `docs/audit/HUMAN_WHOLE_REPO_REVIEW.md` | Large human review narrative | Low | Archive candidate | multiple audit summaries | archive | Very broad narrative; high duplication risk. |
| `docs/audit/TEST_COVERAGE_MATRIX.md` | Coverage matrix snapshot | Medium | Reference | runtime test reports + validation docs | keep | Useful matrix reference. |
| `docs/audit/REPO_LAYOUT_INVENTORY.md` | Repository layout inventory snapshot | Medium | Reference | repo reality map + structure audits | keep | Structure inventory baseline. |

---

## 12) Batch D tranche 2C — audit set (remaining files)

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/audit/LAYER2_COMPILATION_STRUCTURE_AUDIT.md` | Layer2 structure audit | Medium | Reference | Layer2 spec + verification audits | keep | Historical structural evidence. |
| `docs/audit/V16_PRE_GOVERNANCE_DATA_SCRUB_PLAN.md` | Data scrub planning artifact | Low | Archive candidate | structural remediation plans | archive | Planning-only, likely superseded. |
| `docs/audit/RUNTIME_REORG_CANDIDATES.md` | Runtime reorg candidate plan | Low | Archive candidate | runtime directory audits | archive | Planning snapshot, non-canonical. |
| `docs/audit/ROOT_LAYOUT_AUDIT_REPORT.md` | Root layout audit | Medium | Reference | repo layout inventory + structure audits | keep | Useful structure evidence. |
| `docs/audit/RETRIEVAL_DOMINANCE_POLICY_IMPLEMENTATION_PLAN.md` | Retrieval policy implementation plan | Low | Archive candidate | retrieval remediation docs | archive | Plan-stage narrative; superseded by tracker/charters. |
| `docs/audit/REFERENCE_CLEANUP_AND_PATH_RESOLUTION_PLAN.md` | Path/reference cleanup planning | Medium | Reference | doc audit and structural remediation plans | keep | Useful cleanup planning context. |
| `docs/audit/RETRIEVAL_QUALITY_REMEDIATION.md` | Retrieval quality remediation plan | Medium | Reference | retrieval validation docs | keep | Still useful as remediation history. |
| `docs/audit/STRUCTURAL_REMEDIATION_PLAN.md` | Repository structural remediation plan | Medium | Reference | path-safe relocation plan | keep | High-signal remediation plan. |
| `docs/audit/RUNTIME_DIRECTORY_AUDIT.md` | Runtime directory audit | Medium | Reference | layer3 runtime structure audit | keep | Supporting structural evidence. |
| `docs/audit/PHASE_15B_LEGACY_LINEAGE_CONTAINMENT_BOUNDARY_REPORT.md` | Phase 15B containment report | Low | Archive candidate | phase 15 series reports | archive | Phase-series execution log. |
| `docs/audit/PR4_TARGETED_RETRIEVAL_IMPROVEMENT_NOTE.md` | PR4 retrieval note | Low | Archive candidate | retrieval remediation docs | archive | PR-specific note, archival value. |
| `docs/audit/PR5_NO_MATCH_CALIBRATION_NOTE.md` | PR5 no-match calibration note | Low | Archive candidate | no-match policy docs | archive | PR-specific note, archival value. |
| `docs/audit/PR3_VALIDATION_AND_METRICS_NOTE.md` | PR3 validation note | Low | Archive candidate | validation reports | archive | PR-specific note, archival value. |
| `docs/audit/PHASE_14D_REFERENCE_CLEANUP_BATCH_1_EXECUTION_REPORT.md` | Phase 14D batch execution report | Low | Archive candidate | phase cleanup plans | archive | Batch execution history. |
| `docs/audit/PHASE_15A_LEGACY_LINEAGE_CLASSIFICATION_REPORT.md` | Phase 15A classification report | Low | Archive candidate | phase 15 reports | archive | Execution-history artifact. |
| `docs/audit/PATH_SAFE_STRUCTURAL_RELOCATION_PLAN.md` | Path-safe relocation plan | Medium | Reference | structural remediation docs | keep | Useful for controlled relocation decisions. |
| `docs/audit/CROSS_LAYER_INCONSISTENCY_AND_PATH_CONTRACT_AUDIT.md` | Cross-layer inconsistency audit | Medium | Reference | architecture + spec docs | keep | High-signal inconsistency map. |
| `docs/audit/LAYER3_RUNTIME_STRUCTURE_AUDIT.md` | Layer3 structure audit | Medium | Reference | runtime verification reports | keep | Supporting layer structure evidence. |
| `docs/audit/BATCH_D_EXECUTION_REPORT.md` | Batch D execution report | Low | Archive candidate | batch A/B/C/E execution reports | archive | Batch-operation log, archive-target. |
| `docs/audit/BATCH_A_GOVERNED_RUNTIME_CORE.md` | Batch A runtime core note | Low | Archive candidate | batch execution reports | archive | Batch-operation narrative. |
| `docs/audit/BATCH_A_EXECUTION_REPORT.md` | Batch A execution report | Low | Archive candidate | batch report set | archive | Batch-operation log, archive-target. |
| `docs/audit/ARCHIVE_EXPORT_EXECUTION_PLAN.md` | Archive/export execution planning | Medium | Reference | structural remediation plans | keep | Still useful for archival operations. |
| `docs/audit/PHASE_15C_IMPORT_DECOUPLING_PREP_REPORT.md` | Phase 15C prep report | Low | Archive candidate | phase 15 report series | archive | Phase-series execution history. |
| `docs/audit/PHASE_15E_RETAINED_LINEAGE_CONTAINMENT_EXECUTION_REPORT.md` | Phase 15E execution report | Low | Archive candidate | phase 15 report series | archive | Phase-series execution history. |
| `docs/audit/PHASE_15D_LEGACY_PATH_ASSUMPTION_PREP_REPORT.md` | Phase 15D prep report | Low | Archive candidate | phase 15 report series | archive | Phase-series execution history. |
| `docs/audit/PHASE_15F_RETAINED_LINEAGE_PRUNING_REPORT.md` | Phase 15F pruning report | Low | Archive candidate | phase 15 report series | archive | Phase-series execution history. |
| `docs/audit/PHASE_14E_REFERENCE_CLEANUP_BATCH_2_EXECUTION_REPORT.md` | Phase 14E batch execution report | Low | Archive candidate | phase cleanup report series | archive | Batch execution history. |
| `docs/audit/LAYER4_OBSERVATION_STRUCTURE_AUDIT.md` | Layer4 structure audit | Medium | Reference | Layer4 observation spec | keep | Supporting observation-structure evidence. |
| `docs/audit/BATCH_E_EXECUTION_REPORT.md` | Batch E execution report | Low | Archive candidate | batch report set | archive | Batch-operation log, archive-target. |
| `docs/audit/LAYER1_GOVERNANCE_STRUCTURE_AUDIT.md` | Layer1 governance structure audit | Medium | Reference | layer1 governance spec | keep | Supporting governance-structure evidence. |
| `docs/audit/GIT_BRANCH_GOVERNANCE_AUDIT_AND_PRUNE_REPORT.md` | Branch governance/prune report | Medium | Reference | git provenance docs | keep | Useful governance ops reference. |
| `docs/audit/BATCH_C_EXECUTION_REPORT.md` | Batch C execution report | Low | Archive candidate | batch report set | archive | Batch-operation log, archive-target. |
| `docs/audit/BATCH_B_EXECUTION_REPORT.md` | Batch B execution report | Low | Archive candidate | batch report set | archive | Batch-operation log, archive-target. |

---

## 13) Batch D tranche 3A — archive directory inventory

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/archive/README.md` | Archive policy and index | High | Reference | doc audit policy | keep | Keep as archive governance entrypoint. |
| `docs/archive/ROADMAP_L2_L3_L4.md` | Superseded roadmap snapshot | Low | Archive candidate | live roadmap tracker | keep | Already archived; retain as historical artifact. |
| `docs/archive/Notes.md` | Informal historical notes | Low | Archive candidate | multiple narrative docs | keep | Already archived; no reactivation. |
| `docs/archive/demo/INTEGRANTED_EXECUTION_GUIDE.md` | Historical demo guide | Low | Archive candidate | current demo runbooks | keep | Already archived historical demo. |
| `docs/archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md` | Temporary integration guide | Low | Archive candidate | current verification/integration guides | keep | Already archived temporary guide. |
| `docs/archive/status/STREAMING_FIX_SUMMARY.md` | Historical status summary | Low | Archive candidate | current status logs | keep | Already archived status snapshot. |
| `docs/archive/status/TRAINING_MONITOR.md` | Historical training monitor notes | Low | Archive candidate | training docs | keep | Archived operational note. |
| `docs/archive/status/progress-2026-01-08.md` | Historical progress log | Low | Archive candidate | tracker/snapshot timeline | keep | Archived progress entry. |
| `docs/archive/status/COMPLETE_SESSION_SUMMARY_FEB6.md` | Historical session summary | Low | Archive candidate | status logs | keep | Archived session recap. |
| `docs/archive/tooling/CODERABBIT_AUDIT_COVERAGE_MATRIX.md` | Archived tooling audit matrix | Low | Archive candidate | current coverage docs | keep | Archived tooling artifact. |
| `docs/archive/tooling/CODERABBIT_AUDIT_COVERAGE_MATRIX_TEMPLATE.md` | Archived tooling template | Low | Archive candidate | active templates (if any) | keep | Archived template only. |

---

## 14) Batch D tranche 3B — milestones/iterations/training/layer5

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/runtime/milestones/M3.17_TASK_SCHEMA_PLAN.md` | M3.17 task-schema planning spec | Medium | Active working | tracker M3.17 status | keep | Planning/spec doc for follow-on milestone. |
| `docs/runtime/milestones/M4_1_OBSERVABILITY_CLOSURE.md` | M4.1 closure note | Medium | Reference | M4X reports + tracker | keep | Historical closure evidence. |
| `docs/runtime/milestones/M4_2_DRIFT_BASELINE.md` | M4.2 drift baseline note | Medium | Reference | M4X reports | keep | Milestone evidence artifact. |
| `docs/runtime/milestones/M4_3_COLLAPSE_TRACKING.md` | M4.3 collapse tracking note | Medium | Reference | M4X reports | keep | Milestone evidence artifact. |
| `docs/runtime/milestones/M4_4_LEDGER_RECONCILIATION.md` | M4.4 reconciliation note | Medium | Reference | M4X reports | keep | Milestone evidence artifact. |
| `docs/runtime/milestones/M4_5_GREG_ESCALATION.md` | M4.5 escalation note | Medium | Reference | M4X reports | keep | Milestone evidence artifact. |
| `docs/runtime/milestones/M4_6_RUNTIME_METRICS.md` | M4.6 metrics note | Medium | Reference | M4X reports | keep | Milestone evidence artifact. |
| `docs/runtime/milestones/M4_1_SLICE1_IMPL_NOTE.md` | M4.1 slice impl note | Low | Archive candidate | M4.1 closure + M4X reports | archive | Slice-level implementation note, superseded by closure reports. |
| `docs/runtime/milestones/M4_1_SLICE2_IMPL_NOTE.md` | M4.1 slice impl note | Low | Archive candidate | M4.1 closure + M4X reports | archive | Slice-level implementation note, superseded by closure reports. |
| `docs/runtime/milestones/M4_1_SLICE3_IMPL_NOTE.md` | M4.1 slice impl note | Low | Archive candidate | M4.1 closure + M4X reports | archive | Slice-level implementation note, superseded by closure reports. |
| `docs/runtime/milestones/M3.1_AGENT_LOOP_ORCHESTRATOR.md` | M3.1 milestone note | Medium | Reference | Layer3 completion + tracker | keep | Historical milestone detail. |
| `docs/runtime/milestones/M3.3_PLAN_GATE_INTEGRATION.md` | M3.3 milestone note | Medium | Reference | tracker + runtime completion | keep | Historical milestone detail. |
| `docs/runtime/milestones/M3.4_IDE_PLUGIN_INTEGRATION.md` | M3.4 milestone note | Medium | Reference | plugin closure docs + tracker | keep | Historical milestone detail. |
| `docs/runtime/milestones/M3.10_SANDBOX_DRIVER_ABSTRACTION.md` | M3.10 milestone note | Medium | Reference | architecture freeze + tracker | keep | Historical milestone detail. |
| `docs/runtime/milestones/M3.11_CONTAINER_SANDBOX_RUNTIME.md` | M3.11 milestone note | Medium | Reference | architecture freeze + tracker | keep | Historical milestone detail. |
| `docs/iterations/AGENTIC_FRAMEWORK_MASTER.md` | Iteration-era framework narrative | Low | Archive candidate | runtime-governed architecture docs | archive | Pre-closure large narrative; not control-plane. |
| `docs/iterations/OPTION_A_COMPLETION_SUMMARY.md` | Iteration completion summary | Low | Archive candidate | tracker + closure reports | archive | Iteration summary superseded by canonical tracker state. |
| `docs/iterations/BALANCED_OPTIMIZATION_SUMMARY.md` | Optimization summary | Low | Archive candidate | iteration analysis docs | archive | Iteration narrative; non-canonical. |
| `docs/iterations/COMPARISON_BEFORE_AFTER.md` | Before/after iteration comparison | Low | Archive candidate | iteration summaries | archive | Historical analysis snapshot. |
| `docs/iterations/COMPLETE_ITERATIONS_ANALYSIS.md` | Comprehensive iteration analysis | Low | Partially stale | modern tracker/runtime architecture docs | archive | Contains legacy architecture references (e.g. Continue.dev/Qdrant-era framing). |
| `docs/training/V16_2_TRAINING_PLAN.md` | V16.2 training execution plan | Low | Archive candidate | layer2 closure state + training summaries | archive | Legacy training planning, pre-closure era. |
| `docs/training/V16_TRAINING_SUMMARY.md` | V16 training summary | Low | Archive candidate | layer2 compilation records | archive | Historical training summary. |
| `docs/training/V15_TRAINING_SUMMARY.md` | V15 training summary | Low | Archive candidate | layer2 compilation records | archive | Historical training summary. |
| `docs/training/V15_FINETUNING_PRE_TRAINING_CHECKLIST.md` | V15 checklist | Low | Archive candidate | training task/checklist docs | archive | Legacy execution checklist. |
| `docs/training/V15_FINETUNING_TASK_LIST.md` | V15 task list | Low | Archive candidate | training checklists | archive | Legacy task list. |
| `docs/training/V15_QUICK_REFERENCE.md` | V15 quick reference | Low | Archive candidate | training summary docs | archive | Legacy quick reference. |
| `docs/training/V15_COMPLETE_CHECKLIST.md` | V15 completion checklist | Low | Archive candidate | training checklists | archive | Legacy completion checklist. |
| `docs/training/PHASE_4_CORRECTION_WORKFLOW.md` | Training correction workflow | Low | Archive candidate | DPO/training plans | archive | Historical workflow note. |
| `docs/training/DPO_IMPLEMENTATION_PLAN.md` | DPO implementation plan | Low | Archive candidate | training workflow docs | archive | Planning artifact for legacy training path. |
| `docs/training/DIFF_EXAMPLES.md` | Training diff examples | Low | Reference | training workflow docs | keep | Small supporting examples doc. |
| `docs/layer5/PR6_RETRIEVAL_BASELINE_INVARIANTS.md` | PR6 baseline invariants contract | High | Canonical | baseline policy + tracker L5 closure | keep | High-value invariants guardrail. |
| `docs/layer5/WAVE2_FREEZE_REVIEW.md` | Wave2 freeze review | Medium | Reference | layer5 closure records | keep | Historical freeze evidence. |
| `docs/layer5/WSL_CONTEXT_LAYER_PACKAGING_PLAN.md` | Packaging plan for context layer | Medium | Reference | production verification guide + packaging docs | keep | Useful packaging reference. |

---

## 15) Batch D tranche 3C — demo/design/datasets/benchmark + residual top-level

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/demo/PHASE2_JETBRAINS_GOLDEN_DEMO_PLAN.md` | Golden demo planning runbook | Medium | Active working | plugin demo guides + verification runbooks | keep | Current demo preparation reference. |
| `docs/demo/PHASE2_JETBRAINS_GOLDEN_DEMO_RESULT.md` | Golden demo execution result | Medium | Reference | demo plan + validation artifacts | keep | Useful as execution evidence. |
| `docs/demo/NEAR_PRODUCTION_VERTICAL_SLICE_RUNBOOK.md` | End-to-end operator slice runbook | High | Active working | docs README golden path + runtime demo guide | keep | Core demo runbook in current flow. |
| `docs/demo/JETBRAINS_DEMO_NOTES.md` | Demo notes and observations | Low | Reference | demo runbooks | keep | Supporting narrative notes. |
| `docs/demo/M3_12_CONTEXT_DEMO_RUNBOOK.md` | M3.12 context demo runbook | Low | Archive candidate | M3.12 reports + current slice runbook | archive | Milestone-specific runbook largely superseded. |
| `docs/demo/M3.2_PROOF_PACK.md` | Early milestone proof pack | Low | Archive candidate | tracker closure state + modern validation packs | archive | Historical proof artifact. |
| `docs/design/AUTHORITY_REGISTRY_INDEX_AUGMENTATION_SEPARATION.md` | Design proposal for authority/index separation | Medium | Active working | authority registry + tracker follow-ons | keep | Design-level artifact for future implementation. |
| `docs/design/PRODUCT_AUTHORITY_CODE_UNDERSTANDING_LAYER_v1.md` | Product authority understanding layer design | Medium | Active working | layer5/runtime architecture docs | keep | Active design proposal doc. |
| `docs/datasets/CPT_DATASET.md` | CPT dataset methodology and composition | Medium | Reference | V15/V16 dataset summaries | keep | Useful dataset method reference. |
| `docs/datasets/V16_1_DATA_SOURCES_CLARIFICATION.md` | V16.1 data source clarification | Low | Archive candidate | V16 dataset summary docs | archive | Point-in-time clarification note. |
| `docs/datasets/V16_2_DATASET_SUMMARY.md` | V16.2 dataset summary | Low | Archive candidate | V16 dataset summary variants | archive | Historical dataset snapshot. |
| `docs/datasets/V16_DATASET_SUMMARY.md` | V16 dataset summary | Low | Archive candidate | V16.x summaries | archive | Legacy summary superseded by newer records. |
| `docs/datasets/V16_1_DATASET_QUALITY_VERIFICATION.md` | V16.1 quality verification report | Low | Reference | V16.1 analysis docs | keep | Useful quality evidence artifact. |
| `docs/datasets/V15_DATASET_ANALYSIS_AND_RECOMMENDATIONS.md` | V15 dataset analysis | Low | Archive candidate | V15 verification + training docs | archive | Legacy analysis narrative. |
| `docs/datasets/V15_DATASET_QUALITY_VERIFICATION.md` | V15 quality verification | Low | Archive candidate | V15 dataset/training docs | archive | Historical quality report. |
| `docs/datasets/V16_1_DATASET_ANALYSIS_AND_RECOMMENDATIONS.md` | V16.1 analysis and recommendations | Low | Reference | V16.1 verification docs | keep | Retain as analysis baseline for lineage. |
| `docs/datasets/dataset_audit_report.md` | Dataset audit report | Medium | Reference | dataset summaries + quality reports | keep | Useful consolidated audit artifact. |
| `docs/datasets/V16_1_DATASET_EXTRACTION_SUMMARY.md` | V16.1 extraction summary | Low | Archive candidate | V16.1 dataset docs | archive | Point-in-time extraction log. |
| `docs/datasets/Finetuning Paradigms and Coding Assistant.md` | Finetuning paradigms concept note | Low | Reference | training methodology docs | keep | General conceptual reference. |
| `docs/datasets/CPT_Auditing_Steps.md` | CPT audit procedure steps | Medium | Reference | CPT_DATASET + dataset audit report | keep | Procedure-level reference for audits. |
| `docs/benchmark/QUICK_REFERENCE.md` | Benchmark quick reference | Medium | Active working | benchmark plan + validation guides | keep | Handy operational reference. |
| `docs/benchmark/MOTADATA_BENCH_PLAN.md` | Benchmark planning document | Medium | Reference | benchmark quick reference | keep | Core benchmark planning artifact. |
| `docs/README.md` | Docs index and navigation guide | High | Reference | root README + master spec + tracker | keep | Important navigation index, non-canonical truth source. |
| `docs/SYSTEM_EXECUTION_ROADMAP.md` | Legacy execution roadmap flow | Low | Partially stale | live roadmap tracker + layer specs | deprecate_with_stub | Useful architecture flowchart, but live status must defer to tracker. |
| `docs/REPO_REALITY_MAP.md` | Repo path/layer orientation map | High | Active working | structure audits + docs README | keep | High-value navigation reference; keep updated with tracker truth. |
| `docs/MIGRATION_NOTE.md` | 2026 docs refactor migration note | Low | Archive candidate | docs README + master spec | archive | Historical migration record; no active authority role. |
| `docs/DEBUG_DEPTH_CHARTER.md` | Debug-depth post-closure charter | High | Active working | tracker §1.4 + closure report | keep | Current follow-on charter with closure evidence links. |
| `docs/L5_7_DIRTY_BUFFER_CHARTER.md` | L5.7 dirty-buffer post-closure charter | High | Active working | tracker §1.4 + closure report | keep | Current follow-on charter with closure evidence links. |
| `docs/DOC_AUDIT_LEDGER.md` | Central audit decision ledger | Critical | Active working | all batch classification outputs | keep | This ledger is the canonical audit log for this cleanup pass. |

---

## 16) Batch D tranche 3D — architecture/contracts/observation/governance + runtime long-tail

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/architecture/workspace_intelligence_layer_final_architecture_spec.md` | Final architecture spec for WSL context layer split | High | Reference | layer5 specs + runtime architecture | keep | High-signal architecture reference for evidence-first flow. |
| `docs/architecture/workplace_intelligence_layer_spec_critique.md` | Critique/analysis of workspace intelligence spec | Medium | Active working | workspace intelligence final spec | keep | Companion analysis; useful while architecture is evolving. |
| `docs/architecture/Motadata-Coder.md` | Legacy "master blueprint" architecture narrative | Low | Partially stale | runtime-governed architecture docs | archive | Continue.dev/legacy RAG-era framing; archive as historical. |
| `docs/architecture/MOTADATA_CODER_SUMMARY.md` | Legacy deployment/performance summary | Low | Archive candidate | legacy RAG architecture docs | archive | Historical status snapshot, no longer control-plane relevant. |
| `docs/architecture/ARCHITECTURE.md` | Legacy RAG datastore architecture | Low | Archive candidate | repo reality map + modern layer specs | archive | Predates current governed stack topology. |
| `docs/architecture/LAYER_ROOT_DIRECTORY_FEASIBILITY.md` | Feasibility note on layer-prefixed root dirs | Medium | Reference | repo layout audit + structure plans | keep | Useful decision log against disruptive tree renames. |
| `docs/architecture/ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md` | Artifact governance policy for adapters/checkpoints/runtime packages | High | Canonical | layer2/training docs + packaging guidance | keep | Canonical governance policy for model artifacts. |
| `docs/architecture/Golden_Exemplars_Architecture_Map.md` | Conceptual map of exemplar system | Medium | Reference | governance manifest + layer docs | keep | Conceptual model only; not a replacement for constitutional sources. |
| `docs/architecture/Motadata-AI-System-Guide-v2.md` | Legacy comprehensive implementation guide | Low | Archive candidate | runtime architecture + historical guides | archive | Large narrative from pre-governed architecture era. |
| `docs/architecture/PROJECT_STRUCTURE.md` | Legacy RAG-datastore structure map | Low | Archive candidate | repo reality map + audits | archive | Describes outdated repo/project structure. |
| `docs/CONTRACTS/README.md` | Schema and contract index | High | Reference | runtime schema directories + v0.1 specs | keep | Important contract navigator; not an independent authority source. |
| `docs/OBSERVATION/README.md` | Layer-4 observation index and boundaries | High | Reference | layer4 spec + observation packages | keep | Useful orientation doc for observation split locations. |
| `docs/governance/README.md` | Governance layer index and authority pointers | High | Reference | governance manifest + root execution rules | keep | Good navigation doc with explicit root-authority pointer. |
| `docs/governance/AGENT_EXECUTION_RULES.md` | Pointer to root execution rules | Medium | Compatibility | root `AGENT_EXECUTION_RULES.md` | keep | Keep as pointer-only shim; root file remains authoritative. |
| `docs/runtime/motadata_ai_coding_assistant_final_closure_plan.md` | Historical closure plan checklist | Low | Partially stale | tracker closure + maintenance docs | deprecate_with_stub | Planning-era closure checklist superseded by tracker closure state. |
| `docs/runtime/motadata_ai_coding_strategy_capability_roadmap.md` | Strategy narrative for bounded coding capability | Low | Archive candidate | tracker follow-on priorities | archive | High-level narrative, limited operational authority. |
| `docs/runtime/m3.12_demo_scenarios.md` | M3.12 demo scenario corpus | Medium | Reference | M3.12 reports + demo runbooks | keep | Useful deterministic scenario set for historical replay. |
| `docs/runtime/C1_EXECUTION_TRACE_BUILDER_RESULT.md` | C1 implementation result evidence | Medium | Reference | M4.1 closure + runtime observation tests | keep | Solid implementation evidence artifact. |
| `docs/runtime/C2_EXECUTION_EXPLANATION_BUILDER_RESULT.md` | C2 implementation result evidence | Medium | Reference | M4.1 closure + explanation tests | keep | Solid implementation evidence artifact. |
| `docs/runtime/C3_RUNTIME_QUERY_SURFACE_RESULT.md` | C3 implementation result evidence | Medium | Reference | M4.1 closure + runtime summary CLI docs | keep | Solid implementation evidence artifact. |
| `docs/runtime/TRACK_C_FINAL_CLOSURE.md` | Track-C final closure record | Medium | Reference | M4.x reports + tracker | keep | Closure record; tracker remains live status authority. |
| `docs/runtime/WSL_CONTEXT_LAYER_CLIENT.md` | WSL context-layer client contract assumptions | High | Compatibility | layer5 packaging + ask v1 flow docs | keep | Active compatibility contract for plugin/runtime wiring. |
| `docs/runtime/DEMO_LEDGER_COMPAT_FIX_RESULT.md` | Ledger compatibility fix result | Medium | Reference | sandbox ledger store + track-C docs | keep | Useful compatibility evidence for dual ledger schema behavior. |
| `docs/runtime/JETBRAINS_PLUGIN_RUNTIME_WIRING_FIX.md` | Plugin-runtime wiring fix report | Medium | Reference | plugin runtime bridge + demo guides | keep | Troubleshooting evidence for runtime classification behavior. |
| `docs/runtime/JETBRAINS_PLUGIN_MVP_SPIKE.md` | JetBrains MVP spike design and flow | Medium | Compatibility | plugin flow contract + runtime README | keep | Historical but still useful for MVP bridge context. |
| `docs/runtime/branch_execution_notes/feature-m4.1-observability-closure.md` | Branch execution log for M4.1 | Low | Archive candidate | M4.1 closure + C1/C2/C3 result docs | archive | Branch-specific execution note; archive after evidence extraction. |
| `docs/runtime/branch_execution_notes/feature-m3.6-shadow.md` | Branch execution log for M3.6 | Low | Archive candidate | M3.6 shadow docs + milestone notes | archive | Branch-specific implementation log. |
| `docs/runtime/branch_execution_notes/feature-m3.1-orchestrator.md` | Branch execution log for M3.1 | Low | Archive candidate | M3.1 milestone + runtime architecture docs | archive | Branch planning/execution detail, non-canonical. |
| `docs/runtime/branch_execution_notes/feature-m3.5-ledger.md` | Branch execution log for M3.5 | Low | Archive candidate | ledger contract docs + milestone notes | archive | Branch-level execution trace, archival value only. |
| `docs/runtime/branch_execution_notes/m3.10-sandbox-driver.md` | Branch execution log for M3.10 | Low | Archive candidate | M3.10 milestone + sandbox tests | archive | Execution note superseded by milestone and tests. |
| `docs/runtime/branch_execution_notes/m3.11-container-runtime.md` | Branch execution log for M3.11 | Low | Archive candidate | M3.11 milestone + container driver tests | archive | Execution note superseded by closure artifacts. |
| `docs/runtime/branch_execution_notes/PR_M3_6_SHADOW.md` | PR description for M3.6 shadow | Low | Archive candidate | shadow validation report + branch notes | archive | PR-form narrative, archival artifact. |
| `docs/runtime/shadow/M3_6_BASELINE_SCENARIOS.md` | M3.6 scenario corpus summary | Medium | Reference | shadow protocol + validation report | keep | Useful compact scenario reference. |
| `docs/runtime/shadow/M3_6_SHADOW_PROTOCOL_IMPLEMENTATION_NOTE.md` | M3.6 implementation note | Medium | Reference | shadow protocol spec + harness tests | keep | Concise implementation evidence doc. |
| `docs/runtime/shadow/M3_6_SHADOW_VALIDATION_REPORT.md` | M3.6 validation report | Medium | Reference | tracker M3.6 state + shadow tests | keep | Key validation evidence artifact. |
| `docs/runtime/ledger/LEDGER_REPLAY_JOIN_CONTRACT.md` | Ledger replay/join contract details | Medium | Reference | plan/ledger v0.1 spec + transition mapping | keep | Supporting contract detail for audit/replay behavior. |
| `docs/runtime/ledger/TRANSITION_TO_LEDGER_MAPPING.md` | Transition-to-ledger mapping | Medium | Reference | runtime state transitions + ledger contract | keep | Useful mapping reference for evidence joins. |

---

## 17) Batch D tranche 3E — uncategorized long-tail residual set

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/evaluation/V16_POST_TRAINING_EVALUATION.md` | Post-training evaluation report | Low | Reference | training summaries + evaluation reports | keep | Historical model-eval evidence. |
| `docs/evaluation/evaluation_workflow.md` | Evaluation workflow guide | Medium | Reference | evaluation framework docs | keep | Process reference for eval runs. |
| `docs/evaluation/V16_INFERENCE_TEST_REPORT.md` | V16 inference test report | Low | Reference | V16 evaluation reports | keep | Point-in-time inference evidence. |
| `docs/evaluation/LLM-IDE-KPI-Framework-Objective.md` | KPI framework objective doc | Low | Archive candidate | evaluation framework docs | archive | Strategy narrative with overlap. |
| `docs/evaluation/KPI-Implementation-Quick-Start.md` | KPI quick-start guide | Low | Archive candidate | evaluation framework docs | archive | Quick-start variant duplicates broader framework docs. |
| `docs/evaluation/SEMANTIC_CONTEXT_BENCHMARK_RESULTS.md` | Semantic-context benchmark results | Medium | Reference | benchmark plans + eval reports | keep | Useful benchmark evidence artifact. |
| `docs/evaluation/V16_COMPREHENSIVE_EVALUATION_REPORT.md` | V16 comprehensive evaluation report | Low | Reference | evaluation summary docs | keep | Historical comprehensive report. |
| `docs/evaluation/COMPREHENSIVE_EVALUATION_REPORT.md` | Comprehensive evaluation report | Low | Archive candidate | versioned evaluation reports | archive | Prefer versioned report variants. |
| `docs/evaluation/EVALUATION_SUMMARY.md` | Aggregate evaluation summary | Medium | Reference | comprehensive eval reports | keep | Useful high-level summary reference. |
| `docs/rag/RAG_SYSTEM_ITERATIONS_ANALYSIS.md` | RAG iteration analysis | Low | Archive candidate | legacy architecture/evaluation docs | archive | Legacy RAG-era analysis, non-canonical now. |
| `docs/rag/ENHANCED_RAG_IMPLEMENTATION.md` | Enhanced RAG implementation narrative | Low | Archive candidate | runtime-governed architecture docs | archive | Legacy implementation narrative predating current stack. |
| `docs/stage6c/REAL_MODEL_EVAL_TARGETS.md` | Stage6C model-eval targets | Low | Archive candidate | evaluation plans | archive | Stage-era planning artifact. |
| `docs/RETRIEVAL_REDESIGN_SPEC_V1.md` | Retrieval redesign spec | Medium | Reference | retrieval eval/hardening docs | keep | Useful redesign context, non-live authority. |
| `docs/PR6_TRUE_POSITIVE_DEBUG_AND_MINIMAL_SEMANTIC_LIFT_PLAN.md` | PR6 retrieval/debug lift plan | Low | Archive candidate | layer5 PR6 invariants + retrieval plans | archive | Plan-stage artifact superseded by closure docs. |
| `docs/V16_1_MODEL_UPGRADE_HYPOTHESIS.md` | V16.1 model-upgrade hypothesis | Low | Archive candidate | training/evaluation reports | archive | Hypothesis-stage note, historical only. |
| `docs/VALIDATION_COMPLETENESS_MATRIX.md` | Validation completeness matrix | Medium | Reference | closure reports + tracker | keep | Useful gap-check matrix. |
| `docs/WORKFLOW_TRUTH_TABLE.md` | Workflow truth table | Medium | Reference | execution maps + runtime docs | keep | Supporting truth-table reference. |
| `docs/SCENARIO_CODE_EXECUTION_MAP.md` | Scenario-to-execution mapping | Medium | Reference | validation scenario packs | keep | Helpful mapping artifact. |
| `docs/MODULE_CLASSIFICATION_MATRIX.md` | Module classification matrix | Medium | Reference | repo reality map + audits | keep | Useful structural mapping aid. |
| `docs/CLI_VALIDATION_MATRIX.md` | CLI validation matrix | Medium | Reference | production verification guide | keep | Operational validation matrix. |
| `docs/Backend Production Validation Sheet.md` | Backend production validation sheet | Medium | Active working | production verification runbooks | keep | Practical run-sheet for backend verification. |
| `docs/DEBUG_PATH_VALIDATION_RUNBOOK.md` | Debug-path validation runbook | Medium | Active working | debug-depth charter + audit reports | keep | Useful operational runbook for debug verification. |
| `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md` | Demo environment setup runbook | High | Active working | docs README golden path + demo guides | keep | Core setup runbook in golden path. |
| `docs/MOTADATA_DEMO_SCENARIOS.md` | Demo scenarios and success criteria | High | Active working | demo runbooks + production verification | keep | Core demo scenarios companion. |
| `docs/First-Production-MVP-Slice.md` | MVP slice narrative | Low | Archive candidate | product slice docs + closure declarations | archive | Historical narrative superseded by canonical slice docs. |
| `docs/JetBrains Plugin Defect Isolation Sheet.md` | Plugin defect isolation worksheet | Low | Reference | plugin runbooks + wiring fix notes | keep | Troubleshooting worksheet artifact. |
| `docs/FINDINGS_REGISTER.md` | Findings registry | Medium | Active working | audit docs + validation reports | keep | Useful centralized findings tracker. |
| `docs/DOC_MIGRATION_INDEX.md` | Documentation migration index | Medium | Active working | migration notes + doc audit ledger | keep | Helpful migration crosswalk during cleanup. |
| `docs/PRODUCT_SLICE_CHARTER.md` | Product-slice charter | Medium | Compatibility | PRODUCT_SLICE.md + tracker | keep | Keep as charter context; canonical scope remains PRODUCT_SLICE.md. |
| `docs/QUICK_REFERENCE.md` | Top-level quick reference | Low | Reference | benchmark/evaluation quick references | keep | Short operator reference. |
| `docs/STAGE_A_CANDIDATE_GENERATION_SPEC_V2.md` | Stage-A candidate generation spec | Low | Archive candidate | stage layout docs + runtime specs | archive | Stage-era spec outside current canonical path. |
| `docs/STAGE7_FREEZE_REFINEMENTS_PATCH.md` | Stage7 refinements patch note | Low | Archive candidate | compilation/stage docs | archive | Historical patch note. |
| `docs/STAGE_LAYOUT_CANONICAL.md` | Canonical stage layout note | Medium | Reference | master spec + stage docs | keep | Useful cross-reference note. |
| `docs/MAIN_MERGE_READINESS_REPORT.md` | Main merge readiness report | Low | Archive candidate | integration/merge reports | archive | Pre-merge planning report. |
| `docs/LAYER3_INTEGRATION_REPORT.md` | Layer3 integration report | Medium | Reference | layer3 completion reports | keep | Historical integration evidence. |
| `docs/LAYER3_BASELINE_COMPLETION_REPORT.md` | Layer3 baseline completion report | Medium | Reference | layer3 runtime completion docs | keep | Historical baseline closure artifact. |
| `docs/ML_DIR_SURVEY_STAGE_MAP.md` | ML directory/stage survey map | Low | Reference | layer2 compilation docs | keep | Supporting structural reference for ML tree. |
| `docs/MOTADATA_COMMIT_WORKFLOW.md` | Commit workflow guidance | Medium | Active working | governance execution rules | keep | Practical contributor workflow doc. |
| `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md` | Product architecture narrative | Medium | Reference | master spec + architecture docs | keep | Useful architecture companion narrative. |
| `docs/COMPILATION/README.md` | Layer2 compilation index | High | Reference | layer2 compilation spec | keep | Important index/pointer for Layer2 docs. |
| `docs/notes.md` | Informal notes log | Low | Archive candidate | findings and status docs | archive | Informal narrative notes. |
| `docs/findings-2026-01-08.md` | Historical findings snapshot | Low | Archive candidate | findings register | archive | Date-specific findings snapshot. |
| `docs/motadata-coder_case-studies_2026-01-09.md` | Historical case-studies note | Low | Archive candidate | case-study validation report | archive | Historical date-scoped case study. |
| `docs/CASE_STUDIES_VALIDATION_REPORT.md` | Case studies validation report | Medium | Reference | evaluation reports | keep | Retain as supporting validation evidence. |
| `docs/plan-phase1-deepseekV3Integration.md` | Phase1 deepseek integration plan | Low | Archive candidate | model strategy docs | archive | Legacy integration planning artifact. |
| `docs/LLM-Code-Assistant-Evaluation-Framework.md` | Evaluation framework doc | Medium | Reference | robust evaluation guides | keep | Methodology reference. |
| `docs/LLM-Code-Evaluation-Quick-Reference.md` | Evaluation quick reference | Low | Reference | evaluation framework docs | keep | Lightweight reference companion. |
| `docs/Dataset-analysis.md` | Dataset analysis narrative | Low | Archive candidate | dataset summaries + audits | archive | Legacy analysis note with overlap. |
| `docs/GLOSSARY.md` | Term glossary | High | Reference | master system spec + contracts | keep | Useful terminology reference. |
| `docs/agents/AGENTS_IMPLEMENTATION_PLAN.md` | Agents implementation planning doc | Low | Archive candidate | runtime architecture + orchestration docs | archive | Plan-stage doc from prior architecture phase. |
| `docs/troubleshooting/DEBUGGING_GUIDE.md` | Troubleshooting/debugging guide | Medium | Active working | runbooks + runtime troubleshooting docs | keep | Useful operator troubleshooting guide. |
| `docs/DVC_ARTIFACTS_README.md` | DVC artifacts guidance | Medium | Reference | artifact governance policy | keep | Practical DVC usage reference. |
| `docs/DVC_R2_SETUP.md` | DVC R2 setup instructions | Medium | Reference | DVC artifacts guidance | keep | Environment setup reference. |

---

## 18) Batch D tranche 3F — runtime/observation/governance-root + external residuals

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `runtime/README.md` | Runtime namespace boundary/index | High | Reference | docs/runtime/README + layer specs | keep | Important cross-link index for runtime boundaries. |
| `runtime/plan_gate_service/README.md` | Plan-Gate service runtime contract | High | Canonical | docs/runtime contracts + schemas | keep | Operational contract for governed endpoint surface. |
| `runtime/plan_gate_stub/README.md` | Plan-Gate stub protocol runner guide | Medium | Compatibility | shadow protocol docs + plan service docs | keep | Compatibility/testing harness reference. |
| `runtime/ci_gate/README.md` | CI backstop gate behavior | Medium | Reference | plan-gate service + CI model docs | keep | Useful CI enforcement contract reference. |
| `runtime/config/README.md` | Runtime config topology and env guidance | Medium | Active working | B5 host readiness + setup runbooks | keep | Current setup guidance for distributed host model. |
| `runtime/ask_validation/README.md` | Layer5 Ask validation harness guide | Medium | Active working | validation docs + runtime tests | keep | Practical harness usage and metrics reference. |
| `runtime/obs/README.md` | Stage3 mini-ledger doc | Medium | Reference | runtime/observation package docs | keep | Clear scope note for Stage3 ledger vs full observation. |
| `runtime/rag/README.md` | Legacy runtime RAG stub pointer | Low | Archive candidate | archive/legacy_runtime_rag docs | archive | Explicitly deprecated runtime path pointer. |
| `runtime/layer5/README.md` | Layer5 workspace resolver/index overview | Medium | Reference | docs/layer5 docs + runtime layer5 modules | keep | Useful implementation index. |
| `runtime/layer5/index/A5_HANDOFF.md` | A5 handoff for file index contract | Medium | Reference | layer5 index code + evidence contract | keep | Stable handoff contract for retrieval inputs. |
| `runtime/layer5/retrieval/A6_HANDOFF.md` | A6 lexical retrieval handoff | Medium | Reference | layer5 retrieval code + evidence contract | keep | Stable retrieval scoring contract reference. |
| `runtime/layer5/evidence/evidence_bundle.v1.md` | Evidence bundle v1 normative contract | High | Canonical | schema + docs/validation artifacts | keep | Canonical contract for `layer5.evidence_bundle.v1`. |
| `runtime/layer5/evidence/provisional_schema.md` | Deprecated provisional schema note | Low | Archive candidate | evidence_bundle.v1.md | archive | Deprecated bridge note superseded by frozen v1. |
| `runtime/layer5/evidence/FREEZE_CHECKLIST.md` | Wave 2/2.5 freeze checklist | Medium | Active working | evidence bundle v1 + tests | keep | Active freeze/governance checklist. |
| `runtime/layer5/evidence/samples/README.md` | Evidence sample payload guide | Medium | Reference | evidence bundle contract + schema validation | keep | Useful sample-validation reference. |
| `runtime/layer5/evidence/golden/README.md` | Golden evidence fixture regeneration instructions | Medium | Reference | evidence contract + golden tests | keep | Golden fixture provenance/reference doc. |
| `runtime/layer5/audit/pr6_real_repo_run_report.md` | PR6 retrieval audit report | Medium | Reference | docs/layer5 PR6 invariants + validation docs | keep | High-signal retrieval audit evidence. |
| `observation/README.md` | Observation layer package index | High | Reference | docs/OBSERVATION index + layer4 spec | keep | Core index for observation tooling package. |
| `observation/ingest/README.md` | Observation ingest CLI contract | High | Canonical | shadow schemas + observation outputs | keep | Canonical CLI contract for ingest behavior. |
| `observation/baseline/README.md` | Baseline/drift runner contract | High | Canonical | baseline outputs + drift thresholds | keep | Canonical baseline/compare behavior definition. |
| `observation/judge_drift_suite/IMPLEMENTATION_SUMMARY.md` | Judge drift suite implementation summary | Medium | Reference | observation tests + thresholds | keep | Useful implementation/evidence summary. |
| `observation/ingest/golden_reports/pr_merge_report.md` | Golden ingest sample report (PR merge) | Low | Reference | ingest README + golden reports set | keep | Golden output fixture for deterministic behavior. |
| `observation/ingest/golden_reports/jsonl_report.md` | Golden ingest sample report (JSONL) | Low | Reference | ingest README + golden reports set | keep | Golden output fixture for JSONL path. |
| `observation/ingest/golden_reports/config_change_report.md` | Golden ingest sample report (config change) | Low | Reference | ingest README + golden reports set | keep | Golden output fixture for config-change scenario. |
| `observation/baseline/golden_outputs/baseline_report.md` | Golden baseline report sample | Low | Reference | baseline README + drift report sample | keep | Golden baseline fixture output. |
| `observation/baseline/golden_outputs/drift_report.md` | Golden drift report sample | Low | Reference | baseline README + thresholds | keep | Golden drift fixture output. |
| `governance/README.md` | Governance layer canonical entry | High | Reference | docs/master spec + governance corpus | keep | High-value governance navigator. |
| `governance/CONSTITUTIONAL_MANIFEST_v1.0.md` | Golden exemplars constitutional manifest | High | Canonical | docs/layer1 spec + governance phase docs | keep | Core constitutional doctrine source. |
| `governance/REPOSITORY_CONSTITUTION.md` | Repository structural constitution | Medium | Canonical | governance README + project structure docs | keep | Structural governance boundary contract. |
| `governance/PROJECT_STATE_LEDGER.md` | Governance project state snapshot | Low | Partially stale | tracker + Layer2 verification artifacts | keep | Historical/governance-facing snapshot; tracker remains live authority. |
| `governance/PHASE_STATUS_REPORT.md` | Governance phase status report | Low | Partially stale | tracker + release verification artifacts | keep | Status snapshot preserved for lineage, not live truth. |
| `governance/AI-Session-Progress-Tracker.md` | Session-era macro/progress note | Low | Archive candidate | project state ledger + tracker docs | archive | Informal continuity macro, non-canonical. |
| `governance/golden-exemplars/GREG/GREG-Initiation-Ratification-v0.9.md` | GREG initiation ratification protocol | Medium | Reference | GREG package docs + constitutional manifest | keep | Formal governance review artifact. |
| `governance/golden-exemplars/GREG/GREG-Pre-Review-Package.md` | GREG pre-review package | Medium | Reference | GREG ratification docs | keep | Governance review preparation artifact. |
| `governance/golden-exemplars/GREG/GREG_Pre-Review_Attack_Result.md` | GREG pre-review attack results | Medium | Reference | GREG review package | keep | Useful governance validation evidence. |
| `governance/golden-exemplars/Phases/Cross-phase_Readiness_Declaration.md` | Cross-phase readiness declaration | Medium | Canonical | phase doctrine docs | keep | Constitutional cross-phase readiness declaration artifact. |
| `validation/STAGE2_CLOSURE_NOTE.md` | Stage2 closure note (root validation set) | Medium | Reference | docs/validation closure docs | keep | Historical closure evidence outside docs tree. |
| `validation/stage2_human_audit_checkpoint.md` | Stage2 human audit checkpoint template | Medium | Active working | stage2 metrics report | keep | Practical audit checklist template. |
| `validation/stage2_metrics_report.md` | Stage2 metrics report artifact | Medium | Reference | stage2 closure + failure log | keep | Evidence artifact for stage2 lock decision. |
| `validation/stage2_failure_log.md` | Stage2 failure log artifact | Low | Reference | stage2 metrics report | keep | Empty/no-failure evidence log. |
| `packaging/motadata-context-layer/README.md` | Context-layer wheel packaging guide | High | Active working | runtime layer5 docs + deployment guides | keep | Operational packaging/build contract. |
| `README.md` | Root repository entrypoint | High | Canonical | docs/README + tracker + master spec | keep | Primary repo entrypoint for operators/developers. |
| `MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md` | Long-form master system guide narrative | Medium | Compatibility | master spec + governance docs | keep | Supporting long-form guide; not live status authority. |
| `plan-stage25AssistLayerV1.prompt.md` | Stage2.5 Assist planning prompt | Low | Archive candidate | assist docs + tracker follow-on | archive | Planning prompt artifact; archival value only. |

---

## 19) Initial archive-move candidate manifest (v0)

First-pass candidates ready for archive relocation in a controlled move batch (no content rewrite):

| File path | Source tranche | Reason |
|---|---|---|
| `docs/evaluation/KPI-Implementation-Quick-Start.md` | 3E | Duplicate quick-start variant of broader evaluation framework docs. |
| `docs/evaluation/LLM-IDE-KPI-Framework-Objective.md` | 3E | Strategy narrative superseded by consolidated framework and current validation runbooks. |
| `docs/evaluation/COMPREHENSIVE_EVALUATION_REPORT.md` | 3E | Non-versioned duplicate; prefer versioned report artifacts. |
| `docs/rag/RAG_SYSTEM_ITERATIONS_ANALYSIS.md` | 3E | Legacy RAG-era analysis outside current governed runtime architecture. |
| `docs/rag/ENHANCED_RAG_IMPLEMENTATION.md` | 3E | Legacy implementation narrative predating current stack. |
| `docs/stage6c/REAL_MODEL_EVAL_TARGETS.md` | 3E | Stage-era planning artifact with low active relevance. |
| `docs/First-Production-MVP-Slice.md` | 3E | Historical narrative superseded by canonical product-slice docs. |
| `docs/STAGE_A_CANDIDATE_GENERATION_SPEC_V2.md` | 3E | Stage-era spec not on current canonical path. |
| `docs/STAGE7_FREEZE_REFINEMENTS_PATCH.md` | 3E | Historical patch note with low operational value. |
| `docs/MAIN_MERGE_READINESS_REPORT.md` | 3E | Pre-merge readiness report, historical only. |
| `docs/agents/AGENTS_IMPLEMENTATION_PLAN.md` | 3E | Planning artifact from prior architecture phase. |
| `docs/plan-phase1-deepseekV3Integration.md` | 3E | Legacy model-integration planning note. |
| `docs/notes.md` | 3E | Informal notes superseded by formal findings/ledger docs. |
| `runtime/rag/README.md` | 3F | Explicit legacy stub pointer; archive-friendly relocation target. |
| `governance/AI-Session-Progress-Tracker.md` | 3F | Session macro artifact, not canonical governance authority. |
| `plan-stage25AssistLayerV1.prompt.md` | 3F | Planning prompt artifact with no runtime authority role. |

---

## 20) Batch D tranche 3G — governance phase corpus + review packages

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `governance/golden-exemplars/Phases/Phase-01/REF-01.md` | Phase-01 refusal exemplar | High | Canonical | constitutional manifest + phase docs | keep | Core REF exemplar. |
| `governance/golden-exemplars/Phases/Phase-01/REF-02.md` | Phase-01 refusal exemplar | High | Canonical | REF exemplar set | keep | Core REF exemplar. |
| `governance/golden-exemplars/Phases/Phase-01/RCA-01.md` | Phase-01 RCA exemplar | High | Canonical | phase-01 corpus | keep | Core RCA exemplar. |
| `governance/golden-exemplars/Phases/Phase-01/RCA-02.md` | Phase-01 RCA exemplar | High | Canonical | phase-01 corpus | keep | Core RCA exemplar. |
| `governance/golden-exemplars/Phases/Phase-01/ANOM-01.md` | Phase-01 anomaly exemplar | High | Canonical | phase-01 corpus | keep | Core anomaly exemplar. |
| `governance/golden-exemplars/Phases/Phase-01/ANOM-02.md` | Phase-01 anomaly exemplar | High | Canonical | phase-01 corpus | keep | Core anomaly exemplar. |
| `governance/golden-exemplars/Phases/Phase-01/PHASE_01_REVIEW_GUIDE.md` | Phase-01 review guidance | Medium | Reference | review package docs | keep | Reviewer guidance companion. |
| `governance/golden-exemplars/Phases/Phase-01/README.md` | Phase-01 index/readme | Medium | Reference | phase-01 exemplars | keep | Navigation/index doc. |
| `governance/golden-exemplars/Phases/Phase-01/Phase-01_Review.md` | Phase-01 review summary | Medium | Reference | review package + distribution summary | keep | Review evidence summary. |
| `governance/golden-exemplars/Phases/Phase-01/REVIEW_DISTRIBUTION_SUMMARY.md` | Distribution/reviewer summary | Low | Archive candidate | phase-01 review package | archive | Process log artifact. |
| `governance/golden-exemplars/Phases/Phase-01/archives/Phase-01_Validation.md` | Archived phase-01 validation note | Low | Archive candidate | phase-01 review docs | keep | Already archived subtree content. |
| `governance/golden-exemplars/Phases/Phase-01/archives/Phase-01_Hardening_Review.md` | Archived hardening review | Low | Archive candidate | phase-01 review docs | keep | Already archived subtree content. |
| `governance/golden-exemplars/Phases/Phase-01/archives/Notes.md` | Archived notes | Low | Archive candidate | phase-01 docs | keep | Archived notes only. |
| `governance/golden-exemplars/Phases/Phase-01/archives/README copy.md` | Archived legacy readme copy | Low | Archive candidate | phase-01 readme | keep | Legacy duplicate in archived location. |
| `governance/golden-exemplars/Phases/Phase-02/CONF-01.md` | Phase-02 CONF exemplar | High | Canonical | phase-02 corpus | keep | Core CONF exemplar. |
| `governance/golden-exemplars/Phases/Phase-02/CONF-02.md` | Phase-02 CONF exemplar | High | Canonical | phase-02 corpus | keep | Core CONF exemplar. |
| `governance/golden-exemplars/Phases/Phase-02/CONF-03.md` | Phase-02 CONF exemplar | High | Canonical | phase-02 corpus | keep | Core CONF exemplar. |
| `governance/golden-exemplars/Phases/Phase-02/CONF-04.md` | Phase-02 CONF exemplar | High | Canonical | phase-02 corpus | keep | Core CONF exemplar. |
| `governance/golden-exemplars/Phases/Phase-02/CONF-05.md` | Phase-02 CONF exemplar | High | Canonical | phase-02 corpus | keep | Core CONF exemplar. |
| `governance/golden-exemplars/Phases/Phase-02/CONF-06.md` | Phase-02 CONF exemplar | High | Canonical | phase-02 corpus + phase-06 constitution | keep | Core CONF exemplar with endurance linkage. |
| `governance/golden-exemplars/Phases/Phase-02/CONF-Schema.md` | Phase-02 schema/authoring contract | High | Canonical | constitutional manifest | keep | Canonical CONF authoring schema. |
| `governance/golden-exemplars/Phases/Phase-02/Phase-02_Review.md` | Phase-02 review summary | Medium | Reference | phase-02 exemplars | keep | Review evidence summary. |
| `governance/golden-exemplars/Phases/Phase-02/archives/README.md` | Phase-02 archived notes index | Low | Archive candidate | phase-02 docs | keep | Archived subtree file. |
| `governance/golden-exemplars/Phases/Phase-02/archives/Notes.md` | Phase-02 archived notes | Low | Archive candidate | phase-02 docs | keep | Archived notes. |
| `governance/golden-exemplars/Phases/Phase-02/archives/30s-Hygeine-CheckList.md` | Legacy checklist note | Low | Archive candidate | phase-02 review artifacts | keep | Archived process checklist. |
| `governance/golden-exemplars/Phases/Phase-03/DES-01.md` | Phase-03 DES exemplar | High | Canonical | phase-03 corpus | keep | Core DES exemplar. |
| `governance/golden-exemplars/Phases/Phase-03/DES-02.md` | Phase-03 DES exemplar | High | Canonical | phase-03 corpus | keep | Core DES exemplar. |
| `governance/golden-exemplars/Phases/Phase-03/DES-03.md` | Phase-03 DES exemplar | High | Canonical | phase-03 corpus | keep | Core DES exemplar. |
| `governance/golden-exemplars/Phases/Phase-03/DES-04.md` | Phase-03 DES exemplar | High | Canonical | phase-03 corpus | keep | Core DES exemplar. |
| `governance/golden-exemplars/Phases/Phase-03/DES-05.md` | Phase-03 DES exemplar | High | Canonical | phase-03 corpus | keep | Core DES exemplar. |
| `governance/golden-exemplars/Phases/Phase-03/DES-06.md` | Phase-03 endurance DES exemplar | High | Canonical | phase-06 constitution | keep | Canonical DES endurance exemplar. |
| `governance/golden-exemplars/Phases/Phase-03/DES-Correlation-01.md` | DES correlation exemplar | High | Canonical | DES corpus + CODE reconciliation notes | keep | Canonical DES correlation path. |
| `governance/golden-exemplars/Phases/Phase-03/DES-schema.md` | DES schema/authoring contract | High | Canonical | constitutional manifest | keep | Canonical DES authoring schema. |
| `governance/golden-exemplars/Phases/Phase-03/DES-CheckList.md` | DES checklist | Medium | Reference | DES schema | keep | Authoring/review checklist. |
| `governance/golden-exemplars/Phases/Phase-03/README.md` | Phase-03 index/readme | Medium | Reference | DES corpus | keep | Navigation/index doc. |
| `governance/golden-exemplars/Phases/Phase-04/MIX-01.md` | Phase-04 MIX exemplar | High | Canonical | MIX corpus | keep | Core MIX exemplar. |
| `governance/golden-exemplars/Phases/Phase-04/MIX-02.md` | Phase-04 MIX exemplar | High | Canonical | MIX corpus | keep | Core MIX exemplar. |
| `governance/golden-exemplars/Phases/Phase-04/MIX-03.md` | Phase-04 MIX exemplar | High | Canonical | MIX corpus | keep | Core MIX exemplar. |
| `governance/golden-exemplars/Phases/Phase-04/MIX-04.md` | Phase-04 MIX exemplar | High | Canonical | MIX constitution + cross-phase audit | keep | Core MIX exemplar. |
| `governance/golden-exemplars/Phases/Phase-04/MIX-04-Constitution.md` | MIX constitutional framing | High | Canonical | MIX schema + phase constitution | keep | Canonical constitutional companion. |
| `governance/golden-exemplars/Phases/Phase-04/Mix-Schema.md` | MIX schema contract | High | Canonical | constitutional manifest + phase docs | keep | Canonical MIX schema. |
| `governance/golden-exemplars/Phases/Phase-04/Phase-04-Lifecycle.md` | MIX lifecycle guidance | Medium | Reference | MIX schema | keep | Lifecycle/reference doc. |
| `governance/golden-exemplars/Phases/Phase-04/Phase-04_Phase-05_Handoff.md` | MIX to CODE handoff guide | Medium | Reference | phase-05 docs | keep | Handoff companion doc. |
| `governance/golden-exemplars/Phases/Phase-04/Phase-04_Adversarial_Swap_Comparisons.md` | Adversarial swap comparison study | Medium | Reference | phase-04 validation docs | keep | Supporting validation artifact. |
| `governance/golden-exemplars/Phases/Phase-04/Phase-04_Antipatterns.md` | Anti-pattern catalog | Medium | Reference | MIX schema + exemplars | keep | Supporting guardrail guide. |
| `governance/golden-exemplars/Phases/Phase-04/Notes.md` | Phase-04 notes | Low | Archive candidate | phase-04 docs | archive | Informal notes artifact. |
| `governance/golden-exemplars/Phases/Phase-05/CODE-01.md` | Phase-05 CODE exemplar | High | Canonical | code guard set | keep | Core CODE guard exemplar. |
| `governance/golden-exemplars/Phases/Phase-05/CODE-02.md` | Phase-05 CODE exemplar | High | Canonical | code guard set | keep | Core CODE guard exemplar. |
| `governance/golden-exemplars/Phases/Phase-05/CODE-04.md` | Phase-05 CODE exemplar | High | Canonical | code guard set | keep | Core CODE guard exemplar. |
| `governance/golden-exemplars/Phases/Phase-05/CODE-05.md` | Phase-05 CODE exemplar | High | Canonical | code guard set | keep | Core CODE guard exemplar. |
| `governance/golden-exemplars/Phases/Phase-05/CODE-06.md` | Phase-05 CODE exemplar | High | Canonical | code guard set | keep | Core CODE guard exemplar. |
| `governance/golden-exemplars/Phases/Phase-05/CODE-07.md` | Phase-05 CODE exemplar | High | Canonical | code guard set | keep | Core CODE guard exemplar. |
| `governance/golden-exemplars/Phases/Phase-05/CODE-08.md` | Phase-05 CODE exemplar | High | Canonical | code guard set + phase-06 checks | keep | Core CODE guard exemplar. |
| `governance/golden-exemplars/Phases/Phase-05/Phase-05—Preamble_Schema.md` | Phase-05 preamble schema | High | Canonical | CODE exemplar set | keep | Canonical CODE preamble contract. |
| `governance/golden-exemplars/Phases/Phase-05/Notes.md` | Phase-05 notes | Low | Archive candidate | phase-05 docs | archive | Informal notes artifact. |
| `governance/golden-exemplars/Phases/Phase-06/CONF-06-Constitution.md` | Phase-06 CONF endurance constitution | High | Canonical | phase-02/06 doctrine | keep | Canonical endurance constitution. |
| `governance/golden-exemplars/Phases/Phase-06/DES-06-Constitution.md` | Phase-06 DES endurance constitution | High | Canonical | phase-03/06 doctrine | keep | Canonical endurance constitution. |
| `governance/golden-exemplars/Phases/Phase-06/Phase-06_Lock_Procedure_Structural_Closure_Gate.md` | Phase-06 lock/closure gate | High | Canonical | exit verification + cross-phase audit | keep | Canonical closure gate procedure. |
| `governance/golden-exemplars/Phases/Phase-06/Phase-06_Exit_Verification_Report.md` | Phase-06 exit verification report | Medium | Reference | lock procedure + cross-phase audit | keep | Closure evidence report. |
| `governance/golden-exemplars/Phases/Phase-06/Phase-06-Cross-Phase-Audit.md` | Phase-06 cross-phase audit | Medium | Reference | lock procedure + phase corpus | keep | Cross-phase validation evidence. |
| `governance/golden-exemplars/Phases/Phase-06/Notes.md` | Phase-06 notes | Low | Archive candidate | phase-06 closure docs | archive | Informal notes artifact. |
| `governance/review-packages/Phase-01_Review_Package/README.md` | External review package index | Low | Archive candidate | phase-01 review docs | archive | Process package, historical after lock. |
| `governance/review-packages/Phase-01_Review_Package/PACKAGE_MANIFEST.md` | Review package manifest | Low | Archive candidate | package readme | archive | Process inventory artifact. |
| `governance/review-packages/Phase-01_Review_Package/EMAIL_TO_TEAM.md` | Review coordination email templates | Low | Archive candidate | coordinator docs | archive | Ops communication artifact. |
| `governance/review-packages/Phase-01_Review_Package/5_MINUTE_BRIEFING_SCRIPT.md` | Briefing script | Low | Archive candidate | package orientation docs | archive | Review coordination artifact. |
| `governance/review-packages/Phase-01_Review_Package/COORDINATOR_QUICK_START.md` | Coordinator quick-start | Low | Archive candidate | package orientation docs | archive | Process runbook artifact. |
| `governance/review-packages/Phase-01_Review_Package/01_START_HERE/PHASE_01_REVIEW_GUIDE.md` | Review guide copy for package | Low | Compatibility | phase-01 canonical review guide | archive | Duplicated guide packaged for distribution. |
| `governance/review-packages/Phase-01_Review_Package/02_ORIENTATION_GUIDES/01_External_Review_Handout.md` | External review handout | Low | Archive candidate | package guide docs | archive | Distribution artifact. |
| `governance/review-packages/Phase-01_Review_Package/02_ORIENTATION_GUIDES/02_Reviewer_Walkthrough.md` | Reviewer walkthrough | Low | Archive candidate | package guide docs | archive | Distribution artifact. |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/REF-01.md` | Packaged exemplar copy | Low | Compatibility | canonical phase exemplar files | archive | Duplicate exemplar copy in package. |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/RCA-01.md` | Packaged exemplar copy | Low | Compatibility | canonical phase exemplar files | archive | Duplicate exemplar copy in package. |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/RCA-02.md` | Packaged exemplar copy | Low | Compatibility | canonical phase exemplar files | archive | Duplicate exemplar copy in package. |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/ANOM-01.md` | Packaged exemplar copy | Low | Compatibility | canonical phase exemplar files | archive | Duplicate exemplar copy in package. |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/ANOM-02.md` | Packaged exemplar copy | Low | Compatibility | canonical phase exemplar files | archive | Duplicate exemplar copy in package. |
| `governance/review-packages/Phase-01_Review_Package/04_REFERENCE_OPTIONAL/Golden_Exemplars_Guide_v1.5.md` | Optional reference guide copy | Low | Compatibility | governance and ml guide copies | archive | Packaged duplicate reference copy. |
| `governance/review-packages/Phase-01_Review_Package/04_REFERENCE_OPTIONAL/Reviewer_Scoring_Rubric.md` | Optional scoring rubric copy | Low | Compatibility | reviewer rubric docs | archive | Packaged duplicate reference copy. |

---

## 21) Archive-move candidate manifest (v1 addendum)

Additional candidates from tranche 3G:

| File path | Source tranche | Reason |
|---|---|---|
| `governance/golden-exemplars/Phases/Phase-04/Notes.md` | 3G | Informal notes superseded by canonical schema/exemplar set. |
| `governance/golden-exemplars/Phases/Phase-05/Notes.md` | 3G | Informal notes superseded by canonical CODE corpus. |
| `governance/golden-exemplars/Phases/Phase-06/Notes.md` | 3G | Informal notes superseded by lock/verification reports. |
| `governance/golden-exemplars/Phases/Phase-01/REVIEW_DISTRIBUTION_SUMMARY.md` | 3G | Distribution process log with low ongoing authority value. |
| `governance/review-packages/Phase-01_Review_Package/README.md` | 3G | Historical external-review package wrapper. |
| `governance/review-packages/Phase-01_Review_Package/PACKAGE_MANIFEST.md` | 3G | Historical package inventory artifact. |
| `governance/review-packages/Phase-01_Review_Package/EMAIL_TO_TEAM.md` | 3G | One-time coordination templates. |
| `governance/review-packages/Phase-01_Review_Package/5_MINUTE_BRIEFING_SCRIPT.md` | 3G | One-time review briefing script. |
| `governance/review-packages/Phase-01_Review_Package/COORDINATOR_QUICK_START.md` | 3G | Historical coordination runbook. |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/REF-01.md` | 3G | Duplicate exemplar copy (canonical file exists in phase corpus). |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/RCA-01.md` | 3G | Duplicate exemplar copy (canonical file exists in phase corpus). |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/RCA-02.md` | 3G | Duplicate exemplar copy (canonical file exists in phase corpus). |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/ANOM-01.md` | 3G | Duplicate exemplar copy (canonical file exists in phase corpus). |
| `governance/review-packages/Phase-01_Review_Package/03_EXEMPLARS_TO_REVIEW/ANOM-02.md` | 3G | Duplicate exemplar copy (canonical file exists in phase corpus). |

---

## 22) Batch D tranche 3H — `ml/**` + `archive/**` corpus sweep

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `ml/README.md` | Layer-2 ML namespace index | High | Reference | layer2 spec + training pipeline docs | keep | Canonical index for ML subtree (`1 file`). |
| `ml/artifacts/REGISTRY.md` | Artifact registry index | Medium | Reference | artifact policy + checkpoints docs | keep | Artifact pointer/index (`1 file`). |
| `ml/artifacts/checkpoints/*.md` | Checkpoint notes/manifests | Low | Compatibility | training results + artifact registry | keep | Checkpoint-era compatibility notes (`3 files`). |
| `ml/datasets/*.md` | Dataset summaries/specifications | Medium | Reference | docs/datasets + training reports | keep | Dataset reference set (`4 files`). |
| `ml/datasets/cpt/README.md` | CPT dataset index | Medium | Reference | dataset summaries | keep | CPT-specific index (`1 file`). |
| `ml/datasets/tools/Phase-C.md` | Dataset tooling phase note | Low | Reference | pipeline stage docs | keep | Tooling note (`1 file`). |
| `ml/evaluation/**/*.md` | Model evaluation analysis/reports | Medium | Reference | docs/evaluation + validation reports | keep | Compact eval evidence set (`3 files`). |
| `ml/training/ARCHITECTURE_LOCK_v2.md` | Training architecture lock note | Medium | Reference | layer2 docs + training pipeline | keep | Locked architecture reference (`1 file`). |
| `ml/training/ARTIFACT_POLICY.md` | Training artifact policy | Medium | Reference | artifact governance docs | keep | Policy companion (`1 file`). |
| `ml/training/AUDIT_READINESS_REPORT_v1.md` | Audit readiness report | Low | Reference | training/pipeline reports | keep | Audit evidence note (`1 file`). |
| `ml/training/compiler/*.md` | Compiler contracts/index | Medium | Reference | compilation docs | keep | Compiler reference set (`2 files`). |
| `ml/training/datasets/sft/*.md` | SFT dataset readme set | Low | Compatibility | training SFT docs | keep | Dataset compatibility notes (`1 file`). |
| `ml/training/evaluation/*.md` | Training-eval planning notes | Low | Reference | evaluation reports | keep | Evaluation planning artifact (`1 file`). |
| `ml/training/freeze_manifests/stage6c/*.md` | Freeze/import summary notes | Low | Reference | stage6c reports | keep | Freeze-manifest evidence (`1 file`). |
| `ml/training/generated/README.md` | Generated-output subtree index | Low | Compatibility | training outputs | keep | Generated artifact pointer (`1 file`). |
| `ml/training/models/*/*.md` | Model patch notes | Low | Compatibility | checkpoints/results docs | keep | Model-output notes (`1 file`). |
| `ml/training/pipeline/**/*.md` | Stage pipeline design/reports (stages 1–8 incl. stage6 subtree) | Medium | Reference | layer2 spec + closure reports | keep | Core historical pipeline corpus (`31 files`). |
| `ml/training/results/*.md` | Training result analysis notes | Medium | Reference | evaluation reports | keep | Result-analysis artifact (`1 file`). |
| `ml/training/sft/README.md` | SFT subtree index | Medium | Reference | SFT docs + exemplars | keep | SFT navigation entry (`1 file`). |
| `ml/training/sft/docs/*.md` | SFT framework/scorecards/migration notes | Low | Reference | docs/evaluation + training pipeline | keep | SFT methodology set (`6 files`). |
| `ml/training/sft/exemplars/**/*.md` | SFT exemplar mirrors, guides, archived reviewer packs, category notes | Low | Compatibility | governance golden exemplars corpus | keep | Large mirror/historical corpus; not primary constitutional source (`46 files`). |
| `ml/training/sft/stage7/*.md` | Stage7 drift audit note | Low | Reference | stage7/freeze docs | keep | Stage7-specific artifact (`1 file`). |
| `ml/training/sft/variants/*.md` | Variant note | Low | Compatibility | stage4/variant docs | keep | Variant-era artifact (`1 file`). |
| `archive/README.md` | Archive root policy/index | High | Reference | docs/archive docs | keep | Canonical root archive index (`1 file`). |
| `archive/workspace_intelligence/**/*.md` | Archived workspace-intelligence spike notes | Low | Archive candidate | runtime/layer5 docs | keep | Archived by design (`2 files`). |
| `archive/legacy_runtime_rag/**/*.md` | Legacy RAG architecture/API/implementation docs | Low | Archive candidate | runtime/rag stub + historical architecture docs | keep | Archived legacy runtime corpus (`8 files`). |
| `archive/hostB_proof_pack/**/*.md` | Host-B proof pack and verdict notes | Low | Archive candidate | B5 host readiness docs | keep | Archived proof-pack artifacts (`2 files`). |
| `archive/planning/*.prompt.md` | Historical planning prompts | Low | Archive candidate | current tracker/charter docs | keep | Archived planning prompts (`3 files`). |
| `archive/reorg/repo_audit/*.md` | Historical repo audit/reorg mapping docs | Low | Archive candidate | docs/audit current ledger | keep | Archived reorg audit corpus (`10 files`). |
| `archive/reorg/repo_reorg_plan/*.md` | Historical reorg action plans | Low | Archive candidate | docs/audit + migration index | keep | Archived reorg planning set (`7 files`). |
| `archive/okr/*.md` | OKR narratives and progress notes | Low | Archive candidate | tracker + closure docs | keep | Archived OKR set (`4 files`). |
| `archive/okr/supporting-docs/*.md` | OKR supporting references | Low | Archive candidate | docs/reference + validation docs | keep | Archived support references (`10 files`). |
| `archive/docs/**/*.md` | Historical legacy docs, session logs, v15 logs, cleanup snapshots | Low | Archive candidate | current docs canonical spine | keep | Archived historical documentation corpus (`50 files`). |

---

## 23) Archive-move candidate manifest (v2, move-ready seed)

Move-ready candidates identified in 3H sweep:

| File path | Source tranche | Reason |
|---|---|---|
| `ml/training/sft/exemplars/**/*.md` | 3H | Mirror/historical training corpus; compatibility-only versus governance canonical exemplars. |
| `ml/training/sft/stage7/*.md` | 3H | Stage-specific historical drift note set. |
| `ml/training/sft/variants/*.md` | 3H | Variant-era historical artifact with low operational value. |
| `ml/training/models/*/*.md` | 3H | Model-patch note artifacts; not canonical control-plane docs. |
| `archive/workspace_intelligence/**/*.md` | 3H | Already archived spike material. |
| `archive/legacy_runtime_rag/**/*.md` | 3H | Legacy runtime stack docs already outside canonical product slice. |
| `archive/planning/*.prompt.md` | 3H | Historical planning prompts retained for provenance only. |
| `archive/reorg/repo_audit/*.md` | 3H | Historical reorg audit corpus superseded by active ledger decisions. |
| `archive/reorg/repo_reorg_plan/*.md` | 3H | Historical reorg planning corpus. |
| `archive/okr/*.md` | 3H | Historical OKR narrative set. |
| `archive/okr/supporting-docs/*.md` | 3H | Historical supporting references already archived. |
| `archive/docs/**/*.md` | 3H | Large legacy docs corpus; archive-only retention path. |

---

## 24) Batch D tranche 3I — recount, duplicate normalization, residual closure

| File path | Purpose | Current relevance | Canonicality | Overlaps with | Disposition | Notes |
|---|---|---|---|---|---|---|
| `docs/validation/artifacts/plugin_ui_truth_final_demo*/**/*.md` | Plugin UI truth final-demo matrices/checklists | Low | Reference | plugin UI truth certification + closure docs | keep | Residual validation artifact cluster (`45 files`). |
| `docs/validation/artifacts/aiops_mvp/summary/run_summary.md` | AIOps MVP run summary artifact | Low | Reference | AIOps MVP validation docs | keep | Residual summary artifact (`1 file`). |
| `docs/validation/b5_wsl_backend_gpu/README.md` | Legacy B5 artifact path readme | Low | Compatibility | docs/validation/artifacts/b5_wsl_backend_gpu/README.md | keep | Compatibility duplicate path entry (`1 file`). |
| `docs/effort-benefits-risks_analysis.md` | Effort/benefit/risk analysis note | Low | Reference | audit/planning notes | keep | Residual top-level analysis note (`1 file`). |
| `ml/artifacts/checkpoints/**/*.md` | Nested checkpoint readmes | Low | Compatibility | artifact registry + training outputs | keep | Residual nested checkpoint docs (`3 files`). |
| `runtime/layer5/audit/l58*/l58_grounded_report.md` | L5.8 grounded report run outputs | Low | Reference | l58 grounded report artifact under docs | keep | Residual run-output evidence set (`11 files`). |
| `validation/runs/**/stage2_metrics_report.md` | Stage2 run metrics snapshots | Low | Reference | root validation stage2 metrics docs | keep | Residual generated run outputs (`3 files`). |
| `validation/runs/**/stage2_failure_log.md` | Stage2 run failure-log snapshots | Low | Reference | root validation stage2 failure logs | keep | Residual generated run outputs (`3 files`). |

Duplicate normalization outcome (3I):
- Duplicate path entries detected in ledger rows: **32**
- Normalization rule: retain first classification row as authoritative; later duplicate occurrences are treated as manifest/linkage echoes, not additional inventory volume.
- Inventory accounting after normalization uses **unique resolved paths only**.

---

## 25) Archive execution manifest v1 (finalized)

This is the move-ready v1 archive set, merged from v0/v1/v2 manifests and normalized for execution:

| Move group | Candidate scope | Execution posture |
|---|---|---|
| Legacy review packages | `governance/review-packages/Phase-01_Review_Package/**` | Move/retain in archive as historical package (no content rewrites). |
| Governance notes/log artifacts | `governance/golden-exemplars/Phases/**/Notes.md`, `governance/golden-exemplars/Phases/Phase-01/REVIEW_DISTRIBUTION_SUMMARY.md`, `governance/AI-Session-Progress-Tracker.md` | Move to archive/governance-history bucket; keep canonical exemplar/schema corpus in place. |
| Legacy planning prompts | `plan-stage25AssistLayerV1.prompt.md`, `archive/planning/*.prompt.md` | Archive as planning history; not active guidance. |
| Legacy RAG and reorg corpus | `archive/legacy_runtime_rag/**`, `archive/reorg/**`, `archive/workspace_intelligence/**` | Already archived; mark as frozen-historical (no reactivation). |
| Legacy docs narratives | `archive/docs/**/*.md`, selected docs-level archive candidates from 3E | Keep archived and de-emphasize from active navigation. |
| Training mirror/history docs | `ml/training/sft/exemplars/**`, `ml/training/sft/stage7/*.md`, `ml/training/sft/variants/*.md`, `ml/training/models/*/*.md` | Archive/compatibility retention; governance phase corpus remains constitutional source. |

Execution guardrails:
- Perform moves in small deterministic batches; update `docs/archive/README.md` index each batch.
- Leave stubs/redirect pointers at high-traffic old paths when needed (`deprecate_with_stub` policy).
- Re-run unique-path recount after each move batch to ensure no accidental drops.
