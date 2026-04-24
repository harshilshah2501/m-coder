# Plan + Multi-step Code Reasoning Solidification — Discovery

Date: 2026-04-24  
Branch: `plan-code-reasoning-solidification`  
Status: **discovery only** (touchpoint map + implementation plan; no product behavior change in this commit)

## 1) Phase goal (from program brief)

Move from strong **Ask / Debug / Investigate** understanding to a **governed** path:

```text
Ask / Debug / Investigate → Plan → Multi-step Code reasoning → Code proposal / bounded execution
```

**Principles:** plan first, step-wise reasoning, code only when bounded and approved — not an unconstrained “agent writes code” loop.

** Preconditions already met:** Assist v2 HTTP deploy gate is green (grounded Ask, weak Ask omission, Debug fail-closed, graph preflight). Contract and gate artifacts live under `docs/validation/ASSIST_V2_*` and `runtime/scripts/assist_v2_http_deploy_gate.py`.

**Strict non-goals for this phase (unchanged):** no plugin expansion, no model switch, no autonomous execution, no broad agent loop, no multi-file patch generation without explicit plan approval posture, no retrieval rewrite.

---

## 2) Target vs current — honest gap summary

| Target capability | Current repo reality (high level) |
|-------------------|-----------------------------------|
| Rich **Plan contract** (intent, files, boundaries, risk, evidence requirements, allow/forbid, approval posture) | **`plan_summary`** on Ask is **minimal schema**: `steps[]` (strings, 1–10) + optional `notes[]` in `plan_only_response.v0.1` — good for Plan-Only posture, **not** a full planning artifact. |
| **Plan validation pack** (safe doc, small patch, risky config, refusal, insufficient evidence) | **Partial:** `docs/validation/motadata_aiops_behavior_scenarios.v1.json` includes `plan_*` and `code_*` scenarios consumed by `runtime/scripts/motadata_behavior_verify.py`; coverage is **not** yet aligned with the richer contract in §1. |
| **Multi-step Code reasoning contract** (ordered steps before any patch text) | **Stage 3** (`Stage3LoopController`) implements a **bounded loop** (proposal → tool → revise) with envelopes, frames, and budgets — **offline / runtime-loop path**, not an HTTP-first “code reasoning JSON contract” exposed like Assist v2. **`authority_code_reasoning`** is **deterministic, no LLM**, registry-grounded hints — not multi-step reasoning trace. |
| **HTTP-level Plan/Code gate** (shape, refusal, boundedness, `execution=false`, ledger consistency) | **Assist v2 gate** covers **Ask/Debug/investigate + graph** only. **No** sibling script yet that validates enriched Plan payloads + code-proposal surfaces over **`POST /v1/ask`** or a dedicated Plan/Code endpoint. **`POST /v0/plan`** returns **decision_response.v0.1** (CI gate); different surface from v1 Ask `plan_summary`. |

Conclusion: the codebase has **strong governance primitives** (Plan-Gate postures, execute path, Stage 3 loop, behavior verifier) but **fragmented “Plan” and “Code” product contracts** across v0 plan, v1 ask `plan_summary`, execute, and Stage 3. Solidification means **unifying and freezing** intent-shaped artifacts and **adding gates** without smashing those layers together in one shot.

---

## 3) Touchpoint map (where work lands)

### 3.1 HTTP and services

| Location | Responsibility |
|----------|----------------|
| `runtime/plan_gate_service/app.py` | Routes: `/v0/plan`, `/v0/execute`, `/v1/ask`, health, logging. **Primary integration point** for any new HTTP validation or future Plan/Code read surfaces. |
| `runtime/plan_gate_service/handlers.py` | `handle_plan_request` → `stub_decide` + spool artifacts; returns **decision_response**. |
| `runtime/ask_service/v1_ingest.py` (and related) | Builds **`plan_only_response.v0.1`** with `plan_summary`, evidence bundle, Assist v2 projections. |
| `runtime/execute_service/handlers.py` | **M4.1** execute: normalize → deterministic guard → **PlanGateService.evaluate** → sandbox / ledger; rejects `plan_gate_*` overrides by default on live HTTP. |

### 3.2 Governance and decisions

| Location | Responsibility |
|----------|----------------|
| `runtime/plangate/plangate_service.py` | `PlanGateService.evaluate` — deterministic rule posture (`refuse`, `defer`, `bounded_allow`, `safe_execute`). |
| `runtime/plangate/plangate_decision.py` | `PlanGateDecision`; **`may_execute`** only if `safe_execute`. |
| `runtime/plangate/judge_gate.py`, `authority_validator.py`, `irreversibility_detector.py` | Composed decision path (documented in tracker §M3.3). |
| `runtime/plan_gate_stub/` | Stub / legacy plan gate helpers (still referenced in docs). |

### 3.3 Schemas (contract freeze targets)

| Schema | Role today |
|--------|------------|
| `runtime/ide/schemas/plan_only_response.v0.1.schema.json` | Ask response: **`plan_summary.steps`** required; **`execution`** const false; **`governance_posture`** PLAN_ONLY. **Primary candidate to extend or version** (e.g. `v0.2`) for richer Plan fields — requires explicit compatibility policy. |
| `runtime/ide/schemas/decision_response.v0.1.schema.json` | `/v0/plan` outcome; used by `runtime/ci_gate/cli.py`. |
| `runtime/ide/schemas/ask_request.v1.0.schema.json` | Ask ingress. |
| Execute / ledger schemas under `runtime/ide/schemas/` | Execution intent, ledger hooks — align “code proposal” and **execution=false** story with execute path. |

### 3.4 Stage 3 loop (multi-step runtime, not yet IDE-wired)

| Location | Role |
|----------|------|
| `runtime/loop/loop_controller.py` | **`Stage3LoopController`**: pre-loop Plan-Gate, iteration budget, `loop_context_frame`, proposal validation, tool execution, ledger events, terminal outcomes (`refused`, `blocked`, `failed`, success paths). |
| `runtime/loop/state_machine.py`, `decision_engine.py`, `runtime/tools/executor.py` | Transitions, policy, tool bounds. |
| `runtime/state/validators.py` | Task envelope, loop frame, final response validation — **reuse patterns** for any new multi-step code reasoning envelope. |
| `runtime/tests/test_stage3_loop.py` | Rich behavioral tests — **reference implementation** for budgets and refusal paths. |

**Important tracker truth:** **IDE → `Stage3LoopController` E2E** remains **follow-on** (`docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md` §7). This phase can **solidify contracts and HTTP gates** without waiting for IDE wiring, but must **not** silently conflate “Stage 3 pytest green” with “product Plan/Code HTTP complete.”

### 3.5 Orchestrator loop (M3.1)

| Location | Role |
|----------|------|
| `runtime/orchestrator/loop_controller.py` | **`LoopController`** — transition matrix, governance_to_context, validated_to_sandbox with PlanGateService; **different** from Stage 3 product loop. |

### 3.6 Authority / code reasoning (Layer 5, deterministic)

| Location | Role |
|----------|------|
| `runtime/layer5/authority/authority_code_reasoning.py` | Intent classification (`explore` / `debug` / `modify`), target extraction from authority — **feeds synthesis**, not a full multi-step trace. |
| `runtime/ask_service/authority_synthesis.py` | Imports authority code reasoning for Ask path. |

### 3.7 Validation and CI

| Location | Role |
|----------|------|
| `docs/validation/motadata_aiops_behavior_scenarios.v1.json` | Plan/code **scenarios** (`plan_api_layer_change_shadow`, `plan_refusal_or_bounded_approval_*`, `code_safe_echo_probe`, `code_bounded_multistep_probe`, …). |
| `runtime/scripts/motadata_behavior_verify.py` | Deep slice / scenario driver; **extend** for new Plan contract checks. |
| `runtime/ci_gate/cli.py` | POSTs **plan_request** to `/v0/plan` — useful pattern for **additional** HTTP gates. |
| `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md` | Canonical verification commands. |

---

## 4) Mapping to your five immediate action items

| # | Action item | Discovery finding — likely implementation locus |
|---|-------------|--------------------------------------------------|
| 1 | **Freeze Plan contract** | New doc **`docs/validation/PLAN_CONTRACT_FREEZE_V1.md`** (or similar) + schema bump or additive fields under `plan_summary` / new `plan_contract` object with **explicit** `additionalProperties` policy; align with `PLAN_ONLY` + `execution=false`. |
| 2 | **Plan validation pack** | Extend **`motadata_aiops_behavior_scenarios.v1.json`** + verifier expectations; possibly add **`runtime/tests/test_plan_contract_*.py`** for pure JSON-schema + invariants. |
| 3 | **Multi-step Code reasoning contract** | Design **`code_reasoning_trace.v0.1`** (name TBD) — either nested under Ask when in “code reasoning” mode **or** separate internal envelope mirrored to diagnostics; align fields with **Stage3** frame concepts (`iteration_index`, `remaining_budget`, proposal refs, tool refs) without copying the whole loop into Ask. |
| 4 | **Loop/context safeguards** | **Reuse Stage 3 parameters** as source of truth: `attempt_budget`, tool policy, evidence ref closure, max steps — document caps in contract doc; enforce in server-side validation for any new payload. |
| 5 | **HTTP-level Plan/Code gate** | **Delivered:** `runtime/scripts/plan_code_http_deploy_gate.py` + tests + `docs/validation/PLAN_CODE_HTTP_RUNTIME_GATE.md` — `/v0/plan`, `/v0/execute`, `/v1/ask` observational checks; optional `--ledger-path`; **no** new Ask payload fields required. |

---

## 5) Recommended implementation sequence (lanes → commits)

Work **small PR-sized slices** on `plan-code-reasoning-solidification`; merge to `main` only with tests + doc + optional gate artifact policy.

1. **Lane 1 — Plan contract/spec (docs + schema draft)** — **Delivered:** `docs/validation/PLAN_CONTRACT_FREEZE_V1.md` (additive `plan_contract`; no `plan_only_response` bump until criteria in that doc are met).

2. **Lane 2 — Plan validation scenarios** — **Delivered (offline):** four `plan_contract_validate` rows in `motadata_aiops_behavior_scenarios.v1.json`; structural + category checks in `runtime/plan_contract/v1_validate.py`; `motadata_behavior_verify.py` integration + graph bypass when **only** those scenarios are selected. **`/v1/ask` does not emit `plan_contract` yet.**

3. **Lane 3 — Multi-step Code reasoning design** — **Delivered (design-only):** `docs/validation/CODE_REASONING_CONTRACT_DESIGN_V1.md` (`code_reasoning_trace.v1`, step kinds, bounds, `patch_intent.v1`, terminal/refusal, ledger hook names, handoff rules from `plan_contract`). **No** runtime or HTTP changes.

4. **Lane 4 — Code reasoning validation fixtures** — **Delivered (offline):** `code_reasoning_trace_validate` scenarios + `runtime/code_reasoning/v1_validate.py` + verifier wiring (see `CODE_REASONING_CONTRACT_DESIGN_V1.md` §10). **HTTP / deploy gate** for Code reasoning remains **next** (separate slice from offline fixtures).

5. **Lane 5 — Docs/tracker / phase report**  
   - Phase report `docs/validation/PLAN_CODE_REASONING_SOLIDIFICATION_REPORT.md` on closure (optional batch).  
   - Tracker rows updated incrementally with Lanes 1–4.

6. **Lane 6 (next engineering)** — HTTP/runtime **Plan+Code reasoning deploy gate** (separate from offline fixtures).

**Dependency order:** Lanes 1–4 are sequential for contract truth; HTTP/runtime gate (Lane 6) only after offline validators stay green.

---

## 6) Risks and guardrails

- **Schema drift:** `plan_only_response.v0.1` is consumed by the plugin contract path — any change needs **versioning or additive-only** policy matching Assist v2 freeze lessons.  
- **Two “Plan” meanings:** **`/v0/plan` decision** vs **Ask `plan_summary`** — docs and gates must name which surface is under test.  
- **Execution safety:** HTTP gates must **never** turn on execution; use read-only probes and existing **`execution=false`** invariants.  
- **Scope creep:** multi-file patch generation and autonomous loops stay **explicitly out of scope** until this phase’s contract and gates are green.

---

## 7) References (quick index)

- Assist v2 freeze + gate: `docs/validation/ASSIST_V2_API_CONTRACT_FREEZE_V1.md`, `runtime/scripts/assist_v2_http_deploy_gate.py`  
- Ask response schema: `runtime/ide/schemas/plan_only_response.v0.1.schema.json`  
- Stage 3: `runtime/loop/loop_controller.py`, `docs/validation/STAGE3_BURN_IN_REPORT.md`, `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md`  
- Behavior scenarios: `docs/validation/motadata_aiops_behavior_scenarios.v1.json`, `runtime/scripts/motadata_behavior_verify.py`  
- Execute + Plan-Gate: `runtime/execute_service/handlers.py`, `runtime/plangate/plangate_service.py`

---

## 8) Conclusion

The repo **already contains** the right **governance spine** (Plan-Gate postures, execute gating, Stage 3 bounded loop, behavior verifier). The solidification phase is primarily **contract design + validation expansion + HTTP gate**, aligned with Ask/Assist v2 **without** merging unrelated work (plugin, model, retrieval). Next coding step after this discovery: **Lane 1 spec PR** (markdown + schema proposal + ingest stub or feature flag if needed).
