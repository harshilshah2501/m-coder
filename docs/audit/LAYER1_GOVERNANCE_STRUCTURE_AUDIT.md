# Phase 2 — Layer-1 Governance Structure Audit Report

**Repository:** m-coder  
**Audit phase:** Phase 2 only (Layer-1 governance structural audit, read-only)  
**Date:** 2026-03-15  
**Scope:** Governance layout, canonical ownership, naming, path contracts, and separation from Layer-2/3/4. No moves, renames, edits, or remediation performed.

---

## 1. Purpose and scope

This document is the deliverable for **Phase 2** of the m-coder structural audit. It is a **read-only structural audit** of **Layer-1 governance** only. It does not move or rename files, rewrite governance docs, change code or imports, merge duplicates, archive material, or perform remediation. The audit inventories governance anchors, classifies governance material by role, assesses canonical spine clarity, doctrine duplication risk, cross-layer leakage, path-contract sensitivity, and naming consistency.

---

## 2. Executive assessment

- **Overall Layer-1 structural health:** Good. Governance has a **clear canonical anchor**: root `AGENT_EXECUTION_RULES.md` (execution rules), `governance/CONSTITUTIONAL_MANIFEST_v1.0.md` (phase doctrine and structural invariants), `governance/REPOSITORY_CONSTITUTION.md` (structural governance and exemplar consumption), and `governance/README.md` (Layer-1 index). The docs layer `docs/governance/` is explicitly a **pointer layer** (README and AGENT_EXECUTION_RULES point to root and governance/). Doctrine is not duplicated in competing sources; `docs/LAYER1_GOVERNANCE_SPEC.md` and `docs/NON_NEGOTIABLE_INVARIANTS.md` reference governance artifacts and restate invariants for readability but do not claim to be the source of phase definitions. Cross-layer references from ml/ and runtime/ are **reference-only** (read manifest for injection, or cite REF/CONF/DES in code); no governance content is misplaced under other layers. Risks are limited to: (1) potential drift if LAYER1_GOVERNANCE_SPEC or NON_NEGOTIABLE_INVARIANTS are edited without updating the manifest; (2) governance/ containing status/report files (PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, AI-Session-Progress-Tracker) that are supporting/reporting rather than doctrine—they do not compete but could be clarified.

- **Does governance have a clear canonical anchor?** Yes. Root AGENT_EXECUTION_RULES is the single source for agent execution rules; governance/CONSTITUTIONAL_MANIFEST_v1.0.md is the single source for phase definitions and dominance; governance/REPOSITORY_CONSTITUTION is the single source for structural boundaries and exemplar consumption. docs/governance/ does not compete; it points to root and governance/.

- **Biggest governance structural risks:** (1) **Doctrine restatement drift** — LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS restate phase semantics and invariants; if updated independently from the manifest, they could drift. (2) **Dual AGENT_EXECUTION_RULES** — root is canonical, docs/governance/ holds a pointer; content alignment was not diffed in this audit; drift would be a consistency risk. (3) **Governance dir mix** — governance/ contains both canonical doctrine (CONSTITUTIONAL_MANIFEST, REPOSITORY_CONSTITUTION, README) and status/report files (PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, AI-Session-Progress-Tracker); placement is acceptable but could be documented so readers do not treat status docs as doctrine.

---

## 3. Layer-1 canonical governance spine

For each major governance anchor we state: path; role; canonical / pointer / supporting; whether it competes; confidence.

| Anchor | Path | Role | Canonical / pointer / supporting | Competes? | Confidence |
|--------|------|------|----------------------------------|------------|-------------|
| Agent execution rules | AGENT_EXECUTION_RULES.md (root) | Mandatory execution rules for agents; branch discipline, file safety, protected surfaces, runtime invariants | canonical | No (docs copy is pointer only) | **clear** |
| Phase doctrine & structural invariants | governance/CONSTITUTIONAL_MANIFEST_v1.0.md | Phase definitions (REF, CONF, DES, MIX, CODE), dominance hierarchy, structural invariants, locked constraints | canonical | No | **clear** |
| Structural governance & consumption | governance/REPOSITORY_CONSTITUTION.md | Structural layers, Golden Exemplars sovereignty, exemplar consumption contract (mirror under ml), docs/archive boundaries | canonical | No | **clear** |
| Layer-1 index | governance/README.md | Index to root AGENT_EXECUTION_RULES and governance/CONSTITUTIONAL_MANIFEST; allowed/forbidden | canonical index | No | **clear** |
| Docs governance index | docs/governance/README.md | Layer-1 index in docs; states root AGENT_EXECUTION_RULES is canonical; links to governance/CONSTITUTIONAL_MANIFEST | pointer | No | **clear** |
| Docs execution rules pointer | docs/governance/AGENT_EXECUTION_RULES.md | Pointer to root file only; “canonical source at repository root” | pointer | No | **clear** |
| Comprehensive governance spec | docs/LAYER1_GOVERNANCE_SPEC.md | Expanded spec; references governance/CONSTITUTIONAL_MANIFEST as artifact; restates phase table, dominance, boundary, GREG, failure modes | supporting | No (points to manifest); restatement drift risk if edited alone | **partially clear** (role as “supporting” not “source” could be stated at top) |
| Fail-closed invariants | docs/NON_NEGOTIABLE_INVARIANTS.md | Gate-down→block, no bypass, append-only ledger, boundary invariance, REF dominance | supporting | No; references “Constitutional Manifest” for boundary; restatement drift risk | **clear** |

---

## 4. Governance inventory by role

Structured inventory of major governance files/clusters. Classification and placement quality as defined in the task.

| Path | Role / topic | Classification | Canonical status | Placement quality | Notes |
|------|----------------|----------------|------------------|-------------------|-------|
| AGENT_EXECUTION_RULES.md (root) | Agent execution rules; protected surfaces; runtime invariants | canonical doctrine | canonical | good | Single source; docs/governance copy is pointer only |
| governance/CONSTITUTIONAL_MANIFEST_v1.0.md | Phase definitions, dominance, structural invariants | canonical doctrine | canonical | good | Referenced by MASTER_SYSTEM_SPEC, LAYER1_GOVERNANCE_SPEC, ml profiles |
| governance/REPOSITORY_CONSTITUTION.md | Structural layers, exemplar sovereignty, consumption contract | canonical doctrine | canonical | good | Defines governance/, ml/, docs/, archive boundaries |
| governance/README.md | Layer-1 index | canonical pointer/index | canonical | good | Points to root rules and CONSTITUTIONAL_MANIFEST |
| governance/PHASE_STATUS_REPORT.md | Phase status (Golden Exemplars phases 3–8); points to LIVE_ROADMAP_TRACKER | reporting / milestone artifact | non-canonical | good | Governance-facing status; not doctrine |
| governance/PROJECT_STATE_LEDGER.md | Corpus state snapshot; points to LIVE_ROADMAP_TRACKER, LAYER2 verification | reporting / milestone artifact | non-canonical | good | Governance-facing; not doctrine |
| governance/AI-Session-Progress-Tracker.md | Session progress tracking | temporary / planning | non-canonical | questionable | Could be clarified as non-doctrine |
| governance/golden-exemplars/ | Golden Exemplars phases, GREG, reachability, validation-ledger, surfaces | governance exemplar/reference | canonical (content) | good | Single source per REPOSITORY_CONSTITUTION |
| governance/review-packages/ | Phase-01 review package, orientation guides, exemplars to review | governance exemplar/reference | non-canonical (supporting) | good | Review/distribution material |
| docs/governance/README.md | Layer-1 index in docs | canonical pointer | pointer | good | Explicit “root is canonical” |
| docs/governance/AGENT_EXECUTION_RULES.md | Pointer to root AGENT_EXECUTION_RULES | canonical pointer | pointer | good | No content duplication; pointer only |
| docs/LAYER1_GOVERNANCE_SPEC.md | Comprehensive Layer-1 spec; phase table, dominance, GREG, failure modes | supporting governance material | non-canonical | good | References governance/CONSTITUTIONAL_MANIFEST as artifact; restates for readability |
| docs/NON_NEGOTIABLE_INVARIANTS.md | Fail-closed, gate-down→block, append-only ledger, REF dominance | supporting governance material | non-canonical | good | References Constitutional Manifest for boundary |
| docs/PHASE_ALIGNMENT_TABLE_V0_1.md | Phase↔stage alignment | supporting | non-canonical | good | Linked from MASTER_SYSTEM_SPEC |
| docs/ARCHITECTURE_4_LAYER.md | Layer mapping; “no doctrine change”; canonical sources only | supporting | non-canonical | good | Does not redefine phase semantics |
| docs/MASTER_SYSTEM_SPEC.md | TOC; links to governance/CONSTITUTIONAL_MANIFEST, governance/README | supporting (spine) | canonical (as entry) | good | Points to governance; does not duplicate doctrine |

---

## 5. Governance structural findings

Each finding uses: Finding; Why it is a problem; Severity; Recommended action; Action timing.

**Finding 1 — Doctrine restatement in docs without “source of truth” label**  
- **Why it is a problem:** docs/LAYER1_GOVERNANCE_SPEC.md contains a phase table and dominance/boundary text that mirrors governance/CONSTITUTIONAL_MANIFEST_v1.0.md. docs/NON_NEGOTIABLE_INVARIANTS.md restates REF dominance and boundary invariance. Both reference the manifest, but a reader could treat the spec or invariants doc as the source of phase definitions. If LAYER1_GOVERNANCE_SPEC or NON_NEGOTIABLE_INVARIANTS are edited without updating the manifest, doctrine would drift.  
- **Severity:** Medium (drift risk; no current conflict).  
- **Recommended action:** Add a one-line disclaimer at the top of LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS: “Source of truth for phase definitions and structural invariants: governance/CONSTITUTIONAL_MANIFEST_v1.0.md. This document restates for reference only; do not update without updating the manifest.”  
- **Action timing:** `later` (remediation phase).

**Finding 2 — Dual AGENT_EXECUTION_RULES (root vs docs/governance)**  
- **Why it is a problem:** Root holds the canonical file; docs/governance/AGENT_EXECUTION_RULES.md is a pointer. Phase 0 and Phase 1 and SYSTEM_GOVERNANCE_AUDIT already note that drift between the two would be a consistency risk. Content alignment was not diffed in this audit.  
- **Severity:** Low (documented; pointer is explicit).  
- **Recommended action:** No structural change. Optionally diff root vs docs copy in a later verification pass; if identical, add one-line “canonical: root; this file is pointer only” at top of docs copy if not already present.  
- **Action timing:** `later` or `never touch without dedicated plan` for root copy.

**Finding 3 — Governance dir contains status/report files**  
- **Why it is a problem:** governance/ contains PHASE_STATUS_REPORT.md, PROJECT_STATE_LEDGER.md, and AI-Session-Progress-Tracker.md. These are status/corpus reports that point to LIVE_ROADMAP_TRACKER and ml artifacts; they are not phase doctrine or structural invariants. A new contributor might assume everything under governance/ is doctrine.  
- **Severity:** Low (no ownership conflict; clarity only).  
- **Recommended action:** In governance/README or REPOSITORY_CONSTITUTION, add one sentence: “Status and corpus reports (e.g. PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER) in this directory are governance-facing snapshots; canonical milestone and evidence live in docs/LIVE_ROADMAP_TRACKER.md and ml artifacts.”  
- **Action timing:** `later`.

**Finding 4 — Protected path docs/CONSTITUTION* in AGENT_EXECUTION_RULES**  
- **Why it is a problem:** AGENT_EXECUTION_RULES §3 lists “docs/CONSTITUTION*” as a protected surface. No files under docs/ match that pattern; constitutional content lives under governance/. SYSTEM_GOVERNANCE_AUDIT confirmed no docs/CONSTITUTION* files. So the rule is defensive; no current conflict.  
- **Severity:** Low (no duplicate; rule is guard).  
- **Recommended action:** None required. Optional: note in a doc that “docs/CONSTITUTION*” is reserved and unused so that future docs do not create a file that could be mistaken for doctrine.  
- **Action timing:** `later` or leave as-is.

---

## 6. Governance anchor clarity test

- **Is governance canonically anchored in one clear spine?** Yes. Execution rules: root AGENT_EXECUTION_RULES.md. Phase doctrine and structural invariants: governance/CONSTITUTIONAL_MANIFEST_v1.0.md. Structural governance and consumption: governance/REPOSITORY_CONSTITUTION.md. Index: governance/README.md and docs/governance/README.md (both point to root and governance/). There is no second “source of truth” for execution rules or phase definitions.

- **Does root AGENT_EXECUTION_RULES compete with governance/ or docs/governance?** No. docs/governance/AGENT_EXECUTION_RULES.md states that the root file is canonical. governance/ does not contain an alternative execution-rules file. governance/ holds constitutional manifest and repository constitution, which are different artifacts (doctrine vs execution rules).

- **Are there multiple apparent “sources of truth”?** No for execution rules (root only) and no for phase definitions (CONSTITUTIONAL_MANIFEST only). LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS are supporting restatements that reference the manifest; they are not designated as sources of truth.

- **Is the current structure understandable to a new contributor?** Yes, provided they start from README → MASTER_SYSTEM_SPEC or docs/governance/README. Both point to root AGENT_EXECUTION_RULES and governance/CONSTITUTIONAL_MANIFEST. The only ambiguity is whether LAYER1_GOVERNANCE_SPEC is “the” governance spec or an expansion of the manifest; a one-line “source of truth: governance/CONSTITUTIONAL_MANIFEST” would remove that.

---

## 7. Doctrine duplication test

- **Phase semantics (REF, CONF, DES, MIX, CODE):** Defined in full in governance/CONSTITUTIONAL_MANIFEST_v1.0.md. Summarized in docs/LAYER1_GOVERNANCE_SPEC.md (phase table) and referenced in docs/ARCHITECTURE_4_LAYER.md, docs/MASTER_SYSTEM_SPEC.md, and multiple runtime/milestone docs. **Duplication:** Restatement only in LAYER1_GOVERNANCE_SPEC; no competing definition. **Drift risk:** Medium if LAYER1_GOVERNANCE_SPEC is edited without updating the manifest.

- **Dominance hierarchy (Authority > Irreversibility > Design Preference; REF dominates ambiguity):** In CONSTITUTIONAL_MANIFEST §3–4; restated in LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS. **Duplication:** Restatement; no competing source. **Drift risk:** Same as above.

- **Refusal / conditional allowance:** REF “must refuse entirely”; “no conditional allowance” in CONSTITUTIONAL_MANIFEST and AGENT_EXECUTION_RULES §4; NON_NEGOTIABLE_INVARIANTS “REF phase MUST yield REFUSAL; no conditional allowance.” **Duplication:** Consistent restatement. **Drift risk:** Low if NON_NEGOTIABLE_INVARIANTS is kept in sync with manifest/rules.

- **Boundary doctrine:** “Exact boundary phrase must remain character-for-character identical between Phase-3 and Phase-4” in CONSTITUTIONAL_MANIFEST §4; LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS reference it; NON_NEGOTIABLE_INVARIANTS cites boundary_hashing.v0.1.json. **Duplication:** Reference and restatement; no competing definition. **Drift risk:** Low.

- **Irreversible-action doctrine:** In CONSTITUTIONAL_MANIFEST (CONF “explicit block at irreversible boundary”; CODE “execution prevented via guard condition”); REPOSITORY_CONSTITUTION (structural); AGENT_EXECUTION_RULES §4 “irreversible boundary semantics are preserved.” **Duplication:** Consistent; no competing source.

**Conclusion:** No conflicting doctrine sources. Restatements in docs are explicit or clearly derivative. Drift risk is manageable if supporting docs are updated only in lockstep with the manifest or are explicitly labeled “reference only; source: governance/CONSTITUTIONAL_MANIFEST_v1.0.md.”

---

## 8. Cross-layer leakage test

- **Layer-1 into Layer-2 (ml/):**  
  - **Relationship:** Layer-2 **reads** governance for injection and exemplar preparation. `ml/training/pipeline/stage6/stage6c/injections/profiles.py` reads `governance/CONSTITUTIONAL_MANIFEST_v1.0.md` and `docs/NON_NEGOTIABLE_INVARIANTS.md` to build constitution_v1 injection payload. `ml/scripts/prepare_exemplars.sh` copies from `governance/golden-exemplars/Phases` to a mirror (consumption contract in REPOSITORY_CONSTITUTION: training consumes mirror, not governance directly).  
  - **Assessment:** **Clean reference.** Governance is read-only; no governance content is authored under ml/. Exemplar consumption follows the mirror contract. No ambiguous overlap or misplaced ownership.

- **Layer-1 into Layer-3 (runtime/):**  
  - **Relationship:** Runtime code uses phase labels (REF, CONF, DES) and dominance_applied string (“REF>CONF>DES”) in plan_gate_stub, shadow, ledger, emulator. No runtime code reads governance/ or AGENT_EXECUTION_RULES by path. Docs (milestones, verification) reference AGENT_EXECUTION_RULES and governance dirs.  
  - **Assessment:** **Acceptable coupling.** Runtime implements doctrine; it does not redefine it. References are in docs and in-code semantics (enums, strings). No governance files placed under runtime/. No structural concern.

- **Layer-1 into Layer-4 (observation/):**  
  - **Relationship:** Observation code (collapse_vectors, collapse_models) mentions “governance/runtime collapse vectors” in comments. No observation code reads governance/ or AGENT_EXECUTION_RULES.  
  - **Assessment:** **Clean reference.** Terminology only; no coupling to governance paths. No structural concern.

**Summary:** Layer-1 is not leaking into other layers in the wrong way. Layer-2 has a read-only, contract-bound use of governance paths; Layer-3 and Layer-4 reference doctrine semantically or in docs only.

---

## 9. Governance Path Contract Register

| Path | Why path-sensitive | Referenced by | Risk if moved/renamed | Recommendation note |
|------|--------------------|---------------|------------------------|----------------------|
| AGENT_EXECUTION_RULES.md (root) | Canonical execution rules; protected surfaces listed in §3 | docs/governance/README, docs/governance/AGENT_EXECUTION_RULES, verification audits, M4.5 milestone | High | Do not move; many references assume root |
| governance/ | Layer-1 content root; protected in AGENT_EXECUTION_RULES §3 | MASTER_SYSTEM_SPEC, docs/governance/README, ml profiles, prepare_exemplars.sh | High | Do not move |
| governance/CONSTITUTIONAL_MANIFEST_v1.0.md | Canonical phase doctrine | MASTER_SYSTEM_SPEC, LAYER1_GOVERNANCE_SPEC, ml/training/.../profiles.py, stage6a DESIGN_INDEX | High | Do not move; path hardcoded in profiles.py |
| governance/REPOSITORY_CONSTITUTION.md | Structural governance; consumption contract | SYSTEM_GOVERNANCE_AUDIT, REPOSITORY_STRUCTURE_AUDIT | Medium | Do not move |
| governance/README.md | Layer-1 index | MASTER_SYSTEM_SPEC, docs spine | Medium | Do not move |
| governance/golden-exemplars/ | Golden Exemplars doctrine; single source per REPOSITORY_CONSTITUTION | REPOSITORY_CONSTITUTION, prepare_exemplars.sh (Phases) | High | Do not move; consumption contract depends on path |
| docs/governance/README.md | Docs Layer-1 index | MASTER_SYSTEM_SPEC, Phase 1 audit | Medium | Do not move |
| docs/governance/AGENT_EXECUTION_RULES.md | Pointer to root | SYSTEM_GOVERNANCE_AUDIT | Low | Pointer only; do not move without updating link |
| docs/LAYER1_GOVERNANCE_SPEC.md | Comprehensive governance spec | MASTER_SYSTEM_SPEC, SYSTEM_GOVERNANCE_AUDIT | Medium | Do not move; part of doc spine |
| docs/NON_NEGOTIABLE_INVARIANTS.md | Fail-closed invariants | MASTER_SYSTEM_SPEC, profiles.py (constitution_v1 injection) | High | Do not move; path used in ml profiles.py |

---

## 10. Preliminary keep / clarify / move-later / do-not-touch classification

| Item / cluster | Preliminary classification | Rationale |
|----------------|----------------------------|-----------|
| AGENT_EXECUTION_RULES.md (root) | do not touch without dedicated plan | Canonical; path contract; protected surfaces |
| governance/CONSTITUTIONAL_MANIFEST_v1.0.md | do not touch without dedicated plan | Single source of phase doctrine; referenced by ml and docs |
| governance/REPOSITORY_CONSTITUTION.md | keep | Canonical structural governance |
| governance/README.md | keep | Layer-1 index |
| governance/golden-exemplars/ | do not touch without dedicated plan | Single source for exemplars; consumption contract |
| governance/review-packages/ | keep | Supporting review material |
| governance/PHASE_STATUS_REPORT.md, PROJECT_STATE_LEDGER.md, AI-Session-Progress-Tracker.md | clarify later | Document as status/report, not doctrine |
| docs/governance/README.md, docs/governance/AGENT_EXECUTION_RULES.md | keep | Pointer layer; do not move |
| docs/LAYER1_GOVERNANCE_SPEC.md | clarify later | Add “source of truth: governance/CONSTITUTIONAL_MANIFEST” |
| docs/NON_NEGOTIABLE_INVARIANTS.md | clarify later | Add “source: Constitutional Manifest” if not already clear |

---

## 11. Immediate conclusions

- **Does Layer-1 have a clean canonical structure?** Yes. Execution rules live at root; phase doctrine and structural invariants live in governance/CONSTITUTIONAL_MANIFEST_v1.0.md; structural governance and consumption in governance/REPOSITORY_CONSTITUTION.md. docs/governance/ is a pointer layer. No competing sources of truth for doctrine.

- **What are the biggest governance structural risks?** (1) Restatement drift between LAYER1_GOVERNANCE_SPEC or NON_NEGOTIABLE_INVARIANTS and the manifest if edited independently. (2) Dual AGENT_EXECUTION_RULES (root vs docs copy) content drift, already noted in prior audits. (3) Governance dir containing status/report files that could be mistaken for doctrine—clarification only.

- **Which governance items are dangerous to touch?** Root AGENT_EXECUTION_RULES.md, governance/CONSTITUTIONAL_MANIFEST_v1.0.md, governance/golden-exemplars/, and paths referenced by ml (profiles.py: manifest + invariants; prepare_exemplars.sh: golden-exemplars/Phases). Renaming or moving these would break path contracts and injection/prepare logic.

- **What must be clarified later?** (1) LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS: state explicitly that governance/CONSTITUTIONAL_MANIFEST_v1.0.md is the source of truth for phase definitions. (2) governance/: document that PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, and AI-Session-Progress-Tracker are status/reporting, not doctrine.

- **What should the next audit phase be?** Per the approved plan, **Phase 3 — Layer-2 compilation / training audit** (ml/ layout, training/compiler/freeze/lineage/artifacts, generated vs canonical, stage docs placement).

---

## 12. Non-goals

This phase did **not**:

- Move, rename, or edit any governance or doc file.
- Change code or imports.
- Merge or archive any material.
- Fix restatement drift or add “source of truth” labels.
- Propose repo-wide cleanup or remediation.
- Audit Layer-2, Layer-3, or Layer-4 internals beyond reference checks needed to assess leakage.

---

## Phase 2 result summary

### 1. Artifact created
- **path:** `docs/audit/LAYER1_GOVERNANCE_STRUCTURE_AUDIT.md`

### 2. Canonical governance spine assessment
- **primary anchor:** governance/CONSTITUTIONAL_MANIFEST_v1.0.md (phase doctrine, dominance, structural invariants).
- **root execution rules:** AGENT_EXECUTION_RULES.md — single source; docs copy is pointer only.
- **governance directory:** governance/ — canonical content (CONSTITUTIONAL_MANIFEST, REPOSITORY_CONSTITUTION, README, golden-exemplars, review-packages); plus status/report files (PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, AI-Session-Progress-Tracker).
- **docs/governance pointer layer:** docs/governance/README.md and docs/governance/AGENT_EXECUTION_RULES.md — pointer/index only; no competition with root or governance/.
- **overall clarity:** clear — one spine; root rules + governance/ doctrine + docs pointers.

### 3. Major findings
- **finding 1:** Doctrine restatement in LAYER1_GOVERNANCE_SPEC and NON_NEGOTIABLE_INVARIANTS without explicit “source of truth: manifest” — drift risk if edited independently.
- **finding 2:** Dual AGENT_EXECUTION_RULES (root canonical, docs pointer); content alignment not diffed; drift risk documented in prior audits.
- **finding 3:** governance/ contains status/report files (PHASE_STATUS_REPORT, PROJECT_STATE_LEDGER, AI-Session-Progress-Tracker); clarify as non-doctrine.

### 4. Doctrine duplication result
- **status:** No conflicting sources; restatements only in supporting docs.
- **key evidence:** Phase definitions only in CONSTITUTIONAL_MANIFEST; LAYER1_GOVERNANCE_SPEC references it as artifact and restates phase table; NON_NEGOTIABLE_INVARIANTS references “Constitutional Manifest” for boundary; ARCHITECTURE_4_LAYER says “canonical sources only.”
- **conclusion:** Duplication is acceptable restatement; drift risk is medium if supporting docs are updated without updating the manifest; recommend labeling “source of truth” in a later phase.

### 5. Cross-layer leakage result
- **Layer-2:** Clean reference — ml reads governance/CONSTITUTIONAL_MANIFEST and docs/NON_NEGOTIABLE_INVARIANTS for injection; exemplar consumption via mirror per REPOSITORY_CONSTITUTION.
- **Layer-3:** Acceptable coupling — runtime uses REF/CONF/DES semantics and dominance; no governance path reads; docs reference AGENT_EXECUTION_RULES and governance.
- **Layer-4:** Clean reference — observation uses “governance” in comments only; no path coupling.

### 6. Path-sensitive governance items identified
- **number:** 10 (paths in Path Contract Register).
- **notable examples:** AGENT_EXECUTION_RULES.md (root), governance/, governance/CONSTITUTIONAL_MANIFEST_v1.0.md, governance/golden-exemplars/, docs/LAYER1_GOVERNANCE_SPEC.md, docs/NON_NEGOTIABLE_INVARIANTS.md (referenced by ml profiles.py).

### 7. Final status
**PHASE 2 GOVERNANCE AUDIT READY**
