# Nomenclature Audit

**Report date:** 2026-03-13  
**Canonical state reference:** [SYSTEM_CANONICAL_STATE_AUDIT.md](SYSTEM_CANONICAL_STATE_AUDIT.md)  
**Snapshot:** [SYSTEM_REPOSITORY_SNAPSHOT.json](SYSTEM_REPOSITORY_SNAPSHOT.json)

---

## 1. Scope

Audit milestone IDs (canonical M3.0–M3.18), runtime component names, directory names, document titles, and legacy vs canonical naming. Verify live docs use canonical IDs; legacy only in historical docs where justified; record naming inconsistencies precisely.

---

## 2. Canonical Naming Baseline

- **Layer-3 milestones:** M3.0 through M3.18 only (per LIVE_ROADMAP_TRACKER §4.3.1).
- **Live roadmap tables:** No M3.E0, M3.T0, M3X.* in live tables (tracker states this explicitly).
- **Mapping (from LAYER3_MILESTONE_NORMALIZATION_REPORT):** M3.E0→M3.0, M3.T0→M3.1, M3X.1→M3.10 … M3X.9→M3.18.

---

## 3. Legacy Naming Occurrences

| Location | Legacy label(s) | Classification |
|----------|-----------------|-----------------|
| `docs/runtime/RUNTIME_STATE_TRANSITIONS.md` | M3.E0, M3.T0 | Historical; doc describes state machine and emulator mapping. Preserved by design. |
| `README.md` | M3.E0, M3.T0 | Brief pointer to runtime; historical reference. |
| `docs/runtime/milestones/M3.3_PLAN_GATE_INTEGRATION.md` | M3.E0 | One sentence comparing emulator M3.E0 to M3.3; historical context. |
| `docs/runtime/verification/LAYER3_MILESTONE_NORMALIZATION_REPORT.md` | M3.E0, M3.T0, M3X.* | Mapping table legacy→canonical; reference doc only. |
| `runtime/emulator/__init__.py`, `authority.py`, `boundary.py`, `ledger.py` | M3.E0 in docstrings | Code docstrings; historical label for emulator. |
| `runtime/plan_gate_stub/plan_gate.py` | M3.E0 in module docstring | Same. |
| `runtime/shadow_runner/run_demo.py` | M3.E0 in comments/print | Same. |
| `runtime/tests/test_emulator_invariants.py` | M3.E0 in module docstring | Same. |

None of the above are in **live** roadmap tables or milestone status tables. They are historical or reference/mapping content.

---

## 4. Live-Doc Violations

- **LIVE_ROADMAP_TRACKER.md:** Uses only M3.0–M3.18 in §4.3.1 table and header. No M3.E0/M3X.* in live tables. **No violation.**
- **docs/runtime/milestones/*.md:** Titles use canonical IDs (e.g. M3.3_PLAN_GATE_INTEGRATION, M3.1_AGENT_LOOP_ORCHESTRATOR). M3.3 doc contains one historical M3.E0 mention (acceptable per plan).

**Verdict:** No live-doc violations. Live tracker and milestone tables use canonical IDs; legacy appears only where documented as historical.

---

## 5. Component Naming Findings

- **Runtime components:** SandboxExecutor, SandboxDriver, LoopController, PlanGateService, etc. — names align with docs and plan.
- **Directory names:** `runtime/`, `ml/`, `governance/`, `observation/` — lowercase; `docs/runtime`, `docs/governance` — consistent. Mixed-case only under docs (COMPILATION, CONTRACTS, OBSERVATION) and documented in structure audit.
- **Stage vs Phase:** Stage-1..Stage-8 (pipeline) vs Phase-1..Phase-6 (constitutional) separation is documented in ARCHITECTURE_4_LAYER and STAGE_LAYOUT_CANONICAL; no conflation in live tracker.

---

## 6. Pass/Fail Verdict

**PASS.** Live roadmap and milestone tables use only M3.0–M3.18. Legacy labels (M3.E0, M3.T0, M3X.*) appear only in historical or reference docs and in code docstrings for the emulator; LAYER3_MILESTONE_NORMALIZATION_REPORT and tracker state that historical is preserved. No naming violations in live docs.
