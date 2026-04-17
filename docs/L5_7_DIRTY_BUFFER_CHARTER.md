# L5.7 Charter — Dirty Buffer / Live Overlay

**Status:** active charter (post-closure follow-on)  
**Tracker anchor:** `docs/LIVE_ROADMAP_TRACKER.md` §1.4 (`L57-DIRTY-BUFFER-CHARTER-V1`)  
**Scenario pack (D1):** `docs/validation/l57_dirty_buffer_scenarios.v1.json`  
**Baseline guardrail:** preserve `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5 behavior invariants

---

## 1. Objective

Close the `L5.7` correctness gap where Ask/Debug reasoning can miss unsaved editor changes by introducing a deterministic dirty-buffer overlay on top of on-disk retrieval.

This charter exists because:
- current retrieval baseline is stable and closed for MVP scope
- developer pain remains when selected file content in IDE differs from on-disk index
- overlay behavior can improve answer correctness without architecture churn

---

## 2. Scope

### In scope
- Overlay contract for unsaved file content on evidence-first Ask path.
- Deterministic merge precedence between disk snippets and live buffer text.
- Explain/debug selected-file grounding when active buffer diverges from disk.
- Explicit metadata signals for overlay use in Ask response surfaces.
- Repeatable scenario evaluation for overlay correctness.

### Out of scope (for this charter)
- New retrieval backends, ranking stacks, or non-deterministic heuristics.
- Broad plugin UX redesign beyond payload/contract fields needed for overlay.
- Assist influence, auto-execution, or authority-policy changes.
- Reopening closed L5.8 harness closure scope.

---

## 3. Non-negotiables

- Do not regress closure invariants from `MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5.
- Overlay must be deterministic and auditable in payload/metadata.
- Overlay must not mutate on-disk index truth.
- On missing/invalid dirty-buffer input, fail safe to current behavior with explicit notes.

---

## 4. Acceptance metrics

This charter is complete only when all of the following are true:

1. **Overlay correctness**
   - If dirty content exists for a selected file, evidence/snippets for that path reflect overlay text.
   - If no dirty content exists, behavior matches current disk-based baseline.
2. **Determinism**
   - Same request payload and workspace state yield stable context/evidence outputs.
3. **Debug grounding fidelity**
   - `EXPLAIN_DEBUG` references selected-file behavior from effective overlay content when present.
4. **Observability**
   - Ask response includes explicit metadata indicating whether overlay was applied.
5. **No baseline regression**
   - Existing verification suite remains green under §5 policy.

---

## 5. Work phases and live checklist

Status markers: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETE`, `VALIDATING`, `BLOCKED`.

| ID | Task | Status | Exit criteria |
|----|------|--------|---------------|
| D1 | Define dirty-buffer scenario pack (selected file + supporting files) | **COMPLETE** | `docs/validation/l57_dirty_buffer_scenarios.v1.json` committed with expected overlay checks |
| D2 | Define request contract for overlay payload | **COMPLETE** | `ask_request.v0.1` + `ask_request.v1.0` `client_context.dirty_buffers[]` schema contract (path/content required) with validation tests |
| D3 | Implement deterministic overlay merge in evidence path | **COMPLETE** | `runtime/ask_service/dirty_buffer_overlay.py` applied on v0/v1 ask paths with deterministic matching + regression tests |
| D4 | Extend explain_debug grounding with overlay-aware selected-file content | **COMPLETE** | Overlay-aware bundle content reaches `explain_debug` on v0/v1 ask paths; grounding clue regressions added (`test_reasoner_explain_debug_prompt.py`, `test_ask_service.py`, `test_ask_v1_ingest.py`) |
| D5 | Add response metadata and truthfulness notes | **COMPLETE** | Ask metadata now exposes `dirty_buffer_overlay` stats; plan notes report malformed/no-op overlay payload handling |
| D6 | Expand regression suite (unit + scenario) | **COMPLETE** | Added v0/v1 schema + overlay + grounding regressions across `test_ask_service.py`, `test_ask_v1_ingest.py`, `test_reasoner_explain_debug_prompt.py` |
| D7 | Baseline safety verification (`motadata_behavior_verify.py`) | **COMPLETE** | `runtime/.run/motadata_behavior_validation.CANDIDATE.L57_DIRTY_BUFFER_D7.json` (`all_pass=true`), baseline note recorded against SHA `ea9e805` |
| D8 | Charter closure report | **COMPLETE** | `docs/validation/L57_DIRTY_BUFFER_CHARTER_CLOSURE_REPORT.md` with commands, pass counts, artifact path, and before/after deltas |

---

## 6. Execution order

Recommended order:
1. D1-D2 (contract + fixtures first)
2. D3-D5 (behavior + observability)
3. D6 (regressions)
4. D7 (baseline verification)
5. D8 (closure decision)

---

## 7. Evidence and reporting

- Scenario pack: `docs/validation/l57_dirty_buffer_scenarios.v1.json`
- Closure report: `docs/validation/L57_DIRTY_BUFFER_CHARTER_CLOSURE_REPORT.md`
- Target contract surfaces: `runtime/ide/schemas/ask_request.v0.1.schema.json`, `runtime/ide/schemas/ask_request.v1.0.schema.json`
- Target runtime paths: `runtime/ask_service/handlers.py`, `runtime/ask_service/v1_ingest.py`, `runtime/ask_service/reasoner.py`
- Maintenance discipline: `docs/validation/POST_CLOSURE_MAINTENANCE.md`

All milestone claims under this charter must include:
- commit SHA
- exact pytest command(s)
- pass/fail counts
- baseline comparison note vs §5 policy

---

## 8. Decision policy

- If D7 fails (baseline regression), freeze and rollback charter changes until parity is restored.
- If overlay behavior improves one path but weakens explain-debug honesty, prefer truthful insufficiency over speculative analysis.
- If plugin payload contract is ambiguous, keep parser conservative and document unresolved edge cases.

---

*This charter is intentionally narrow: improve live-buffer correctness without reopening baseline architecture.*
