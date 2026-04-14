# Phase 1 — Canonical Docs / Spec Placement Audit Report

**Repository:** m-coder  
**Audit phase:** Phase 1 only (canonical docs/spec placement audit, read-only)  
**Date:** 2026-03-15  
**Scope:** Documentation and spec placement across root, docs/, and layer boundaries. No moves, renames, link fixes, or remediation performed.

**Update (2026-03):** `docs/status_reports/` was **removed** from the repository. Mentions of that path in this report describe layout at audit time.

---

## 1. Purpose and scope

This document is the deliverable for **Phase 1** of the m-coder structural audit. It is a **read-only structural audit** of **canonical documentation and spec placement** only. It does not move or rename files, merge duplicates, rewrite docs, fix links, archive files, or perform any remediation. The audit inventories and classifies document clusters, identifies the canonical documentation spine, detects competition and ambiguity between canonical and explanatory/temporary docs, and explicitly assesses the documentation of the observation/ vs runtime/observation/ split.

---

## 2. Executive assessment

- **Overall docs/spec placement health:** Moderate. The repo has a **defined canonical spine**: README → MASTER_SYSTEM_SPEC → ARCHITECTURE_4_LAYER, LIVE_ROADMAP_TRACKER, layer indices (governance/README, COMPILATION/README, runtime/README, OBSERVATION/README), and layer specs (LAYER1–LAYER4, RUNTIME_PLAN_AND_LEDGER, etc.). That spine is referenced consistently from root README and verification docs. However, **competing or ambiguous elements** weaken single-source clarity: (1) two observation index locations (docs/OBSERVATION/README.md vs root observation/README.md) with case/naming inconsistency; (2) no canonical document that explains the observation/ vs runtime/observation/ split; (3) report/status docs spread across docs/reports, docs/status, docs/status_reports, and docs/runtime/verification; (4) docs/README.md reads like a broad “system index” and may be mistaken for the canonical entry; (5) mixed-case docs subdirs (OBSERVATION, COMPILATION, CONTRACTS) vs lowercase (governance, runtime) create path/link inconsistency.

- **Does the repo have a clear canonical documentation spine?** Partially. The **intended** spine (README → MASTER_SYSTEM_SPEC → layer specs and indices) is clear and is the one used by verification audits and LIVE_ROADMAP_TRACKER. Competing or parallel entrypoints (docs/README.md, root motadata-coder-a-complete-guide, multiple report clusters) and the missing canonical explanation of the observation split reduce clarity.

- **Biggest doc placement risks:** (1) **Observation split not canonically documented** — readers cannot infer from the doc spine that observation/ is the Layer-4 boundary/CLI surface and runtime/observation/ is the runtime-consumed library. (2) **Dual observation index paths** — MASTER_SYSTEM_SPEC and MIGRATION_NOTE point to OBSERVATION/README.md (docs subdir); root README points to observation/README.md (root package). On case-sensitive systems these are different paths; the relationship is implicit. (3) **Report sprawl** — completion/verification/status docs live in docs/reports, docs/status, docs/status_reports, and docs/runtime/verification with no single convention for “where completion reports live.” (4) **docs/README.md** — content is a broad system/training index and may be mistaken for the canonical doc entry; only one line references MASTER_SYSTEM_SPEC as canonical.

---

## 3. Canonical documentation spine

For each chain we state: canonical current path(s); whether it is obvious; whether it competes with another doc; confidence (`clear`, `partially clear`, `unclear`).

| Chain | Canonical current path(s) | Obvious? | Competes? | Confidence |
|-------|----------------------------|----------|------------|------------|
| **Architecture** | README.md → docs/MASTER_SYSTEM_SPEC.md → docs/ARCHITECTURE_4_LAYER.md | Yes — README “Canonical spec entry point” and “4-layer architecture” | Slightly: root motadata-coder-a-complete-guide_v1.7.md referenced as “Golden Exemplars guide”; docs/README.md as “Documentation Index” | **clear** |
| **Roadmap / tracker** | docs/LIVE_ROADMAP_TRACKER.md | Yes — README “Live execution tracker,” “canonical live status authority”; verification docs cite it | docs/ROADMAP_L2_L3_L4.md, docs/SYSTEM_EXECUTION_ROADMAP.md are supporting; no conflict | **clear** |
| **Governance** | Root AGENT_EXECUTION_RULES.md (canonical); governance/CONSTITUTIONAL_MANIFEST_v1.0.md; docs/governance/README.md (pointer to root rules) | Yes — docs/governance/README states root is canonical; MASTER_SYSTEM_SPEC links governance/README | No | **clear** |
| **Runtime** | docs/LAYER3_RUNTIME_SPEC.md; docs/runtime/README.md (layer index); docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md; runtime/ (code) | Yes — README and MASTER_SYSTEM_SPEC point to LAYER3_RUNTIME_SPEC and runtime/README | No | **clear** |
| **Observation** | docs/LAYER4_OBSERVATION_SPEC.md; MASTER_SYSTEM_SPEC links to docs/OBSERVATION/README.md (Layer-4 index); root observation/README.md (layer package) | Partially — root README links to observation/README.md; MASTER_SYSTEM_SPEC links to OBSERVATION/README.md (docs subdir). Two index locations; case OBSERVATION vs observation. Split with runtime/observation/ not explained in spine | Yes — dual index paths; split unexplained | **partially clear** |
| **Demo / operator** | docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md; docs/runtime/JETBRAINS_PLUGIN_MVP_SPIKE.md; docs/guides/E2E-flow.md (non-canonical banner) | Partially — demo guide is under docs/runtime/; E2E-flow is explicitly non-canonical | E2E-flow is long and narrative; could be mistaken for canonical | **partially clear** |

---

## 4. Documentation inventory by role

Structured inventory of major doc clusters. Classification: canonical, canonical pointer, explanatory, milestone-specific, verification/reporting, demo/operator, temporary/planning, archival, unclear. Canonical status: canonical, pointer, non-canonical, unclear. Placement quality: good, questionable, poor.

| Path | Role / topic | Classification | Canonical status | Placement quality | Notes |
|------|----------------|----------------|------------------|-------------------|-------|
| README.md (root) | Repo entry; layer status; links to MASTER_SYSTEM_SPEC | canonical | canonical | good | Single root entry; points to docs/MASTER_SYSTEM_SPEC, observation/README.md |
| docs/MASTER_SYSTEM_SPEC.md | Single spec entry; TOC; doctrine immutability | canonical | canonical | good | Links to OBSERVATION/README.md (docs subdir), not observation/README |
| docs/ARCHITECTURE_4_LAYER.md | 4-layer directory mapping, allowed/forbidden | canonical | canonical | good | References MASTER_SYSTEM_SPEC |
| docs/LIVE_ROADMAP_TRACKER.md | Live milestone status and evidence | canonical | canonical | good | Referenced as canonical live status authority |
| docs/ROADMAP_L2_L3_L4.md | L2/L3/L4 milestone conditions | explanatory / supporting | non-canonical | good | Linked from MASTER_SYSTEM_SPEC |
| docs/SYSTEM_EXECUTION_ROADMAP.md | End-to-end roadmap, artifact matrix | explanatory / supporting | non-canonical | good | |
| docs/README.md | Broad documentation index (training, RAG, dir structure) | explanatory | non-canonical | questionable | Reads like system index; one line cites MASTER_SYSTEM_SPEC; can be mistaken for canonical entry |
| docs/MIGRATION_NOTE.md | Doc refactor migration; what moved where | temporary / historical | non-canonical | good | Links OBSERVATION/README.md |
| docs/PHASE_ALIGNMENT_TABLE_V0_1.md | Phase vs stage vs runtime vs observation | canonical | canonical | good | |
| docs/NON_NEGOTIABLE_INVARIANTS.md | Fail-closed semantics | canonical | canonical | good | |
| docs/GLOSSARY.md | CIM terms, schema refs | canonical | canonical | good | |
| docs/CONTRACTS/README.md | Schema and contract index | canonical | canonical | good | |
| docs/governance/README.md | Layer-1 index; pointer to root AGENT_EXECUTION_RULES | canonical pointer | pointer | good | Explicit “root is canonical” |
| docs/governance/AGENT_EXECUTION_RULES.md | Pointer to root AGENT_EXECUTION_RULES | canonical pointer | pointer | good | |
| docs/COMPILATION/README.md | Layer-2 index | canonical | canonical | good | Uppercase dir |
| docs/runtime/README.md | Layer-3 index; specs, schemas, stub, service | canonical | canonical | good | Does not mention runtime/observation/ |
| docs/OBSERVATION/README.md | Layer-4 index (docs subdir); links to observation/ingest, observation/baseline | canonical | canonical | questionable | Uppercase; dual with root observation/README.md; does not explain runtime/observation/ |
| observation/README.md | Layer-4 package README (ingest, baseline, drift) | canonical | canonical | good | Root package; does not mention runtime/observation/ |
| docs/LAYER4_OBSERVATION_SPEC.md | Layer-4 comprehensive spec | canonical | canonical | good | “Directory: observation/”; no runtime/observation/ split |
| docs/LAYER3_RUNTIME_SPEC.md | Layer-3 comprehensive spec | canonical | canonical | good | |
| docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md | Plan/ledger v0.1 | canonical | canonical | good | |
| docs/JETBRAINS_PLUGIN_FLOW_V0_1.md | IDE contracts | canonical | canonical | good | |
| docs/SHADOW_MODE_PROTOCOL_V0_1.md | Shadow rules | canonical | canonical | good | Links observation/ingest, observation/baseline (lowercase) |
| docs/runtime/RUNTIME_AGENT_ARCHITECTURE.md | Runtime-governed agent loop | canonical | canonical | good | |
| docs/runtime/RUNTIME_STATE_TRANSITIONS.md | State machine | canonical | canonical | good | |
| docs/runtime/milestones/*.md | M3.x, M4.x implementation notes | milestone-specific | non-canonical | good | M4.x docs reference runtime/observation/ as implementation location |
| docs/runtime/branch_execution_notes/*.md | Branch-level execution notes | milestone-specific | non-canonical | good | |
| docs/runtime/verification/*.md | Audits, constitutional reference, completion | verification/reporting | non-canonical | good | Reference canonical spine |
| docs/reports/*.md | M4X merge, readiness, verification, freeze | verification/reporting | non-canonical | good | Concentrated in docs/reports |
| docs/status/*.md, docs/status_reports/*.md | Progress, session summaries, findings | verification/reporting | non-canonical | questionable | Multiple report clusters; no single convention |
| docs/guides/E2E-flow.md | Narrative E2E walkthrough | explanatory / demo | non-canonical | good | Explicit non-canonical banner; links docs/OBSERVATION/ |
| docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md | Demo runbook | demo/operator | non-canonical | good | |
| docs/reference/NAMING_CONVENTIONS.md | Naming conventions; legacy uppercase docs dirs | explanatory | non-canonical | good | Documents docs/COMPILATION, CONTRACTS, OBSERVATION |
| motadata-coder-a-complete-guide_v1.7.md (root) | Golden Exemplars long-form guide | explanatory | non-canonical | questionable | Competes as “guide”; referenced by README and ARCHITECTURE_4_LAYER |

---

## 5. Documentation placement findings

Each finding uses: Finding; Why it is a problem; Severity; Recommended action; Action timing.

**Finding 1 — Observation split not canonically explained**  
- **Why it is a problem:** The repo has two observation-related trees: top-level observation/ (CLIs: ingest, baseline, judge_drift_suite) and runtime/observation/ (Python library implementing M4.1–M4.6). No canonical doc in the spine (MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, LAYER4_OBSERVATION_SPEC, observation/README, docs/OBSERVATION/README, docs/runtime/README) states this split. The split appears only in milestone (M4.x) and verification docs. New contributors or auditors cannot infer from the doc spine that Layer-4 has a “boundary/CLI” surface vs “runtime library” implementation.  
- **Severity:** High (architectural ambiguity; blurs layer boundary).  
- **Recommended action:** Add a short canonical subsection (e.g. in LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER or a dedicated “Layer-4 structure” note) stating: observation/ is the Layer-4 boundary (CLIs, drift suite); runtime/observation/ is the runtime-consumed library implementing M4.1–M4.6; both are Layer-4 responsibility but different placement for coupling reasons.  
- **Action timing:** `later` (remediation phase; no edit in this audit).

**Finding 2 — Dual observation index paths and case inconsistency**  
- **Why it is a problem:** MASTER_SYSTEM_SPEC and MIGRATION_NOTE link to [OBSERVATION/README.md], i.e. docs/OBSERVATION/README.md (uppercase docs subdir). Root README links to observation/README.md (root package). So there are two “Layer-4 index” docs: docs/OBSERVATION/README.md (shorter, points to observation/ingest, observation/baseline) and observation/README.md (layer package README). On case-sensitive systems the paths differ; naming is inconsistent (OBSERVATION vs observation). Verification docs note “root observation/ distinct from docs/OBSERVATION (different role)” but the spine does not state which is the authoritative Layer-4 entry for “where do I start for Layer-4.”  
- **Severity:** Medium (naming/link inconsistency; dual index).  
- **Recommended action:** Either (a) make docs/OBSERVATION/README.md a clear pointer to observation/README.md and state “canonical Layer-4 package README: observation/README.md,” or (b) consolidate to a single canonical location and fix links. Do not change in this phase.  
- **Action timing:** `later`.

**Finding 3 — Report sprawl across multiple conventions**  
- **Why it is a problem:** Completion/verification/status docs live in docs/reports (M4X, etc.), docs/status (progress, session summaries), docs/status_reports (V16, findings, planning), and docs/runtime/verification (audits, completion reports). There is no single stated convention for “where completion or verification reports live,” so future reports may be added in any of these places and the spine does not point to one “reports home.”  
- **Severity:** Medium (organizational sprawl; not a single-source conflict).  
- **Recommended action:** Document in a canonical place (e.g. docs/README or MASTER_SYSTEM_SPEC supporting section) where completion reports vs status reports vs verification audits live. Optionally consolidate in a later phase.  
- **Action timing:** `later`.

**Finding 4 — docs/README.md can be mistaken for canonical entry**  
- **Why it is a problem:** docs/README.md is titled “Motadata AI System - Documentation Index” and describes a broad directory structure (venv, training, RAG, evaluation, etc.). It has one line referencing MASTER_SYSTEM_SPEC as canonical. Readers opening docs/ first may treat docs/README.md as the doc entrypoint instead of root README → MASTER_SYSTEM_SPEC.  
- **Severity:** Low (competing entrypoint risk; not a conflict of content).  
- **Recommended action:** Add a prominent “Canonical entry: see root README.md and docs/MASTER_SYSTEM_SPEC.md” at the top of docs/README.md in a later phase; or clarify that docs/README is an index, not the spec spine entry.  
- **Action timing:** `later`.

**Finding 5 — Root guide competes with canonical entry flow**  
- **Why it is a problem:** Root motadata-coder-a-complete-guide_v1.7.md is referenced by README as “Golden Exemplars guide” and by ARCHITECTURE_4_LAYER. It functions as a secondary entrypoint. Phase 0 already flagged this. From a docs-placement perspective, it is not part of the canonical spec spine but is linked from it, which can dilute “start at README → MASTER_SYSTEM_SPEC.”  
- **Severity:** Low (already identified in Phase 0).  
- **Recommended action:** Clarify in MASTER_SYSTEM_SPEC or README that the guide is long-form reference and MASTER_SYSTEM_SPEC remains the single canonical spec entry.  
- **Action timing:** `later`.

**Finding 6 — Mixed-case docs subdirs (OBSERVATION, COMPILATION, CONTRACTS)**  
- **Why it is a problem:** docs/ uses uppercase for OBSERVATION, COMPILATION, CONTRACTS and lowercase for governance, runtime. NAMING_CONVENTIONS.md treats uppercase as legacy and says “do not add new UPPERCASE docs subdirs.” Links from MASTER_SYSTEM_SPEC and E2E-flow use OBSERVATION, COMPILATION, CONTRACTS. Inconsistency can cause broken links on case-sensitive systems if someone assumes lowercase.  
- **Severity:** Low (documented legacy; links currently resolve).  
- **Recommended action:** No change in this phase. Future remediation could normalize to lowercase and update links with a dedicated plan.  
- **Action timing:** `never touch without dedicated plan` (legacy; link update has path-contract risk).

---

## 6. Observation split clarification test

This section answers the required audit target.

**1. Is the observation/ vs runtime/observation/ split explicitly and clearly documented anywhere canonical?**  
**No.** No document in the canonical spine (README, MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, LAYER4_OBSERVATION_SPEC, observation/README.md, docs/OBSERVATION/README.md, docs/runtime/README.md) states that:
- observation/ is the Layer-4 boundary / CLI / tooling surface, and  
- runtime/observation/ is a runtime-consumed library implementation.

**2. Does the repo documentation make it obvious that observation/ is the Layer-4 boundary and runtime/observation/ is the runtime-consumed library?**  
**No.** observation/README.md and docs/OBSERVATION/README.md describe ingest, baseline, drift, GREG evidence, and point to observation/ingest and observation/baseline. They do not mention runtime/observation/. docs/runtime/README.md lists “runtime/” contents (plan-gate, IDE, shadow, schemas) and does not list runtime/observation/. The only docs that describe runtime/observation/ as the implementation location are docs/runtime/milestones/M4_1 through M4_6 and branch_execution_notes/feature-m4.1-observability-closure.md — all milestone-specific, not canonical spine.

**3. Is that explanation canonical, repeated inconsistently, or missing?**  
**Missing** from canonical docs. It is **repeated consistently** only in milestone/implementation docs (M4.x), which are not the canonical architecture entrypoints.

**4. Does the docs tree create ambiguity about whether observation is a separate layer or a runtime submodule?**  
**Yes.** A reader following only the spine (MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, LAYER4_OBSERVATION_SPEC, observation/README) sees Layer-4 as “observation/” (ingest, baseline, drift). They do not see that a large part of Layer-4 capability (trace building, baseline store, collapse, reconciliation, GREG bundle, runtime metrics) lives under runtime/observation/ and is consumed by the runtime. The docs tree does not state that both are Layer-4 with different placement, so it is ambiguous whether “observation” is only the top-level package or also includes runtime/observation/.

**5. Is this a docs-placement issue only, or evidence of deeper structural ambiguity?**  
**Primarily a docs-placement issue.** The code layout (observation/ vs runtime/observation/) is consistent with “Layer-4 boundary vs runtime library.” The missing piece is a **canonical sentence or subsection** that records this in the spec spine. If such a sentence is added, the structural ambiguity for readers is resolved. Deeper structural ambiguity (e.g. whether runtime/observation/ should eventually move to an observation package) is out of scope for this phase; this audit only concludes that the current split is **not** clearly documented in canonical docs.

**Key evidence:**  
- observation/README.md: no mention of runtime/observation/.  
- docs/OBSERVATION/README.md: no mention of runtime/observation/.  
- docs/runtime/README.md: no mention of runtime/observation/.  
- LAYER4_OBSERVATION_SPEC.md: “Directory: observation/”; lists ingest, baseline, drift; no runtime/observation/.  
- ARCHITECTURE_4_LAYER.md: “Layer-4: observation/”; allowed/forbidden; no runtime/observation/.  
- M4_1_OBSERVABILITY_CLOSURE.md through M4_6_RUNTIME_METRICS.md: list runtime/observation/ modules; milestone-specific.

**Conclusion:** The observation split is **not** canonically explained. Adding a short canonical clarification (in LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER or observation/README) would resolve the docs-placement ambiguity. This is a **docs-placement gap**, not necessarily a code-structure error.

---

## 7. Path Contract Register for docs

| Path | Why path-sensitive | Referenced by | Risk if moved/renamed | Recommendation note |
|------|---------------------|---------------|----------------------|---------------------|
| docs/MASTER_SYSTEM_SPEC.md | Canonical spec entry | README, verification docs, E2E-flow, ARCHITECTURE_4_LAYER | High | Do not move; link target for many docs |
| docs/ARCHITECTURE_4_LAYER.md | Layer mapping authority | MASTER_SYSTEM_SPEC, README, verification | High | Do not move |
| docs/LIVE_ROADMAP_TRACKER.md | Canonical authority for milestones | README, verification, reports | High | Do not move |
| docs/LAYER4_OBSERVATION_SPEC.md | Layer-4 spec | MASTER_SYSTEM_SPEC | High | Do not move |
| docs/LAYER3_RUNTIME_SPEC.md | Layer-3 spec | MASTER_SYSTEM_SPEC, README | High | Do not move |
| docs/OBSERVATION/README.md | Layer-4 index in docs | MASTER_SYSTEM_SPEC, MIGRATION_NOTE, E2E-flow | Medium | Case-sensitive; link from MASTER_SYSTEM_SPEC; clarify vs observation/README |
| observation/README.md | Layer-4 package README | README (root), SHADOW_MODE_PROTOCOL, plan_gate_stub | Medium | Do not move; root layer entry |
| docs/runtime/README.md | Layer-3 index | MASTER_SYSTEM_SPEC, runtime docs | High | Do not move |
| docs/CONTRACTS/README.md | Schema index | MASTER_SYSTEM_SPEC | Medium | Do not move |
| docs/COMPILATION/README.md | Layer-2 index | MASTER_SYSTEM_SPEC, MIGRATION_NOTE | Medium | Uppercase dir; do not rename without plan |
| docs/governance/README.md | Layer-1 index; pointer to root rules | MASTER_SYSTEM_SPEC | Medium | Do not move |
| docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md | Plan/ledger spec | MASTER_SYSTEM_SPEC, runtime README | High | Do not move |
| docs/JETBRAINS_PLUGIN_FLOW_V0_1.md | IDE contracts | MASTER_SYSTEM_SPEC, runtime README | High | Do not move |
| docs/SHADOW_MODE_PROTOCOL_V0_1.md | Shadow protocol | MASTER_SYSTEM_SPEC, runtime README | High | Do not move |
| docs/PHASE_ALIGNMENT_TABLE_V0_1.md | Phase alignment | MASTER_SYSTEM_SPEC | Medium | Do not move |
| docs/NON_NEGOTIABLE_INVARIANTS.md | Invariants | MASTER_SYSTEM_SPEC | Medium | Do not move |
| docs/GLOSSARY.md | Glossary | MASTER_SYSTEM_SPEC | Low | Do not move |
| README.md (root) | Repo entry | All users, docs | High | Do not move |

---

## 8. Preliminary canonical / pointer / archive / clarify classification

| Item / cluster | Preliminary classification | Rationale |
|----------------|----------------------------|-----------|
| Root README, docs/MASTER_SYSTEM_SPEC, docs/ARCHITECTURE_4_LAYER, docs/LIVE_ROADMAP_TRACKER | canonical | Defined spine; do not move |
| docs/LAYER*_*_SPEC, RUNTIME_PLAN_AND_LEDGER, JETBRAINS_PLUGIN_FLOW, SHADOW_MODE_PROTOCOL | canonical | Linked from MASTER_SYSTEM_SPEC |
| docs/governance/README, docs/governance/AGENT_EXECUTION_RULES | canonical pointer | Point to root governance and root AGENT_EXECUTION_RULES |
| docs/COMPILATION/README, docs/CONTRACTS/README, docs/OBSERVATION/README | canonical (index) | Layer/schema indices; OBSERVATION vs observation clarify later |
| observation/README.md | canonical | Layer-4 package README |
| docs/runtime/README.md | canonical | Layer-3 index |
| docs/runtime/milestones/*, branch_execution_notes/* | milestone-specific | Do not treat as canonical; reference only |
| docs/runtime/verification/* | verification/reporting | Do not treat as canonical |
| docs/reports/*, docs/status/*, docs/status_reports/* | verification/reporting | Report sprawl; clarify convention later |
| docs/guides/E2E-flow.md | explanatory | Explicit non-canonical banner |
| docs/README.md | clarify only | Add canonical-entry pointer; do not treat as spine entry |
| docs/MIGRATION_NOTE.md | temporary / historical | Keep for reference; not spine |
| Root motadata-coder-a-complete-guide_v1.7.md | clarify only | Document as long-form guide; MASTER_SYSTEM_SPEC remains spec entry |
| docs/OBSERVATION vs observation/ | clarify only | Add canonical sentence on split; fix link case later |

---

## 9. Immediate conclusions

- **Does the docs tree have one clear spine or multiple competing spines?** **One intended spine** (README → MASTER_SYSTEM_SPEC → ARCHITECTURE_4_LAYER, LIVE_ROADMAP_TRACKER, layer indices and specs) that is referenced by verification and README. **Competing or parallel entrypoints** exist: docs/README.md (broad index), root Golden Exemplars guide, and dual observation index paths. So: one primary spine with competing entrypoints, not multiple equal spines.

- **What are the biggest canonical-placement risks?** (1) Observation split not documented in the spine — readers cannot tell that runtime/observation/ is Layer-4 implementation. (2) Dual observation index (docs/OBSERVATION/README vs observation/README) and case inconsistency. (3) Report sprawl (reports, status, status_reports, runtime/verification) with no single stated convention.

- **Which docs are dangerous to touch?** MASTER_SYSTEM_SPEC, ARCHITECTURE_4_LAYER, LIVE_ROADMAP_TRACKER, LAYER3/LAYER4 specs, RUNTIME_PLAN_AND_LEDGER, JETBRAINS_PLUGIN_FLOW, SHADOW_MODE_PROTOCOL, root README, docs/runtime/README, docs/governance/README — all are path-contract sensitive and linked from multiple places. Renaming or moving without a dedicated plan would break the spine.

- **Which docs most likely need clarification later?** (1) LAYER4_OBSERVATION_SPEC or ARCHITECTURE_4_LAYER or observation/README — add canonical sentence on observation/ vs runtime/observation/. (2) docs/README.md — add prominent “canonical entry: root README → MASTER_SYSTEM_SPEC.” (3) Report locations — document where completion vs status vs verification reports live.

- **What should the next audit phase be?** Per the approved plan, **Phase 2 — Layer-1 governance audit** (governance directory layout, constitutional docs, doctrine, invariants, golden exemplars, and whether lower-layer docs are incorrectly mixed into governance).

---

## 10. Non-goals

This phase did **not**:

- Move, rename, merge, or delete any document.
- Fix links (including OBSERVATION vs observation).
- Rewrite or edit canonical docs.
- Archive files or consolidate report directories.
- Change code or imports.
- Perform remediation; only inventory, classification, and recommendation.
- Resolve the observation split structurally (only assessed whether it is documented).

---

## Phase 1 result summary

### 1. Artifact created
- **path:** `docs/audit/CANONICAL_DOCS_PLACEMENT_AUDIT.md`

### 2. Canonical spine assessment
- **architecture:** clear — README → MASTER_SYSTEM_SPEC → ARCHITECTURE_4_LAYER (slight competition from root guide and docs/README).
- **roadmap/tracker:** clear — docs/LIVE_ROADMAP_TRACKER.md.
- **governance:** clear — root AGENT_EXECUTION_RULES, governance/, docs/governance/README (pointer).
- **runtime:** clear — docs/LAYER3_RUNTIME_SPEC, docs/runtime/README, runtime/.
- **observation:** partially clear — LAYER4_OBSERVATION_SPEC, docs/OBSERVATION/README, observation/README; dual index and case; split with runtime/observation/ not in spine.
- **demo/operator:** partially clear — docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE; E2E-flow non-canonical.

### 3. Major findings
- **finding 1:** Observation split (observation/ vs runtime/observation/) is not documented in any canonical spine doc; only in M4.x milestone docs.
- **finding 2:** Dual observation index paths (docs/OBSERVATION/README.md vs observation/README.md) and OBSERVATION vs observation case inconsistency.
- **finding 3:** Report sprawl across docs/reports, docs/status, docs/status_reports, docs/runtime/verification with no single stated convention.

### 4. Observation split clarification result
- **status:** Not canonically explained.
- **key evidence:** observation/README, docs/OBSERVATION/README, docs/runtime/README, LAYER4_OBSERVATION_SPEC, ARCHITECTURE_4_LAYER none mention runtime/observation/; only M4.x milestones and branch notes do.
- **conclusion:** Docs-placement gap; adding a short canonical subsection would resolve reader ambiguity; no evidence of code-structure error.

### 5. Path-sensitive docs identified
- **number:** 18 (paths in Path Contract Register).
- **notable examples:** docs/MASTER_SYSTEM_SPEC.md, docs/ARCHITECTURE_4_LAYER.md, docs/LIVE_ROADMAP_TRACKER.md, docs/LAYER4_OBSERVATION_SPEC.md, docs/OBSERVATION/README.md, observation/README.md, docs/runtime/README.md, docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md, README.md (root).

### 6. Final status
**PHASE 1 DOCS AUDIT READY**

---

## 7. Follow-up (2026-04-14) — docs corpus alignment

Surgical updates (no mass moves) to reduce drift called out in §2–§4:

- **`docs/README.md`** — Replaced generic `~/…` tree with pointers to [REPO_LAYOUT_INVENTORY.md](REPO_LAYOUT_INVENTORY.md), pytest-based test instructions, `docs/api/README.md` index, corrected RAG paths (`runtime/rag/`), non-invariant “system stats,” and governed-stack log locations.
- **`docs/api/README.md`** — New index for split API/schema surfaces.
- **`docs/OBSERVATION/README.md`** and **`observation/README.md`** — Short table linking `docs/OBSERVATION/`, repo-root `observation/`, `runtime/observation/`, `runtime/obs/`.
- **`docs/archive/Notes.md`** — Non-canonical essay (moved from `docs/Notes.md`).
- **`docs/production_closure_handbook_corrected_canonical_version.md`** — Explicit deferral to `mvp_declaration/` for formal sign-off.
- **`docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md`** — Branch naming note aligned with current runbooks.

**Still deferred:** Full merge of dual observation indexes into one URL (case-sensitive paths); optional future canonical paragraph in `LAYER4_OBSERVATION_SPEC.md`.

**Archive (2026-04-14):** Non-canonical and obsolete docs moved under **`docs/archive/`** (see [archive/README.md](../archive/README.md)): `Notes.md`, historical demo guide, TEMP Motadata integration guide, CodeRabbit matrices, and prior `docs/status/` journal files.
