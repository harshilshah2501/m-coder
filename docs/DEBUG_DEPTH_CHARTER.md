# Debug Depth Charter — Thinking With Code

**Status:** active charter (post-closure follow-on)  
**Tracker anchor:** `docs/LIVE_ROADMAP_TRACKER.md` §1.4 (`DEBUG-DEPTH-CHARTER-V1`)  
**Scenario pack (D1):** `docs/validation/debug_depth_scenarios.v1.json`  
**Baseline guardrail:** preserve `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5 behavior invariants

---

## 1. Objective

Increase **debug reasoning depth** and operator usefulness for `EXPLAIN_DEBUG` without reopening closed MVP gates or introducing architecture churn.

This charter exists because:
- retrieval baseline and authority-gated Ask are already stabilized
- explain/debug usefulness is present but still shallow on harder code reasoning asks
- post-closure expansion should prioritize visible product value over broad ingestion surface growth

---

## 2. Scope

### In scope
- Prompt/response quality for `EXPLAIN_DEBUG` on code-centered asks.
- Selection grounding behavior for minimal snippets and method-level reasoning.
- Evidence-first debug output quality (`summary`, `logic_flow`, `likely_bug_risk`, `evidence`, `confidence_limits`).
- Deterministic failure handling when reasoning service is unavailable.
- Repeatable evaluation set and score rubric for debug depth.

### Out of scope (for this charter)
- Jira/PR ingestion expansion (M3.13-M3.16).
- Task evaluation harness expansion (M3.18).
- Retrieval architecture churn (new vector stores, graph DB, alternate RAG stacks).
- Assist influence enablement (remains advisory-only unless separately chartered).

---

## 3. Non-negotiables

- Do not regress closure invariants from `MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5.
- Do not introduce silent fallback behavior on debug path.
- Do not allow ungrounded confident debug output when evidence is weak/insufficient.
- Keep runtime-owned control flow intact (no LLM-owned orchestration).

---

## 4. Acceptance metrics

This charter is complete only when all of the following are true:

1. **Grounding correctness**
   - Selected file grounding appears first in evidence for debug outputs.
   - Missing selected file returns explicit insufficient grounding.
2. **Reasoning depth**
   - Debug output contains concrete logic flow and likely risk statements on curated hard cases.
   - Template-style generic guidance is reduced on strong-evidence debug asks.
3. **Failure truthfulness**
   - vLLM/transport failures remain explicit and do not masquerade as successful deep debug analysis.
4. **Determinism**
   - Repeat runs on fixed fixtures produce stable structured fields.
5. **No baseline regression**
   - Existing behavior verification suite remains green under §5 policy.

---

## 5. Work phases and live checklist

Status markers: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETE`, `VALIDATING`, `BLOCKED`.

| ID | Task | Status | Exit criteria |
|----|------|--------|---------------|
| D1 | Define debug-depth scenario pack (easy/medium/hard) | **COMPLETE** | `docs/validation/debug_depth_scenarios.v1.json` + per-scenario `expect_rubric` (numeric scoring = D2) |
| D2 | Define scoring rubric (depth, grounding, actionability, honesty) | NOT_STARTED | Deterministic rubric schema + scorer utility |
| D3 | Prompt contract refinement for explain_debug | NOT_STARTED | Prompt updates with tests for grounding and output structure |
| D4 | Selection-aware reasoning upgrades (method/flow clues) | NOT_STARTED | Improved outputs on hard cases without weakening insufficiency rules |
| D5 | Failure-path hardening and truthfulness checks | NOT_STARTED | Explicit failure outputs + no fake planner substitution for deep debug |
| D6 | Regression suite expansion (unit + scenario) | NOT_STARTED | Added pytest coverage for new debug-depth cases |
| D7 | Baseline safety verification (`motadata_behavior_verify.py`) | NOT_STARTED | §5 regression pair documented with SHA + artifacts |
| D8 | Charter closure report | NOT_STARTED | Report with metrics, before/after deltas, and decision |

---

## 6. Execution order

Recommended order:
1. D1-D2 (evaluation contract first)
2. D3-D5 (behavior changes under tests)
3. D6 (expanded regressions)
4. D7 (baseline guardrail verification)
5. D8 (closure decision)

---

## 7. Evidence and reporting

- Scenario pack: `docs/validation/debug_depth_scenarios.v1.json`
- Test artifacts: `runtime/tests/test_reasoner_explain_debug_prompt.py`, `runtime/tests/test_reasoner_explain_debug_logging.py`, `runtime/tests/test_explain_debug_action6_proof.py` (+ new D1-D6 files).
- Operational context: `docs/audit/DEBUG_PATH_VALIDATION_REPORT.md`, `docs/DEBUG_PATH_VALIDATION_RUNBOOK.md`.
- Maintenance discipline: `docs/validation/POST_CLOSURE_MAINTENANCE.md`.

All milestone claims under this charter must include:
- commit SHA
- exact pytest command(s)
- pass/fail counts
- baseline comparison note vs §5 policy

---

## 8. Decision policy

- If D7 fails (baseline regression), freeze and rollback charter changes until parity is restored.
- If D4 improves depth but increases hallucination risk, prefer truthful insufficiency over overconfident analysis.
- If trade-off is unclear, keep behavior conservative and document the unresolved edge cases.

---

*This charter is intentionally narrow: increase debug depth while preserving closed-slice honesty and reproducibility.*
