# Phase 7 — Structural Remediation Plan (Revised)

**Repository:** m-coder  
**Audit phase:** Phase 7 only (structural remediation planning, planning-only, read-only)  
**Revision:** Stricter decision standards, single-owner-per-truth, redundancy intolerance, discard/archive classification, naming acceptance test, freshness validation  
**Date:** 2026-03-15  
**Scope:** Convert Phases 0–6 audit findings into a precise, dependency-safe, justified remediation plan. No remediation is applied. No files moved, renamed, edited, or deleted.

**Update (2026-03):** `docs/status_reports/` was **removed** from the repository. Mentions of that path below reflect the layout when this plan was written.

---

## 1. Purpose and scope

This document is the deliverable for **Phase 7** of the m-coder structural audit. It is **planning-only**: it synthesizes Phases 0–6 into an implementation-ready remediation plan with ordered batches, risk levels, preconditions, path-contract protection, and timing. This phase does not move or rename files, edit docs or code, refactor, clean up artifacts, delete, or archive anything. The revised plan enforces stricter decision standards so that future remediation is maximally surgical, justified, redundancy-intolerant, and path-safe.

---

## 2. Executive recommendation

- **Overall remediation strategy:** Proceed in **small, ordered, verifiable batches**. Doc-only clarifications first; then convention and classification; then root hygiene only after path-contract preconditions are met. No broad repo-wide reorganization. Path-contract risk **dominates** cosmetic cleanup—no move or rename without a dedicated plan and full reference checklist.

- **What should be fixed first:** Batch A (canonical docs spine + observation split, doc-only). Then Batches B–D (report convention, naming/legacy clarification, governance clarification, all doc-only). Root hygiene (Batch E) only after .gitignore and reference audit for ledger.db, stage6c_ledger, suite_traces, tail_*.

- **What must not be touched casually:** All paths in the Phase 6 path-contract consolidation register that are referenced by **code** (profiles.py, observation/ingest/validate.py, prepare_exemplars.sh, compile_stage7.py, conf_drift_pipeline, plan_gate_service/tests, etc.). No rename of docs/OBSERVATION, observation/, governance/, ml/, runtime/ without a dedicated migration plan and synchronized updates.

- **Small batches vs large reorg:** **Small batches only.** Clarify truth → classify residue → protect path contracts → only then move/remove/rename. Every action must pass the remediation decision standard (ownership, redundancy, path-contract, clarity, freshness). Redundant material is not preserved by default; it is classified as discard/archive/relocate/clarify-only/leave-as-is.

---

## 3. Remediation decision standard

Every future remediation action must be evaluated against the following. Actions failing one or more tests must be **deferred**, **reclassified**, or **rejected**.

| Test | Criterion |
|------|-----------|
| **Ownership test** | Does this item live in the correct canonical home? If not, is the proposed home the single owner for this truth? |
| **Redundancy test** | Does this duplicate stronger truth elsewhere? If yes, reduce to pointer/supporting/history or classify as discard/archive/relocate. |
| **Path-contract test** | What references break if this changes? Full grep (code, docs, tests, scripts, CI, schemas) must be done before any move/rename. |
| **Clarity test** | Does this change materially reduce ambiguity? If the change is cosmetic or marginal, prefer clarify-only or leave-as-is. |
| **Freshness test** | Will the resulting name/content be current and durable? Terminology must reflect current architecture; status must reflect actual state. |

No action is justified by "cleanup" or "tidiness" alone. Justification must cite one of: canonical truth placement, removal of duplicate structural truth, path-contract-safe relocation, material clarity gain, or required operator/audit context.

---

## 4. Single-owner-per-truth rule

Each important structural truth must have **one canonical owner**. Duplicate ownership must later be reduced to exactly one of:

- **Canonical owner** — The canonical authority for that truth.
- **Pointer** — Explicit pointer to the canonical owner; no restatement of the truth.
- **Supporting context** — Explanation or operator guidance that does not restate structural truth; may reference canonical owner.
- **Historical record** — Archived or milestone doc that is explicitly non-canonical; structural truth moved to spine.
- **Removable residue** — Redundant copy with no justified role; candidate for discard or archive.

Applicable truths include: governance doctrine (CONSTITUTIONAL_MANIFEST); runtime architecture (LAYER3 spec, runtime/README); observation split (observation/ vs runtime/observation/); roadmap/tracker (LIVE_ROADMAP_TRACKER); verification evidence (report placement convention); demo procedure (demo guides). Future remediation must not create or preserve competing owners; restating docs must either point to the canonical owner or be reclassified.

---

## 5. Discard / archive / clarify classification standard

Future remediation must **classify** every file, doc, paragraph, or directory that is redundant or marginal. Do not preserve material merely because it is "possibly useful." Classify as exactly one of:

| Category | When to use | Triggers (examples) |
|----------|-------------|----------------------|
| **Discard candidate** | No enduring value; redundant with stronger source; stale planning residue; generated artifact in wrong home; temporary file with no contract. | plan-*.prompt.md if superseded; duplicate pointer copies; one-off outputs at root with no doc reference. |
| **Archive candidate** | Historical value; no longer canonical; milestone/session artifact. | M4.x milestone docs after structural truth moved to spine; old branch notes; session trackers. |
| **Relocate candidate** | Correct canonical home exists; path-contract can be updated in one batch. | Root prompt files → docs/planning; root artifacts → ml/training/generated or .spool; cuda-pytorch_test → scripts/tests/ml. |
| **Clarify-only** | Role or ownership unclear; no move/rename; add one sentence or label. | Root guide vs MASTER_SYSTEM_SPEC; docs/README vs canonical entry; PHASE_STATUS_REPORT as non-doctrine. |
| **Leave-as-is** | Already correct; no redundancy; no clarity gain from change. | Canonical spine docs; path-contract paths with no justified move. |

This is **planning-only**: the plan requires that later execution classify candidates; it does not perform discard or archive.

---

## 6. Consolidated remediation themes

| Theme | Why it exists | Source phases | Priority | Risk profile |
|-------|----------------|---------------|----------|---------------|
| Canonical docs spine + observation split | Observation split and dual index not in spine; governance restatement drift; canonical entry competition | 1, 2, 4, 5, 6 | High | Low (doc-only) |
| Report / verification convention | docs/reports, docs/status, docs/status_reports, docs/runtime/verification with no stated convention | 1, 6 | Medium | Low (convention doc only) |
| Naming consistency + legacy clarification | OBSERVATION vs observation; plangate vs plan_gate_stub; Stage-7 vs sft/stage7; policies/ vs plangate | 1, 3, 4, 5, 6 | Medium | Low (clarify only); High if rename without plan |
| Governance clarification | PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, AI-Session-Progress-Tracker not labeled as non-doctrine | 2, 6 | Low | Low |
| Root hygiene / artifact-home | Root leakage (ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_*); prompt files; cuda-pytorch_test; OUT convention | 0, 3, 6 | High | Medium (structural; path-check required) |
| Path-contract protection | 45+ path-sensitive clusters; code refs in profiles.py, observation/ingest, prepare_exemplars, conf_drift_pipeline, etc. | 0–6 | Critical | High (any move/rename without plan) |

---

## 7. Recommended remediation sequencing

Order is chosen so that **clarify truth** and **classify residue** come before any **structural change**, and path-contract protection is never relaxed.

1. **Batch A — Canonical docs spine + observation split (doc-only).** Establishes single owner for observation split and governance restatement; clarifies canonical entry. No path moves. Lowest risk.
2. **Batch B — Report / verification convention (doc-only).** Documents where completion vs status vs verification reports live. Classification only; no file moves.
3. **Batch C — Naming and legacy clarification (doc-only).** Documents OBSERVATION vs observation, dual index, plangate vs plan_gate_stub, Stage-7 vs sft/stage7, policies/ vs plangate. No renames.
4. **Batch D — Governance clarification (doc-only).** Labels PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, AI-Session-Progress-Tracker as status/reporting, not doctrine.
5. **Batch E — Root hygiene / artifact-home (structural).** Only after preconditions: .gitignore updated; full grep for ledger.db, stage6c_ledger, suite_traces, tail_*, plan-*.prompt.md references; then relocate or remove root artifacts and prompt files; document OUT convention.
6. **Batch F — Optional / later.** Root guide move to docs (optional); mixed-case docs dir normalization or any path-contract rename **only with dedicated migration plan**.

Dependency: A may precede B–D in any order. E depends on A (so artifact-home convention is documented) and on path-contract checklist for any path that is moved. F has no fixed order; always requires dedicated plan.

---

## 8. Remediation batch definitions

### Batch A — Canonical docs spine + observation split (doc-only)

| Attribute | Value |
|-----------|--------|
| **Goal** | One canonical sentence for observation/ vs runtime/observation/; single-owner labels for governance restatement; canonical entry line; root guide role; runtime/README gaps. |
| **Issues addressed** | Observation split not in spine; dual observation index ambiguity; governance restatement drift; docs/README vs MASTER_SYSTEM_SPEC; runtime/README missing subpackages. |
| **In-scope** | LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER (one sentence); LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS ("source of truth: governance/CONSTITUTIONAL_MANIFEST_v1.0.md"); docs/README.md ("canonical entry: root README → MASTER_SYSTEM_SPEC"); README or MASTER_SYSTEM_SPEC (root guide as long-form guide, not spec entry); runtime/README.md (missing subpackages or pointer to docs). |
| **Out-of-scope** | Moving or renaming any path; rewriting milestone docs; consolidating report dirs. |
| **Type** | Doc-only clarification. |
| **Risk level** | Low. |
| **Dependencies** | None. |
| **Preconditions** | None. Apply sentence-level justification: every added sentence must be canonical truth, required explanation, or operator guidance. |
| **Expected verification** | Readers can infer observation split and canonical entry from spine; no new duplicate structural truth. |
| **Recommended timing** | Now. |

### Batch B — Report / verification convention (doc-only)

| Attribute | Value |
|-----------|--------|
| **Goal** | Document where completion vs status vs verification reports live (MASTER_SYSTEM_SPEC or docs README). |
| **Issues addressed** | Report sprawl across docs/reports, docs/status, docs/status_reports, docs/runtime/verification. |
| **In-scope** | One short convention paragraph: e.g. completion/merge reports → docs/reports; verification audits → docs/runtime/verification; status/session → docs/status or docs/status_reports. No file moves. |
| **Out-of-scope** | Moving or consolidating report files; changing existing placement. |
| **Type** | Convention clarification. |
| **Risk level** | Low. |
| **Dependencies** | None. |
| **Preconditions** | None. |
| **Expected verification** | Convention is findable and unambiguous. |
| **Recommended timing** | Next (after A). |

### Batch C — Naming and legacy clarification (doc-only)

| Attribute | Value |
|-----------|--------|
| **Goal** | Document OBSERVATION vs observation and dual index; one sentence plangate vs plan_gate_stub; Stage-7 vs sft/stage7; policies/ vs plangate. |
| **Issues addressed** | Naming inconsistency; legacy/stub ambiguity. |
| **In-scope** | Clarify-only text in LAYER4_OBSERVATION_SPEC or docs/OBSERVATION/README and observation/README (relationship of two indices); LAYER3_RUNTIME_SPEC or runtime/README (plangate production, plan_gate_stub protocol/test); LAYER2 or stage docs (Stage-7 pipeline vs sft/stage7 CONF drift); policies/ vs plangate (test-only vs production). |
| **Out-of-scope** | Renaming docs/OBSERVATION, observation/, or any path-contract path; normalizing case in links (unless part of a dedicated migration plan). |
| **Type** | Naming clarification; legacy/stub clarification. |
| **Risk level** | Low. |
| **Dependencies** | None. |
| **Preconditions** | Naming acceptance test: no rename in this batch; only clarification. |
| **Expected verification** | No cosmetic renames; clarity improved by documentation only. |
| **Recommended timing** | Next (after A). |

### Batch D — Governance clarification (doc-only)

| Attribute | Value |
|-----------|--------|
| **Goal** | Document PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, AI-Session-Progress-Tracker as status/reporting, not doctrine. |
| **Issues addressed** | Governance dir mix (doctrine vs status). |
| **In-scope** | governance/README or a single sentence in each status doc (or in LAYER1_GOVERNANCE_SPEC) stating these are reporting artifacts, not constitutional doctrine. |
| **Out-of-scope** | Moving or deleting governance files. |
| **Type** | Convention clarification. |
| **Risk level** | Low. |
| **Dependencies** | None. |
| **Preconditions** | None. |
| **Expected verification** | Readers do not treat status docs as doctrine. |
| **Recommended timing** | Next (after A). |

### Batch E — Root hygiene / artifact-home (structural)

| Attribute | Value |
|-----------|--------|
| **Goal** | Add ledger.db and tail_* to .gitignore; relocate or remove root ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt; move plan-*.prompt.md to docs/planning or archive; reclassify or move cuda-pytorch_test.py; document OUT convention. |
| **Issues addressed** | Root artifact leakage; prompt files at root; one-off script; missing artifact-home convention. |
| **In-scope** | .gitignore (ledger.db, tail_stage6c_ledger.txt or pattern); relocate/remove root artifacts (after reference check); plan-*.prompt.md → docs/planning or archive (after checking plan-stage6cPassToStage7Freeze references to OUT/stage6c_ledger); cuda-pytorch_test.py → scripts/tests/ml or reclassify; one sentence or short doc for OUT convention. |
| **Out-of-scope** | Moving path-contract paths (governance/, ml/, runtime/, observation/, docs/ canonical paths); moving root guide without dedicated plan. |
| **Type** | Root hygiene; artifact-home cleanup. |
| **Risk level** | Medium. |
| **Dependencies** | Batch A recommended first (artifact-home convention documented). |
| **Preconditions** | Full grep for ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt, plan-*.prompt.md in code, docs, scripts; update or document any references before move; .gitignore updated before relocate. |
| **Expected verification** | No broken references; CI and verify_artifact_hygiene pass; root no longer holds generated outputs. |
| **Recommended timing** | Later (after A–D and precondition checklist). |

### Batch F — Optional / deferred

| Attribute | Value |
|-----------|--------|
| **Goal** | Optional root guide move; mixed-case docs dir normalization; any path-contract move/rename. |
| **Issues addressed** | Competing root guide; OBSERVATION/COMPILATION/CONTRACTS case. |
| **In-scope** | Only when justified by decision standard and **dedicated migration plan**: motadata-coder-a-complete-guide_v1.7.md move to docs; docs dir renames; any path in Phase 6 path-contract register. |
| **Out-of-scope** | Casual or cosmetic renames; moves without full reference grep and synchronized update. |
| **Type** | Deferred migration. |
| **Risk level** | High. |
| **Dependencies** | Dedicated migration plan; path-contract checklist; full reference grep. |
| **Preconditions** | Ownership test, path-contract test, and naming acceptance test must pass; value must exceed churn. |
| **Expected verification** | All references updated; tests and CI pass. |
| **Recommended timing** | Only with dedicated migration plan; possibly never for layer roots. |

---

## 9. Canonical docs spine clarification plan

- **What to clarify:** (1) Observation split: observation/ = boundary/CLI, runtime/observation/ = runtime-consumed library (one sentence in LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER). (2) Governance restatement: "Source of truth: governance/CONSTITUTIONAL_MANIFEST_v1.0.md" at top of LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS. (3) Canonical entry: "Canonical entry: root README → docs/MASTER_SYSTEM_SPEC" in docs/README.md. (4) Root guide: in README or MASTER_SYSTEM_SPEC, state that motadata-coder-a-complete-guide_v1.7.md is the long-form Golden Exemplars guide and MASTER_SYSTEM_SPEC is the single spec entry. (5) Runtime/README: add missing subpackages (plangate, sandbox, ledger, observation, etc.) or pointer to LAYER3_RUNTIME_SPEC.
- **What remains pointer-only:** docs/governance/AGENT_EXECUTION_RULES → root; docs/OBSERVATION/README and observation/README both remain (relationship clarified, not merged).
- **What not to rewrite broadly:** No wholesale rewrite of MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, or layer specs; only minimal additive sentences. Sentence-level justification: every retained sentence is canonical truth, required explanation, operator guidance, or required historical/audit context; prefer pointering or reduction over repetition.
- **Milestone vs canonical:** Structural truth currently only in M4.x (e.g. runtime/observation/ module list) must be reflected in spine (add one sentence); milestone docs remain as historical record, not moved or deleted in this batch.

---

## 10. Root hygiene / artifact-home cleanup plan

- **Safe candidates (after precondition check):** plan-artifactSegregation.prompt.md, plan-stage6c-ref-sanitizer.prompt.md (move to docs/planning or archive if no code reference); cuda-pytorch_test.py (reclassify or move to scripts/tests/ml). Classify as relocate candidate; path-contract check for plan-stage6cPassToStage7Freeze (references OUT/stage6c_ledger).
- **High-risk candidates:** ledger.db, stage6c_ledger.jsonl, suite_traces.jsonl, tail_stage6c_ledger.txt. Doc/examples reference ledger.db; add to .gitignore first; relocate only after grep and update of any hardcoded root path. Generated artifacts in wrong home → relocate candidate; do not discard if docs reference path without update.
- **Doc-only vs structural:** .gitignore update and OUT convention doc are doc-only/low-structure. Relocating files is structural; requires path-contract checklist.
- **Preconditions:** Grep code, docs, scripts for ledger.db, stage6c_ledger, suite_traces, tail_*, plan-*.prompt.md; list all references; update or document before move.

---

## 11. Report / verification convention plan

- **Classify existing clusters:** Document current placement: docs/reports (merge/readiness/freeze); docs/runtime/verification (audits, completion); docs/status, docs/status_reports (progress, session). No reclassification of files required in plan; only document convention.
- **Consolidate or leave placement:** **Leave placement mostly intact.** Document convention in MASTER_SYSTEM_SPEC or docs/README: e.g. "Completion/merge reports → docs/reports; verification audits → docs/runtime/verification; status/session summaries → docs/status or docs/status_reports." Selective consolidation only if a later explicit decision justifies it and path-contract check is done.
- **Convention documentation only:** No file moves in report-convention batch. Redundancy rule: do not create a new "reports index" that duplicates MASTER_SYSTEM_SPEC; add one short paragraph or bullet list.

---

## 12. Naming consistency clarification plan

- **Clarify only:** Document OBSERVATION vs observation (docs subdir vs root package; two index paths); dual index relationship; plangate vs plan_gate_stub (production vs protocol/stub); Stage-7 (pipeline) vs sft/stage7 (CONF drift); policies/ vs plangate (test-only vs production). No renames in clarification batch.
- **Might later justify normalization:** Link fixes (e.g. MASTER_SYSTEM_SPEC link to observation/README if case is wrong on target system) only as part of dedicated migration plan with naming acceptance test: current name materially misleading, replacement materially improves clarity, blast radius acceptable, all refs updated in one batch, value > churn.
- **Must not rename without migration plan:** docs/OBSERVATION, docs/COMPILATION, docs/CONTRACTS (path-contract and case-sensitive); observation/, governance/, ml/, runtime/; any path in Phase 6 path-contract register. **Naming acceptance test:** No rename unless (1) current name materially misleading, (2) replacement materially improves ownership clarity, (3) contract blast radius acceptable, (4) all references updatable in controlled batch, (5) value exceeds churn. Cosmetic renaming is **prohibited**.

---

## 13. Legacy / stub clarification plan

- **Structures needing explanation only:** policies/ (role: test-only or alternate; vs plangate as production); plan_gate_stub vs plangate (one sentence in LAYER3_RUNTIME_SPEC or runtime/README). Add one sentence each; no removal or rename.
- **Remain untouched:** runtime/plan_gate_stub/, runtime/plangate/, runtime/plan_gate_service/ paths; governance/ and ml/ path-contract paths.
- **Later rationalization:** Only if justified by ownership test and single-owner-per-truth; e.g. deprecating policies/ in favor of plangate only with explicit migration plan and test updates.

---

## 14. Path-contract protection plan

- **Do-not-touch clusters (no move/rename without dedicated plan):** Root AGENT_EXECUTION_RULES.md; governance/ (CONSTITUTIONAL_MANIFEST_v1.0.md, golden-exemplars/, REPOSITORY_CONSTITUTION.md, README.md); docs/NON_NEGOTIABLE_INVARIANTS.md (profiles.py), docs/LAYER1_GOVERNANCE_SPEC.md; docs/MASTER_SYSTEM_SPEC.md, docs/ARCHITECTURE_4_LAYER.md, docs/LIVE_ROADMAP_TRACKER.md; docs/LAYER2–4 specs; docs/OBSERVATION/README.md, observation/README.md, docs/runtime/README.md, docs/COMPILATION/README.md; ml/ (training/, generated/, _build/exemplars, compiler/compile_stage7.py, pipeline/stage6/stage6c/, freeze/, pipeline/stage08/, sft/stage7/); ml/scripts/prepare_exemplars.sh; runtime/schemas/, runtime/ide/schemas/, runtime/state/schemas/, runtime/shadow/schemas/; runtime/plangate/, runtime/sandbox/, runtime/ledger/, runtime/observation/, runtime/plan_gate_stub/, runtime/plan_gate_service/; observation/, observation/ingest/, observation/baseline/, observation/judge_drift_suite/; Makefile, .gitignore, .dvc, .spool.
- **Move/rename preconditions:** Full grep of path in code, docs, tests, scripts, CI, schemas; list all references; update all references in one coordinated change; run tests and CI; run verify_artifact_hygiene where applicable; confirm profiles.py and observation/ingest paths if those areas are touched.
- **Synchronized update categories:** Code (profiles.py, observation/ingest/validate.py, prepare_exemplars.sh, conf_drift_pipeline, plan_gate_service, etc.); docs (MASTER_SYSTEM_SPEC, layer specs, READMEs); tests; scripts; CI; schemas. No partial update—all or none.
- **Verification checklist for any structural change:** Build succeeds; tests pass; verify_artifact_hygiene passes if artifact paths change; profiles.py and observation/ingest path load if governance or runtime schema paths change. Path-contract risk **dominates** cosmetic cleanup; no move/rename for tidiness alone.

---

## 15. Recommended timing matrix

| Theme / batch | Timing | Reason | Risk | Notes |
|---------------|--------|--------|------|-------|
| Batch A — Spine + observation split | Now | Doc-only; establishes single owner for split and restatement | Low | First batch |
| Batch B — Report convention | Next | Doc-only; no path moves | Low | After A |
| Batch C — Naming/legacy clarification | Next | Doc-only; no renames | Low | After A |
| Batch D — Governance clarification | Next | Doc-only | Low | After A |
| Batch E — Root hygiene | Later | Structural; requires precondition checklist | Medium | After A–D; path-check required |
| Batch F — Optional/migration | Only with dedicated plan | Path-contract and naming acceptance test | High | Possibly never for layer roots |
| Path-contract move/rename | Only with dedicated migration plan | Code refs; blast radius | Critical | Use Phase 6 §7 register as checklist |
| Mixed-case docs dir rename | Only with dedicated migration plan | Case-sensitive; link updates | High | Cosmetic unless justified |
| Broad reorg | Possibly never | Not justified by current audit | Critical | Not recommended |

---

## 16. Deferred or “possibly never” items

- **Do not fix now:** Mixed-case docs dir renames; consolidation of report dirs (moving files); root guide move (optional, only with plan); any path-contract move/rename.
- **Only if concrete value:** Normalizing OBSERVATION/observation link case (only if link breakage confirmed and value > churn); moving governance status files to docs/ (only if single-owner-per-truth demands it and path-check done).
- **Possibly never:** Moving governance/, ml/, runtime/, observation/ roots; moving AGENT_EXECUTION_RULES from root; broad repo-wide reorganization; cosmetic renames that fail naming acceptance test.

---

## 17. Immediate conclusions

- **Safest first remediation batch:** Batch A (canonical docs spine + observation split, doc-only). No path moves; establishes single owner for observation split and governance restatement; applies sentence-level justification.
- **Most dangerous structural changes:** Any move/rename of paths in the Phase 6 path-contract register, especially those referenced by code (profiles.py, observation/ingest/validate.py, prepare_exemplars.sh, compile_stage7.py, conf_drift_pipeline, plan_gate_service/tests). Root hygiene moves without checking references to ledger.db, stage6c_ledger, suite_traces, tail_*. Renaming docs/OBSERVATION or observation/ or governance/ without full-link and code audit.
- **What must be clarified before any path changes:** Full reference list (grep) for any path to be moved or renamed; classification of item as relocate candidate with correct canonical home; path-contract checklist completed; naming acceptance test passed if rename.
- **Next execution phase:** Execute Batch A only (doc-only). Then reassess; then Batches B–D; then Batch E only after preconditions. Do not execute Batch F without a dedicated migration plan.

---

## 18. Non-goals

This phase did **not**:

- Execute any remediation batch.
- Move, rename, edit, or delete any file.
- Refactor code or docs.
- Clean up the repo, archive, or discard anything.
- Weaken path-contract safeguards or expand scope beyond Phases 0–6 findings.

---

## Phase 7 result summary

### 1. Artifact created
- **path:** docs/audit/STRUCTURAL_REMEDIATION_PLAN.md

### 2. Recommended first remediation batches
- **batch 1:** Canonical docs spine + observation split (doc-only)
- **batch 2:** Report convention (doc-only)
- **batch 3:** Naming and legacy clarification (doc-only)

### 3. Highest-risk changes
- **risk 1:** Moving/renaming any path in Phase 6 path-contract register (code refs in profiles.py, observation/ingest, prepare_exemplars, conf_drift_pipeline, etc.)
- **risk 2:** Root hygiene moves without checking doc/script references to ledger.db, stage6c_ledger, suite_traces
- **risk 3:** Renaming docs/OBSERVATION or observation/ or governance/ without full-link and code audit

### 4. Path-contract protection result
- **do-not-touch clusters:** Governance (manifest, golden-exemplars, NON_NEGOTIABLE path in profiles.py); ml/training (generated, _build/exemplars, compiler, pipeline/stage6/stage6c); runtime (schemas, plangate, sandbox, ledger, observation); observation/ and observation/ingest; root AGENT_EXECUTION_RULES; docs MASTER_SYSTEM_SPEC/ARCHITECTURE_4_LAYER/LIVE_ROADMAP_TRACKER.
- **key preconditions:** Full reference grep; synchronized updates; run tests and CI.
- **conclusion:** No move/rename of path-contract items without dedicated plan and checklist.

### 5. Naming/report/root plan result
- **naming:** Clarify only in docs; no renames without migration plan and naming acceptance test.
- **report:** Convention documentation only; leave placement as-is.
- **root:** .gitignore first; then relocate artifacts and prompt files with reference check.
- **conclusion:** Doc-only batches first; root hygiene after preconditions.

### 6. Timing result
- **now:** Batch A (spine + observation split).
- **next:** Batches B, C, D (convention and naming doc-only).
- **later:** Batch E (root hygiene with precondition check).
- **only with dedicated migration plan:** Any path-contract move/rename; mixed-case dir normalization.
- **possibly never:** Broad reorg; moving governance/ or layer roots.

### 7. Final status
**PHASE 7 REMEDIATION PLAN READY**

---

## Phase 7 revision result summary

### 1. Artifact revised
- **path:** docs/audit/STRUCTURAL_REMEDIATION_PLAN.md

### 2. Strongest new planning rules added
- **rule 1:** Remediation decision standard — every action evaluated against ownership, redundancy, path-contract, clarity, freshness tests; actions failing tests deferred/reclassified/rejected.
- **rule 2:** Single-owner-per-truth — each structural truth has one canonical owner; duplicates reduced to canonical/pointer/supporting/history/removable residue.
- **rule 3:** Redundancy intolerance + discard/archive classification — do not preserve redundant material by default; classify as discard candidate, archive candidate, relocate candidate, clarify-only, or leave-as-is.
- **rule 4:** Naming acceptance test + freshness validation — no rename without materially misleading name, material clarity gain, acceptable blast radius, batch update, value > churn; doc batches validate terminology, status, paths, case, canonical vs pointer.

### 3. Decision-standard result
- **added tests:** Ownership test; Redundancy test; Path-contract test; Clarity test; Freshness test.
- **conclusion:** Actions failing one or more tests must be deferred, reclassified, or rejected; no action justified by cleanup or tidiness alone.

### 4. Redundancy / discard-classification result
- **classification categories added:** Discard candidate; Archive candidate; Relocate candidate; Clarify-only; Leave-as-is.
- **conclusion:** Redundant prose, docs, files, and directories are not preserved by default; later remediation must classify and reduce duplicate ownership.

### 5. Naming / freshness result
- **naming:** No rename proposed later unless current name materially misleading, replacement materially improves ownership clarity, contract blast radius acceptable, all references updatable in one controlled batch, value exceeds churn; cosmetic renaming prohibited.
- **freshness:** Every doc/naming clarification batch must validate terminology reflects current architecture, status reflects actual state, old branch/integration wording removed or marked history, examples and paths exist, case-sensitive refs exact, canonical vs pointer status current.
- **conclusion:** Naming and freshness rules make remediation surgical and avoid churn.

### 6. Sequencing / safety result
- **sequencing rule:** (1) Clarify truth, (2) classify residue, (3) protect path contracts, (4) only then move/remove/rename.
- **path-contract stance:** Path-contract risk dominates cosmetic cleanup; no move/rename without dedicated plan and full reference checklist.
- **conclusion:** Small-batch discipline preserved; path-contract protection unchanged.

### 7. Final status
**PHASE 7 PLAN REVISION READY**
