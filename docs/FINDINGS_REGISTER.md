# FINDINGS_REGISTER — execution-grounded review

**Scope:** Repo review using **routes** (`runtime/plan_gate_service/app.py`), **CLI** (`runtime/scripts/motadata_behavior_verify.py`), **tests** (`runtime/tests/`, `runtime/layer5/tests/`), and **tracker** (`docs/LIVE_ROADMAP_TRACKER.md`). **No code changes** in this pass.

---

## A. High-confidence truths

1. **Plan-Gate HTTP is the real integration spine for the slice** — `app.py` dispatches `/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute` to documented handlers (`handlers.py`, `ask_service`, `execute_service`). **Proven by reading source.**

2. **Evidence-first Ask is implemented as export → `/v1/ask`** — verifier builds `ask_request.v1.0` with bundle from `POST /v1/export_evidence`. **Proven by `motadata_behavior_verify.py` and `verify_ask_path.sh`.**

3. **Execute path uses `runtime/plangate` + sandbox**, not the HTTP stub’s `stub_decide` — `execute_service/handlers.py` imports `PlanGateService`, `SandboxExecutor`, etc. **Proven by imports.**

4. **Two different `LoopController` implementations exist** — `runtime/loop/loop_controller.py` (Stage 3) vs `runtime/orchestrator/loop_controller.py` (M3.1 matrix). Both have tests; **neither** is the other. **Proven by grep + test files.**

5. **Tracker closure (B1–B7, Action 14)** is the right **program** authority for “what shipped” — aligns with artifact dirs under `docs/validation/`. **Proven by tracker text.**

6. **`runtime/obs/` is Stage 3 ledger-only** — imported by `Stage3LoopController`, not a duplicate of `runtime/observation/`. **Proven by imports.**

---

## B. Execution gaps

| Gap | Severity | Detail |
|-----|----------|--------|
| **v0 Ask not the primary `motadata_behavior_verify.py` “query” check** | Low | Verifier emphasizes v1 evidence path; v0 still **exists** and is **tested** elsewhere — risk is **assuming CLI = full dual-path matrix** without reading verifier |
| **Stage 3 not on Plan-Gate HTTP** | Medium (clarity) | **Not a bug** — tracker calls IDE E2E follow-on; newcomers may expect `/v0/agent` or loop on HTTP |
| **`archive/legacy_runtime_rag/` validation vs slice** | Medium | Large tree; **not** exercised by `motadata_behavior_verify.py` — **parallel** stack per audit |
| **End-to-end “one pytest”** | Low | No single test runs Context Layer + GPU + full IDE; **closure** uses **layered** artifacts instead |

---

## C. Repo bloat / dead-weight candidates

| Item | Assessment | Action |
|------|------------|--------|
| `archive/legacy_runtime_rag/` | **Archived** (2026-04-14); **off** Plan-Gate CLI slice | **RETIRED** from `runtime/`; optional revival for experiments only |
| `runtime/plan_gate_stub/` | Small; **shared** with service | **KEEP** — protocol tests |
| `AskClient.kt` (if still unused) | **DEAD_CANDIDATE** per audit | **NEEDS_CONFIRMATION** via `rg` before delete |
| Duplicate runbooks (IDE + CLI) | Doc overlap | **Consolidate** reading order to `MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md` + matrices |

---

## D. Risky ambiguities

1. **`plan_gate_service` vs `plangate`** — Both “Plan-Gate” in name; **HTTP** vs **in-process** gate. Misrouting operators to wrong layer is a **real** failure mode.

2. **Two loop controllers** — Name collision; “the loop” in conversation may mean orchestrator or Stage 3.

3. **`observation` × 3** — Root `observation/`, `runtime/observation/`, `runtime/obs/` — **three** concepts; **not** interchangeable.

4. **“Tests pass” ≠ “HTTP slice”** — Many tests cover **authority**, **sandbox**, **migration** paths that are **not** the same as `motadata_behavior_verify.py`.

5. **Plugin closed vs CLI-first** — Tracker **B3** closed for MVP; **this pass** still treats **plugin proof as deferred** — not contradictory if labeled clearly.

---

## E. Recommended next actions (ranked)

1. **Add a one-line banner** to `runtime/README.md` (or pointer) listing **HTTP entry** vs **loop variants** — reduces onboarding errors (**doc-only**).

2. **Optional: extend `motadata_behavior_verify.py` or scenarios JSON** with an explicit **v0 Ask** row if dual-path regression must be **one command** (**code change** — outside this pass).

3. **grep audit** for `AskClient.kt` and dead Kotlin entrypoints — **DELETE_CANDIDATE** only after confirmation.

4. **Keep** `SCENARIO_CODE_EXECUTION_MAP.md` updated when **new** HTTP routes are added to `app.py`.

5. **Treat `archive/legacy_runtime_rag/`** as **explicitly non-canonical** for JetBrains slice in onboarding until product decision wires it.

---

## Verdict (sharp)

| Question | Answer |
|----------|--------|
| Is the repo **empirically** understandable? | **Much more so** if readers use **HTTP router + verifier + tracker** — not README alone. |
| What still **ambiguous**? | **Orchestrator vs Stage 3 loop**; **three observation trees**; **rag** vs **layer5** roles. |
| What to review next? | **Branch alignment** (tracker integration branch vs `main`); **root README** Layer-3/4 lines vs tracker; optional **v0** CLI scenario. |
