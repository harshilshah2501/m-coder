# Layer-3 — Comprehensive Runtime Enforcement Spec

**Entry point:** [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)

## Purpose

Layer-3 enforces constitutional judgment at execution time. It implements Phase-05 CODE semantics. Runtime consumes trained behavior and enforces it. **Runtime never redefines doctrine.**

**Directory:** `runtime/`

Deterministic runtime state machine semantics are defined in `docs/runtime/RUNTIME_STATE_TRANSITIONS.md` and the associated schemas in `runtime/state/schemas/`.

**Live program status:** [`LIVE_ROADMAP_TRACKER.md`](LIVE_ROADMAP_TRACKER.md) §2.1.1 · [`SYSTEM_TRUTH.md`](SYSTEM_TRUTH.md). **Layer-3 rollup:** **COMPLETE** (M3.0–M3.12 on `main`). Follow-on milestones **M3.13–M3.18:** tracker §4.3.1. **Slide PDF:** [`Layer-3_Runtime_Enforcement.pdf`](Layer-3_Runtime_Enforcement.pdf) is a visual snapshot only; authoritative text is this spec and linked contracts.

### Plan-Gate HTTP service vs in-process gate

- **HTTP API (production):** `runtime/plan_gate_service/` — Plan-Gate, Ask, and governed execute over HTTP (e.g. `POST /v0/plan`, `POST /v0/ask`, `POST /v1/ask`, `POST /v0/execute`, `GET /healthz`, `GET /version`). See [`SYSTEM_TRUTH.md`](SYSTEM_TRUTH.md) §3 and [`docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md`](audit/END_TO_END_SYSTEM_AUDIT_REPORT.md).
- **In-process library:** `runtime/plangate/` — authority validator, irreversibility detector, judge gate; consumed by execute and loop paths. **Not** the same artifact as the HTTP daemon; do not conflate the two (see [`ARCHITECTURE_4_LAYER.md`](ARCHITECTURE_4_LAYER.md) Layer-3 notes).

### Evidence path (Layer-5 boundary)

Workspace evidence is assembled **before** Plan-Gate evaluation: Context Layer `POST /v1/export_evidence`; frozen bundle schema **`layer5.evidence_bundle.v1`**. Layer-5 supplies structured context; **Layer-3** owns governance posture, routing, execution honesty, and `POST /v0/execute` outcomes.

### Ask paths (known system condition)

- **Compatibility / default IDE path:** `POST /v0/ask` when evidence-first is not in use.
- **Evidence-first (CLI and opt-in IDE):** export → `POST /v1/ask` (see `runtime/scripts/verify_ask_path.sh`, `motadata_behavior_verify.py`).

### Stage 3 loop and validation stance

- **Controlled loop:** `runtime/loop/` — burn-in closure: tracker **B7**, `docs/validation/STAGE3_BURN_IN_REPORT.md`. **IDE → `Stage3LoopController` live E2E** is **follow-on** (tracker §1, §6.20), not the same bar as HTTP burn-in.
- **Regression proof:** CLI + HTTP verification is the **canonical** repeatable surface (`SYSTEM_TRUTH.md` §4); [`JETBRAINS_PLUGIN_FLOW_V0_1.md`](JETBRAINS_PLUGIN_FLOW_V0_1.md) remains a **compatibility** contract for the plugin.

---

## Plan-Gate Architecture

- **Plan object:** Captures request context, constitutional phase expectation, authority/boundary state, routing invariants. Used at plan-gate and judge-gate.
- **Decision flow:** Plan Request → Plan Gate → Authority Validator → Irreversibility Detector → Judge Gate → Execution (allow/block)
- **Fail-closed:** If plan-gate unreachable (timeout, error, network failure) and `fail_closed_if_gate_unreachable` is true, client MUST block execution. No bypass path.
- **Implementation:** Production plan-gate logic lives in `runtime/plangate/`; `runtime/plan_gate_stub/` is a protocol stub for demos and IDE contract testing. `runtime/policies/` is a function-level authority/irreversibility surface used only by tests; production uses plangate.

---

## Authority Validator

Enforces REF/ownership. Authority failure at risky boundary yields refuse or defer. No path to execute under invalid authority. REF phase MUST yield REFUSAL; no conditional allowance.

---

## Irreversibility Detector

Blocks at boundaries. Phase-05 CODE semantics honored. Boundary crossing attempted without authority → blocked. `boundary.irreversible_boundary_phrase` must match exactly between plan and ledger.

---

## Judge Gate

Applies dominance hierarchy. Terminal posture must align with constitutional phase expected. REF → refuse; DES → not safe_execute; CODE → execution_mode shadow or live. DES is a **proposal-only** phase; `safe_execute` is a runtime terminal posture, not a DES semantic authorization.

---

## Execution Blocker

No path exists to execute tool calls or cross irreversible boundaries without plan-gate approval when enforcement is enabled.

---

## Ledger Emission

- Every intercepted action (success or failure) MUST emit a ledger row in shadow and live modes
- Ledger rows append-only; no deletion or modification
- Join key: (request_id, plan_hash)
- Links to plan via plan_hash; boundary_phrase must match

---

## Routing Invariants (Enforced)

| Invariant | Values | Role |
|-----------|--------|------|
| legitimacy_state | legitimate \| illegitimate \| unknown | Authority and scope validity |
| irreversibility_state | pre_boundary \| boundary_present \| boundary_cross_attempted \| boundary_crossed | Boundary position |
| ambiguity_state | resolved \| unresolved \| conflicting | Conflict resolution |
| dominance_applied | "REF>CONF>DES" | Phase dominance hierarchy |

---

## Validation Rules (R1–R5, L1–L5)

**Plan:** R1 (authority fail + risky boundary → refuse/defer); R2 (REF → refuse); R3 (DES → not safe_execute); R4 (CODE → shadow/live); R5 (boundary_phrase match).

**Ledger:** L1 (ref_enforced → phase REF or MIX); L2 (boundary_crossed → verdict crossed); L3 (cross_attempted, not crossed → blocked); L4 (authority fail AND boundary crossed → invalid); L5 (boundary_phrase match, plan_hash link).

---

## CI Backstop

`runtime/ci_gate/` — CI integration for pre-commit, commit-msg, pre-push. Block on gate failure.

---

## IDE Plugin Integration

Plan/Judge/Authority are integrated in the JetBrains plugin for **product compatibility**; tool calls are gated when the bridge is used. Contracts: [JETBRAINS_PLUGIN_FLOW_V0_1.md](JETBRAINS_PLUGIN_FLOW_V0_1.md). **Program-level regression proof** for the closed slice is **CLI/HTTP-first** per [`SYSTEM_TRUTH.md`](SYSTEM_TRUTH.md) §4–§6.

---

## Shadow Mode Protocol

Log-only enforcement. No execution side-effects. Validates telemetry and drift wiring before live mode. S-1: boundary_verdict != crossed in shadow; S-2: every run emits plan and ledger; S-3: plan_hash consistency; S-4: boundary_phrase_hash per boundary_hashing.v0.1; S-5: semantic resolution via lineage; S-6: ingestion_batch includes request_id, plan, ledger_row.

---

## Runtime SAFE Definition

**Runtime is SAFE when:**
1. REF is enforced (no action under illegitimacy)
2. Irreversibility detector blocks at boundaries
3. Ledger emits phase + boundary + allow/block per run
4. Phase-05 CODE semantics honored (fail-closed, ownership checks)

**Production cannot ship without REF enforcement.** No best-effort or advisory-only REF.

---

## Enforcement Invariants

- Gate down → block
- No bypass path
- Append-only ledger
- Boundary invariance (character-for-character)
- REF dominance

---

## Non-Bypass Rules

- No fallback that allows execution when gate unreachable
- Authority violations cannot be overridden by lower phases

---

## Failure Modes

- Gate unreachable with fallback execution
- REF not enforced under illegitimacy
- Boundary crossed without authority
- Ledger not emitted
- Plan/ledger boundary_phrase mismatch

---

## Definition of Done (Layer-3)

The following are **satisfied on `main`** for the closed MVP slice (**M3.0–M3.12**); detail and follow-on (**M3.13+**) are in [`LIVE_ROADMAP_TRACKER.md`](LIVE_ROADMAP_TRACKER.md) §4.3.1.

- Plan and ledger contracts defined; authority/irreversibility hooks implemented (`runtime/plangate/`, schemas under `runtime/ide/schemas/` and `runtime/schemas/`)
- Authority validator implemented; no bypass paths when governed enforcement applies
- Irreversibility detector blocks at boundaries; boundary phrase match between plan and ledger
- HTTP Plan-Gate service and governed execute (`POST /v0/execute`) operational; outcomes validated for the MVP slice (tracker §1, §6.12)
- JetBrains plugin bridge implemented for compatibility; **canonical regression proof** is CLI/HTTP per `SYSTEM_TRUTH.md` §4
- Ledger rows emitted per governed run; shadow mode validated; no REF violations under test closure

---

## What Runtime Must Never Do

- Redefine doctrine
- Change constitutional phase semantics
- Allow execution under invalid authority
- Omit ledger emission
- Relax boundary invariance
