# Patch Proposal Quality Hardening — Discovery (Doc Only)

Date: 2026-04-24  
Status: Q1/Q2 executed (quality diagnostics + builder hardening + offline suite); Q3 follow-up  
Depends on: `docs/validation/BOUNDED_PATCH_PROPOSAL_V1_STRATEGY.md`, `docs/validation/BOUNDED_PATCH_PROPOSAL_V1_REPORT.md`

## 1) Objective

Improve reviewer usefulness and trust in `patch_proposal.v1` outputs while preserving all current safety invariants:

- `PLAN_ONLY`
- `execution=false`
- no apply
- no execute
- no Stage 3 wiring
- no autonomous loop

## 2) Scope of hardening

Quality-only improvements to proposal artifacts:

1. proposal clarity/readability
2. diff-bounds realism
3. rollback plan quality
4. test-plan usefulness
5. omission/failure explanation quality
6. reviewer-facing output consistency

No authority, execution, or governance posture changes are in scope.

## 3) Quality rubric (v1)

Each emitted proposal should score against this rubric (0/1 per criterion; pass threshold defined in Section 4).

### A. Proposal clarity

- A1: each `proposed_edits[]` entry has concrete rationale tied to query/plan intent
- A2: intent wording avoids vague filler ("improve code", "clean up") without specifics
- A3: file list is concise and deduplicated

### B. Bounds realism

- B1: `proposed_edits` count is <= `bounded_scope.max_files_touched`
- B2: proposal paths are inside allowed/known plan scope
- B3: risk notes explicitly mention likely boundary overrun risks where relevant

### C. Rollback quality

- C1: rollback strategy is actionable (not generic placeholder text)
- C2: rollback safety checks are concrete and verifiable
- C3: rollback references touched scope (files/tests) instead of generic global rollback language

### D. Test plan usefulness

- D1: required checks map to proposed change type (logic/config/docs)
- D2: pass/fail criteria are observable and not tautological
- D3: plan includes at least one targeted check for the primary touched file/flow

### E. Omission/failure quality

- E1: omission reasons are deterministic and category-stable
- E2: omission messages are actionable for operator/reviewer next step
- E3: omission never leaks into fabricated partial proposal fields

### F. Reviewer UX consistency

- F1: `human_review_required=true` always present
- F2: reviewer checklist has no empty placeholders
- F3: narrative sections stay within concise length limits and avoid duplication

## 4) Acceptance criteria (quality gate)

For hardening completion:

1. Structural safety invariants remain unchanged and existing gates remain green.
2. On a quality fixture pack, emitted proposals meet:
   - required pass on all F-criteria and all bounds criteria (B1/B2)
   - >= 80% pass across remaining criteria
3. Omission fixtures produce deterministic reason classes with >= 95% stable mapping.
4. Reviewer quality regression tests pass with no added execution authority.

## 5) Proposed fixture matrix

Add dedicated proposal-quality fixtures (offline/contract style first):

- safe small refactor proposal (single-file)
- multi-file bounded behavior change proposal
- docs-only proposal with minimal tests
- weak evidence omission path
- over-bound candidate path (must omit with diagnostic)
- forbidden/refusal posture (must omit with diagnostic)

Each fixture should carry expected rubric outcomes and expected omission behavior.

## 6) Suggested implementation slices (future)

### Slice Q1 — Quality diagnostics + scoring

- add internal scoring helper for rubric
- expose non-authoritative quality diagnostics in metadata (additive)
- no change to emission authority

### Slice Q2 — Builder text-quality tightening

- improve rationale generation templates
- strengthen rollback/test-plan specificity
- ensure concise, non-redundant reviewer sections

### Slice Q3 — Quality fixture + gate expansion

- add quality-focused fixture suite and assertions
- enforce pass thresholds in CI-safe tests
- keep existing plan/trace/proposal dependency checks intact

## 7) Non-goals

This hardening phase does not:

- apply patches
- execute commands
- alter Stage 3 wiring
- change governance posture semantics
- introduce autonomous behavior

## 8) Summary

`patch_proposal.v1` capability is complete for governed non-autonomous proposal emission.  
Next value is proposal quality hardening: make outputs clearer, more realistic, and more reviewer-actionable while preserving all current safety contracts.

## 9) Q1/Q2 closure evidence

- Added offline quality fixture pack: `docs/validation/patch_proposal_quality_scenarios.v1.json`
- Added validator quality scoring + scenario summary:
  - `runtime/patch_proposal/v1_validate.py`
  - `runtime/scripts/motadata_behavior_verify.py` (`scenario_suite.patch_quality_summary`)
- Q2 builder hardening completed in `runtime/ask_service/patch_proposal_builder.py`:
  - 2+ concrete reviewer checklist items
  - 2+ specific required test checks
  - rationale specificity with explicit file/path + plan bounds cue
- WSL artifact:
  - `TestRunEvals/patch_proposal_quality_validation.q2.wsl.json`
  - `all_pass=true`, `scenario_count=6`, `average_score_percent=85.56` (up from 82.67 baseline)
