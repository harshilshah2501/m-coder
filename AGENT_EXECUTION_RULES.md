# AGENT_EXECUTION_RULES.md

## Purpose

This repository is developed using governed autonomous agents.
Agents must preserve architectural discipline, fail-closed runtime behavior,
and milestone isolation.

This file defines mandatory execution rules for all autonomous coding agents.

---

## 1. Global Operating Doctrine

Agents are implementers, not architects.

You must:
- preserve existing architecture
- preserve governance invariants
- make the smallest safe change
- prefer additive implementation over refactoring
- stop when the requested milestone is complete

You must NOT:
- redesign the system
- reinterpret governance semantics
- broaden scope beyond the assigned milestone
- make opportunistic cleanup changes
- modify unrelated files for style or formatting

---

## 2. Branch Discipline

Each agent works on exactly one milestone branch.

Rules:
- branch from the assigned baseline only
- do not merge, rebase, or cherry-pick other feature branches unless explicitly instructed
- do not switch milestones inside the same branch
- do not perform unrelated work

---

## 3. File Safety Rules

Prefer:
- new files
- narrow adapters
- isolated tests
- local documentation updates

Avoid:
- broad edits to shared runtime kernel files
- changing schemas unless explicitly required
- touching plugin code unless the milestone is plugin-specific
- touching governance or training layers from Layer-3 milestone work

Never modify protected surfaces unless explicitly instructed:
- governance/**
- ml/**
- docs/CONSTITUTION*
- docs/GOVERNANCE/**
- runtime/schemas/**
- runtime/ide/schemas/**
- core doctrine / invariant documents

---

## 4. Runtime Safety Invariants

The following must remain true after every change:

- fail-closed behavior is preserved
- no bypass path is introduced
- Plan-Gate governance remains enforced
- append-only ledger behavior is preserved
- irreversible boundary semantics are preserved
- REF dominates ambiguity
- runtime decides; model does not own control flow
- shadow mode never crosses irreversible boundaries

If your change risks violating any of these, stop and reduce scope.

---

## 5. Refactor Restrictions

Refactors are forbidden unless they are strictly necessary to complete the assigned milestone.

If a refactor is unavoidable:
- keep it minimal
- document why it is necessary
- prove no behavior change outside milestone scope
- add regression tests

Forbidden refactor patterns:
- renaming widely used modules
- moving directories without need
- rewriting shared interfaces for convenience
- changing public contracts for cleanup purposes
- reformatting unrelated files

---

## 6. Testing Requirements

No task is complete without tests.

Required:
- add or update milestone-local tests
- run related regression tests
- verify no breakage in sandbox / ledger / plan-gate semantics if touched
- report exact commands run
- report exact pass/fail status

Do not claim success if tests are failing.

---

## 7. Documentation Requirements

For each branch, maintain a branch execution note under:

docs/runtime/branch_execution_notes/<branch>.md

It must contain:
- objective
- boundaries
- files changed
- tests run
- evidence summary
- known limitations
- merge risks

---

## 8. Allowed Decision Pattern

When uncertain, choose the narrowest safe option.

Order of preference:
1. implement with existing interfaces
2. add a narrow local adapter
3. add a small internal helper
4. document blocker and stop

Do NOT choose:
- broad redesign
- speculative abstraction
- future-proofing refactor
- “while I’m here” cleanup

---

## 9. Commit Behavior

Commits must be milestone-specific and reviewable.

Preferred commit style:
- short
- concrete
- scoped

Examples:
- [M3.5] Add append-only ledger replay utility
- [M3.6] Add shadow ingestion batch validation tests
- [M3.1] Enforce orchestrator iteration cap

Do not mix multiple milestones in one commit.

---

## 10. Pull Request Contract

Each PR must include:
- milestone goal
- exact file scope
- invariants preserved
- tests executed
- evidence summary
- known limitations
- merge dependency, if any

If dependency exists, state it explicitly.

---

## 11. Stop Conditions

Stop and report instead of improvising if:
- protected files must change
- milestone requires architecture redesign
- another branch’s unfinished work is required
- tests fail and root cause lies outside milestone scope
- governance behavior becomes ambiguous

When stopping, produce:
- blocker summary
- minimal recommended next step
- exact files inspected

---

## 12. Agent Success Definition

An agent is successful only if:
- assigned milestone is completed
- scope stayed contained
- invariants remained intact
- tests passed
- PR is safe to review
- no architecture drift was introduced