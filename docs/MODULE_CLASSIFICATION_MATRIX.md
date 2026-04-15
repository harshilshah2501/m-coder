# MODULE_CLASSIFICATION_MATRIX — major paths by execution relevance

**Rules:** Classification follows **imports, HTTP wiring, tests, CLI scripts**, and **product slice** docs — not directory size. **UNKNOWN** used where evidence is incomplete without running full CI locally.

**Tags:** Each row: **Classification** + **Product Slice** (`IN_PRODUCT_SLICE` | `OUT_OF_PRODUCT_SLICE` | `DEFERRED_INTEGRATION`).

---

## Matrix

| Path / module | Role | Classification | Product Slice | Execution evidence | Validation evidence | Recommended action | Notes |
|---------------|------|----------------|---------------|---------------------|----------------------|-------------------|-------|
| `runtime/plan_gate_service/` | HTTP daemon: `/v0/plan`, `/v0/ask`, `/v1/ask`, `/v0/execute`, health | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | `app.py` routes to ask/execute; **cli** verifier | pytest HTTP (`test_ask_v1_ingest.py`), verifier JSON | **KEEP_AS_CANONICAL** | Entry point for slice |
| `runtime/plangate/` | In-process `PlanGateService`, pre-gate, authority — **sandbox/execute chain** | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | Imported by `execute_service/handlers.py`, orchestrator | `test_plangate_*.py`, `test_execute_service.py` | **KEEP_AS_CANONICAL** | **≠** `plan_gate_service/` |
| `runtime/plan_gate_stub/` | Shared `stub_decide`, CLI pressure-test | **ACTIVE_COMPATIBILITY** | **IN_PRODUCT_SLICE** (plan/spool) | Used by `plan_gate_service/handlers.py` | Plan tests | **KEEP_AS_COMPATIBILITY** | Not user “execute” semantics |
| `runtime/ask_service/` | v0/v1 Ask, planner, reasoner, Explain/Debug | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | Called from `plan_gate_service/app.py` | Many `test_ask_*.py` | **KEEP_AS_CANONICAL** | |
| `runtime/context_layer_service/` | `POST /v1/export_evidence` | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | Standalone HTTP app | `test_context_layer_service.py`, verifier | **KEEP_AS_CANONICAL** | |
| `runtime/layer5/` | Index, lexical retrieval, evidence models, authority adapters, **audit/L5.8** | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | Export + `/v1/ask` consumes bundles | `test_l58_*.py`, B1 artifacts | **KEEP_AS_CANONICAL** | Heart of evidence path |
| `runtime/execute_service/` | `/v0/execute` handler implementation | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | Wired in `plan_gate_service/app.py` | `test_execute_service*.py` | **KEEP_AS_CANONICAL** | |
| `runtime/loop/` | `Stage3LoopController`, Stage 3 state machine | **ACTIVE_CANONICAL** (component) | **IN_PRODUCT_SLICE** (feature) | Used by **`test_stage3_loop.py` only** (no default HTTP wire-up) | B7 artifacts, pytest | **KEEP_AS_CANONICAL** | **Passive** relative to Plan-Gate HTTP |
| `runtime/orchestrator/` | M3.1 `LoopController`, transitions, replay — **governed task loop** | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | `LoopController` in sandbox/task tests, `demo_governed_execution.py` | `orchestrator_test_suite.py`, `test_task_wiring.py` | **KEEP_AS_CANONICAL** | **Different lifecycle** from `runtime/loop/` |
| `runtime/context/` | Contracts, `ContextEngine` for v0 ask context | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | `ask_service.handlers` | `test_context_engine.py` | **KEEP_AS_CANONICAL** | |
| `archive/legacy_runtime_rag/` | RAG API, indexing (parallel; **retired** from `runtime/`) | **ARCHIVE** / parallel | **OUT_OF_PRODUCT_SLICE** | Code lives under `archive/`; **no** `from runtime.rag` in plan_gate trace | Tests under `archive/legacy_runtime_rag/tests/` | **ARCHIVE** (optional delete later) | Moved 2026-04-14 |
| `runtime/observation/` | Traces, metrics, reconciliation (full stack) | **ACTIVE_CANONICAL** (subsystem) | **PARTIAL** vs slice | Many `test_*runtime_metrics*`, drift tests | pytest | **KEEP_AS_SUPPORT** | Broader than HTTP demo |
| `runtime/obs/` | Stage 3 ledger only | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** (Stage 3) | Imported by `runtime/loop/loop_controller.py` | `test_stage3_loop.py` | **KEEP_AS_CANONICAL** | **≠** `observation/` |
| `runtime/assist_layer/` | Advisory augmentation on Ask path | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** (advisory) | `plan_gate_service/app.py` `_apply_assist_to_ask_payload` | `test_assist_layer_v1.py` | **KEEP_AS_CANONICAL** | Does not change query authority |
| `runtime/tests/` | Pytest tree | **PASSIVE_SUPPORT** | **IN_PRODUCT_SLICE** | N/A | N/A | **KEEP_AS_CANONICAL** | Proof surface |
| `observation/` (repo root) | Layer-4 CLI / packages | **PASSIVE_SUPPORT** | **OUT_OF_PRODUCT_SLICE** (slice centers runtime HTTP) | Separate entrypoints | Own README | **KEEP_AS_SUPPORT** | Confusable name |
| `ml/` | Layer-2 compilation, training | **PASSIVE_SUPPORT** | **OUT_OF_PRODUCT_SLICE** | Training jobs | Freeze certs, layer2 tests | **KEEP_AS_CANONICAL** (L2 line) | Not on hot HTTP path |
| `governance/` | L1 constitution | **PASSIVE_SUPPORT** | **IN_PRODUCT_SLICE** (doctrine) | Doctrine consumers | N/A | **KEEP_AS_CANONICAL** | |
| `packaging/motadata-context-layer/` | Installable context layer | **ACTIVE_CANONICAL** | **IN_PRODUCT_SLICE** | Wheel install on workspace host | Integration implied by B5 | **KEEP_AS_CANONICAL** | |
| `jetbrains-plugin/` | IDE client | **ACTIVE_CANONICAL** (shipping) | **DEFERRED_INTEGRATION** (proof) | Kotlin; calls HTTP | Plugin tests / manual; tracker B3 closed | **KEEP_AS_COMPATIBILITY** | **CLI/HTTP proof preferred** this pass |
| `archive/` | Historical spikes | **ARCHIVE** | **OUT_OF_PRODUCT_SLICE** | None hot | None | **ARCHIVE** | |
| `archive/workspace_intelligence/` | Old WI spikes | **ARCHIVE** | **OUT_OF_PRODUCT_SLICE** | — | — | **ARCHIVE** | Packaged L5 is under `runtime/layer5/` |
| `docs/validation/artifacts/` | Proof packs | **PASSIVE_SUPPORT** | **IN_PRODUCT_SLICE** (evidence) | Human + CI | Tracker references | **KEEP_AS_CANONICAL** | Not executable code |

---

## Naming confusion register (risk reduction)

| Ambiguity | Resolution |
|-----------|------------|
| `plan_gate_service` vs `plangate` | HTTP **vs** in-process gate — **both ACTIVE** on different edges (`app.py` vs execute/orchestrator) |
| `runtime/loop/loop_controller.py` vs `runtime/orchestrator/loop_controller.py` | **Stage 3** schema-driven loop **vs** M3.1 transition-matrix loop — **both tested**; **neither** equals the other |
| `runtime/obs/` vs `runtime/observation/` vs `observation/` | Stage3 ledger **vs** runtime trace stack **vs** root CLI — see `docs/README.md` |

---

## Dead-weight candidates (careful)

| Candidate | Verdict | Why not “delete” blindly |
|-----------|---------|---------------------------|
| `archive/legacy_runtime_rag/` | **Archived** parallel stack | Revive only with explicit product decision; ML eval scripts may still assume `localhost:8081` |
| `AskClient.kt` (if still present) | **DEAD_CANDIDATE** (per audit) | Confirm grep before removal — **NEEDS_CONFIRMATION** |
