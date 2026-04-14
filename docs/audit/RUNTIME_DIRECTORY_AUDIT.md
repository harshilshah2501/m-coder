# `runtime/` directory audit — consistency, relevance, efficiency

**Scope:** [`runtime/`](../../runtime/) only (≈340 `.py` files, 165 dirs; excludes `__pycache__`).  
**Audit date:** 2026-04-13 · **Closure:** 2026-04-14 · **Findings pass:** 2026-04-14 (§6 strikethroughs + §8)  
**Related:** [REPO_LAYOUT_INVENTORY.md](REPO_LAYOUT_INVENTORY.md), [RUNTIME_REORG_CANDIDATES.md](RUNTIME_REORG_CANDIDATES.md), [TEST_COVERAGE_MATRIX.md](TEST_COVERAGE_MATRIX.md), [BATCH_A_GOVERNED_RUNTIME_CORE.md](BATCH_A_GOVERNED_RUNTIME_CORE.md)

---

## 1. Executive summary

`runtime/` is **large but structurally purposeful**: a **governed core** (`plangate`, `orchestrator`, `execute_service`, `sandbox`, `integrity`, `ask_service`, `context_layer_service`, `layer5`) sits beside **compatibility surfaces** (`plan_gate_service`, `plan_gate_stub`), **support protocols** (`shadow`, `ide` schemas, `ci_gate`), and **heavier subsystems** (`rag`, `observation`, `layer5`).  

**Consistency** is strongest where **M4/M3.3/L5** docs match code (`execute_service`, `plangate`). **PlanGate** naming is mapped in README + package `__init__.py` (R-1). **Two loop controllers** remain a **human** distinction (§4.2) — documented in README.  

**Relevance:** Most lines sit in **layer5**, **rag**, **observation**, and **tests**; the **vertical slice** does not require every line of `rag_api.py` on every request.  

**Efficiency:** Co-locating **`runtime/tests/`** inside `runtime/` is a **large test tree** next to production code; a few **top-heavy files** (>500 LOC) drive maintenance cost. No widespread `TODO`/`FIXME` noise in a quick scan.

**Post-audit (2026-04-14):** Dead **`runtime/intake/`** removed; **`runtime/README.md`** and **`runtime/obs/README.md`** updated; repo-level **hygiene** and **inventory** alignment recorded in §8.

---

## 2. Scale snapshot

| Metric | Value |
|--------|--------|
| Python files (approx.) | 340 |
| Top-level packages | 38 |
| Largest non-test `.py` (lines) | `rag/src/api/rag_api.py` (~2490) |
| Co-located tests | `runtime/tests/` (~63 `.py` files) |

---

## 3. Relevance tiers (for review / onboarding)

| Tier | Packages (representative) | Review priority |
|------|----------------------------|-----------------|
| **A — Core governed path** | `plangate/`, `integrity/`, `orchestrator/`, `execute_service/`, `sandbox/`, `ledger/` (usage), `state/`, `loop/` (Stage 3), `tools/`, `obs/` | **Highest** — execution honesty, gate-before-sandbox |
| **B — L5 + Ask + context** | `layer5/`, `ask_service/`, `context_layer_service/`, `context/`, `ask_validation/` | **High** — evidence, routing, export |
| **C — Observability** | `observation/` | **High** for trace/correlation; large files |
| **D — RAG** | `rag/` | **Medium** — workspace retrieval; not every IDE path hits full API surface |
| **E — Compatibility / CI** | `plan_gate_service/`, `plan_gate_stub/`, `ci_gate/` | **Medium** — do not confuse with `runtime/plangate/` |
| **F — Protocol / optional** | `shadow/`, `shadow_runner/`, `emulator/`, `replay/`, `ide/` (schemas) | **Lower** unless changing shadow/demo |
| **G — Thin / config** | `execute_service/` (2 py), `policies/`, `schemas/` (JSON), `config/` (env templates) | **Contextual** |
| **H — Removed** | ~~`intake/`~~ — **deleted** 2026-04-14 (orphan cache only) | — |

---

## 4. Consistency

### 4.1 Plan-Gate naming (intentional but dense)

| Symbol / path | Role |
|----------------|------|
| [`runtime/plangate/PlanGateService`](../../runtime/plangate/plangate_service.py) | **M3.3 execution gate** — used by orchestrator + execute_service |
| [`runtime/plan_gate_service/`](../../runtime/plan_gate_service/) | **HTTP** PlanRequest v0.1 → DecisionResponse; uses **stub** `stub_decide` from `plan_gate_stub` |
| [`runtime/plan_gate_stub/PlanGate`](../../runtime/plan_gate_stub/plan_gate.py) | Legacy **class** name for stub/emulator path; not the M3.3 service |
| [`runtime/plan_gate_service/app.py` `PlanGateHandler`](../../runtime/plan_gate_service/app.py) | HTTP handler class |

**Assessment:** Architecturally **consistent** (stub feeds HTTP service; real gate is `plangate`). **Risk** is **human confusion** in PRs and audits — mitigated by [`runtime/README.md`](../../runtime/README.md) (*Execution gate*) plus package docstrings in `plangate/`, `plan_gate_service/`, `plan_gate_stub/` (R-1).

### 4.2 Two “loop controllers”

| Class | Path | Role |
|-------|------|------|
| `LoopController` | [`orchestrator/loop_controller.py`](../../runtime/orchestrator/loop_controller.py) | Transition matrix + `validated_to_sandbox` + plangate |
| `Stage3LoopController` | [`loop/loop_controller.py`](../../runtime/loop/loop_controller.py) | Stage 3 state machine + tool loop |

**Assessment:** **Different products** in one repo; naming overlap is **consistent** with docs (IDE demo vs Stage 3 burn-in). Flag any new third “loop” name.

### 4.3 `obs/` vs `observation/`

- **`runtime/obs/`** — minimal **Stage 3 ledger** (`Stage3Ledger`, `LedgerEvent`) used by [`loop/loop_controller.py`](../../runtime/loop/loop_controller.py).
- **`runtime/observation/`** — full **trace, reconciliation, metrics, GREG**, etc.

**Assessment:** **Abbreviation vs full name** — mitigated by [`runtime/obs/README.md`](../../runtime/obs/README.md), cross-links in **`runtime/obs/__init__.py`** and **`runtime/observation/__init__.py`**, and R-2 closure in §6.

### 4.4 `runtime/README.md` vs tree

The **intro** still highlights **rag** and **`.config`** as the main entry points. **Post-audit (2026-04-14):** the same file now includes an **execution gate** table (plangate vs HTTP stub vs plan_gate_service), a **package map** (layer5, ask, context layer, assist_layer, obs vs observation, etc.), and links to this audit and [RUNTIME_REORG_CANDIDATES.md](RUNTIME_REORG_CANDIDATES.md). **Remaining gap:** optional polish to align the opening bullets with the deeper map (low priority).

---

## 5. Efficiency (size + coupling)

### 5.1 Largest production modules (LOC, approximate)

Non-test Python files exceeding **~450 LOC** (indicative maintenance hotspots):

- `rag/src/api/rag_api.py` — **dominant**; single-file API surface
- `layer5/retrieval/lexical.py`
- `loop/loop_controller.py`, `orchestrator/loop_controller.py` — expected complexity
- `ask_validation/harness.py`
- `observation/reconciliation.py`, `collapse_vectors.py`, `greg_escalation.py`, `runtime_metrics.py`
- `execute_service/handlers.py`, `ask_service/handlers.py`
- `plan_gate_service/app.py`, `context_layer_service/app.py`

**Assessment:** **No smell of “dead mega-file”** — but **rag** and **observation** concentrate **LOC**; refactors should stay **surgical** (per project rules).

### 5.2 Tests inside `runtime/`

- **`runtime/tests/`** is **large** and **appropriate** for integration tests, but **mixes** many subsystems in one tree.
- **Efficiency:** repo-root [`pytest.ini`](../../pytest.ini) registers **`slow`** and **`integration`** markers for optional tiered CI (`pytest -m "not slow"`); applying marks to individual tests remains **optional** (R-5).

### 5.3 Dependency fact

- **`plan_gate_service`** imports **`runtime.plan_gate_stub.rules.stub_decide`** — **explicit reuse** of stub logic for HTTP service. **Consistent**; alternative would duplicate rules (worse).

### 5.4 Empty / near-empty

- **`runtime/schemas/`** — JSON only (correct; not “empty”).
- **`runtime/intake/`** — **Removed** (2026-04-14): had no sources, only `__pycache__`. See [RUNTIME_REORG_CANDIDATES.md](RUNTIME_REORG_CANDIDATES.md).

---

## 6. Findings table (actionable)

Strikethrough = **done** for this pass (see §8 for evidence).

| ID | Category | Severity | Finding |
|----|----------|----------|---------|
| R-1 | Consistency | P2 | ~~Multiple “PlanGate*” names — keep README/operator docs as canonical map; new code should not introduce a fourth gate name without doc.~~ **Done:** [`runtime/README.md`](../../runtime/README.md) table + docstrings in [`plangate/__init__.py`](../../runtime/plangate/__init__.py), [`plan_gate_service/__init__.py`](../../runtime/plan_gate_service/__init__.py), [`plan_gate_stub/__init__.py`](../../runtime/plan_gate_stub/__init__.py) (2026-04-14). |
| R-2 | Consistency | P2 | ~~`obs/` vs `observation/` — abbreviate in one place or document cross-reference in both `__init__.py` files.~~ **Done:** [`obs/__init__.py`](../../runtime/obs/__init__.py) ↔ [`observation/__init__.py`](../../runtime/observation/__init__.py) (2026-04-14). |
| R-3 | Relevance | P3 | ~~`runtime/README.md` under-lists hot packages.~~ **Done:** Package map + gate table (2026-04-14); intro bullets still minimal (acceptable). |
| R-4 | Efficiency | P2 | `rag_api.py` + large `observation/*` files — natural owners for any **split-only-when-needed** refactors. *(Ongoing guidance — no split in this pass.)* |
| R-5 | Efficiency | P3 | ~~Low pytest marker usage — optional CI tiering later.~~ **Done:** [`pytest.ini`](../../pytest.ini) registers `slow` / `integration`; marking tests is optional. |
| R-6 | Consistency / hygiene | P3 | ~~`runtime/intake/` orphan dir.~~ **Done:** Removed 2026-04-14 (orphan `__pycache__` only). |

**None of the above** reopens closed milestones unless paired with **a failing test or contract drift** (per tracker discipline).

---

## 7. Recommended next steps (remaining)

1. ~~**Optional (R-2):** Cross-reference `obs/` ↔ `observation/` in both packages’ `__init__.py`.~~ **Done** (2026-04-14).
2. ~~**Optional (R-5):** Pytest markers for CI tiering.~~ **Convention:** [`pytest.ini`](../../pytest.ini) — **adopt** `@pytest.mark.slow` / `integration` on heavy tests when convenient.
3. **Optional (R-4):** Surgical splits of `rag_api.py` / large `observation/*` only when maintenance cost justifies a dedicated refactor PR.
4. **Keep** Batch A ledger follow-up (A-1) as **runtime/orchestrator** issue, not a layout issue — see [BATCH_A_GOVERNED_RUNTIME_CORE.md](BATCH_A_GOVERNED_RUNTIME_CORE.md).
5. **Re-run** this audit after **major** refactors (e.g. RAG split, observation module split).

---

## 8. Post-audit closure (output)

Actions taken **after** this audit to align the tree and docs with §3–§6. Full hygiene table: [RUNTIME_REORG_CANDIDATES.md § Done](RUNTIME_REORG_CANDIDATES.md#done-hygiene).

| Area | Outcome |
|------|---------|
| **`runtime/intake/`** | Removed — no sources, only orphan cache; see R-6. |
| **`runtime/README.md`** | Execution gate table + primary package map + audit links. |
| **`runtime/obs/README.md`** | Added — Stage 3 scope + pointer to `observation/`. |
| **Repo hygiene (non-`runtime/`)** | Removed scratch `git_diff.txt`, `motadata_context_layer.egg-info/`, local `packaging/motadata-context-layer/` `.venv*` / `dist/` / `build/`; **`.gitignore`** dedupe for `golden_exemplars` dataset lines. |
| **Layout inventory** | `hostB_proof_pack/` archived under [`archive/hostB_proof_pack/`](../../archive/hostB_proof_pack/) (see [REPO_LAYOUT_INVENTORY.md](REPO_LAYOUT_INVENTORY.md)). |
| **Sanity** | `python3 -m pytest runtime/tests/test_plangate_integration.py` — **14 passed** at closure. |
| **R-1 / R-2 / R-5** | Package docstrings (Plan-Gate trio, `obs` ↔ `observation`); repo [`pytest.ini`](../../pytest.ini) marker registration. |

**Deferred:** R-4 surgical splits; mass move of `runtime/tests/`; merge of plan_gate packages; optional renames — see [RUNTIME_REORG_CANDIDATES.md](RUNTIME_REORG_CANDIDATES.md).

---

## References

- [`runtime/README.md`](../../runtime/README.md)
- [`docs/audit/RUNTIME_REORG_CANDIDATES.md`](RUNTIME_REORG_CANDIDATES.md)
- [`docs/LIVE_ROADMAP_TRACKER.md`](../LIVE_ROADMAP_TRACKER.md)
- [`docs/ARCHITECTURE_4_LAYER.md`](../ARCHITECTURE_4_LAYER.md)
