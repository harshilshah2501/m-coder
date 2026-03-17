# Phase 10 — Batch C Execution Report (Naming and Legacy Clarification)

**Repository:** m-coder  
**Batch:** C — Naming and legacy clarification (doc-only)  
**Date:** 2026-03-15  
**Governing plan:** [STRUCTURAL_REMEDIATION_PLAN.md](STRUCTURAL_REMEDIATION_PLAN.md)

---

## 1. Purpose

Batch C is **naming and legacy clarification only**. It reduces naming ambiguity and legacy-structure confusion by adding minimal clarifying documentation in canonical layer specs. No files or directories were moved or renamed. No code was edited. No path normalization or case changes were applied.

---

## 2. Files inspected

| Target | Purpose |
|--------|---------|
| `docs/OBSERVATION/README.md` | Layer-4 docs-spine index; relationship to observation/README.md |
| `observation/README.md` | Layer-4 package root README |
| `docs/LAYER4_OBSERVATION_SPEC.md` | Canonical Layer-4 spec; already had observation/ vs runtime/observation/ (Batch A) |
| `docs/runtime/README.md` | Runtime index; already points to LAYER3_RUNTIME_SPEC |
| `docs/LAYER3_RUNTIME_SPEC.md` | Canonical Layer-3 spec; Plan-Gate section |
| `runtime/README.md` | Runtime package README; plan_gate_stub, plan_gate_service described |
| `docs/LAYER2_COMPILATION_SPEC.md` | Canonical Layer-2 spec; Stage-7 section |
| Stage-7 / sft/stage7 references in docs | Whether ambiguity still warranted a note |

---

## 3. Files modified

| File | Why touched |
|------|-------------|
| `docs/LAYER4_OBSERVATION_SPEC.md` | Add one sentence clarifying OBSERVATION vs observation and dual index roles (docs-spine index vs package root). |
| `docs/LAYER3_RUNTIME_SPEC.md` | Add one bullet clarifying plangate (production) vs plan_gate_stub (protocol stub) and policies/ (test-only) vs plangate. |
| `docs/LAYER2_COMPILATION_SPEC.md` | Add one sentence in Stage-7 section clarifying that sft/stage7/ is the CONF drift bundle, not the Stage-7 compiler. |

---

## 4. Clarifications applied

### A. OBSERVATION vs observation and dual observation index (LAYER4_OBSERVATION_SPEC)

- **Added:** One sentence after the existing Directory line: "Two index entrypoints: `docs/OBSERVATION/README.md` (docs-spine Layer-4 index) and `observation/README.md` (package root)."
- **Justified:** Readers could not tell why two Layer-4 README paths exist or what each is for; one canonical sentence assigns roles without touching either file.
- **Broader edits avoided:** No edit to docs/OBSERVATION/README.md or observation/README.md (would duplicate truth); no case normalization; no merge of the two indices.

### B. plangate vs plan_gate_stub and policies vs plangate (LAYER3_RUNTIME_SPEC)

- **Added:** One bullet under Plan-Gate Architecture: "**Implementation:** Production plan-gate logic lives in `runtime/plangate/`; `runtime/plan_gate_stub/` is a protocol stub for demos and IDE contract testing. `runtime/policies/` is a function-level authority/irreversibility surface used only by tests; production uses plangate."
- **Justified:** Audits noted confusion between plangate (production) and plan_gate_stub (stub) and between policies/ and plangate; LAYER3_RUNTIME_SPEC is the single canonical runtime spec.
- **Broader edits avoided:** No rewrite of Plan-Gate section; no edit to runtime/README.md (it already describes stub and service; plangate is listed in docs/runtime/README pointer); no implementation detail beyond role assignment.

### C. Stage-7 naming (LAYER2_COMPILATION_SPEC)

- **Added:** One sentence in the Stage-7 subsection: "**Note:** The path `ml/training/sft/stage7/` is the CONF drift workflow bundle (tools and outputs), not the Stage-7 compiler."
- **Justified:** Stage-7 table and compiler/freeze text do not mention sft/stage7; the naming overlap was flagged in audits; one sentence removes ambiguity in the canonical Layer-2 spec.
- **Broader edits avoided:** No new Stage-7 section; no edit to STAGE_LAYOUT_CANONICAL or other Layer-2 docs; single sentence only.

---

## 5. Ambiguities intentionally left unchanged

- **docs/OBSERVATION/README.md and observation/README.md content:** Not edited. The relationship is stated once in LAYER4_OBSERVATION_SPEC; adding the same to both READMEs would duplicate truth.
- **runtime/README.md:** Already describes plan_gate_stub and plan_gate_service; does not need to repeat plangate vs stub (now in LAYER3_RUNTIME_SPEC).
- **Case or path normalization:** OBSERVATION vs observation casing was not changed; no link or path edits. Clarification only.

---

## 6. Non-changes

- **No renames** of files or directories.
- **No path normalization** or case changes in paths or links.
- **No code edits** in runtime, observation, or ml.
- **No file moves**; no structural changes.
- **No report or root hygiene work**; no Batch D, E, or F scope.
- **No edits** to docs/OBSERVATION/README.md, observation/README.md, milestone docs, or audit artifacts (except this report).

---

## 7. Validation

- **Minimality:** Three files modified; one sentence or one bullet per clarification theme; no paragraphs or restatement of existing content.
- **No duplicate truth:** OBSERVATION/observation and dual index stated only in LAYER4_OBSERVATION_SPEC; plangate/stub/policies only in LAYER3_RUNTIME_SPEC; Stage-7/sft only in LAYER2_COMPILATION_SPEC.
- **No path-contract impact:** No paths moved or renamed; no references to code or scripts changed; docs-only additive edits.
- **Scope:** Only the five Batch C themes (OBSERVATION vs observation, dual index, plangate vs plan_gate_stub, policies vs plangate, Stage-7 note); no report convention, no root cleanup, no governance or Batch A/B content.

---

## 8. Final status

**BATCH C COMPLETE**
