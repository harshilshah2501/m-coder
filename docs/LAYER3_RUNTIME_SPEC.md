# Layer-3 — Comprehensive Runtime Enforcement Spec

**Entry point:** [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)

## Purpose

Layer-3 enforces constitutional judgment at execution time. It implements Phase-05 CODE semantics. Runtime consumes trained behavior and enforces it. **Runtime never redefines doctrine.**

**Directory:** `runtime/`

Deterministic runtime state machine semantics are defined in `docs/runtime/RUNTIME_STATE_TRANSITIONS.md` and the associated schemas in `runtime/state/schemas/`.

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

Plan/Judge/Authority integrated in IDE flow. Tool calls gated. Contracts: [JETBRAINS_PLUGIN_FLOW_V0_1.md](JETBRAINS_PLUGIN_FLOW_V0_1.md).

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

- Plan object spec defined; authority/irreversibility hooks specified
- Authority validator implemented; no bypass paths
- Irreversibility detector blocks at boundaries
- IDE plugin integrated; tool calls gated
- Ledger rows emitted per run
- Shadow mode validated; no REF violations

---

## What Runtime Must Never Do

- Redefine doctrine
- Change constitutional phase semantics
- Allow execution under invalid authority
- Omit ledger emission
- Relax boundary invariance
