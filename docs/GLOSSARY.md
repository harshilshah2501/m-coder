# Glossary — Canonical Info Model (CIM)

Single definitions for key terms. Schema paths are normative for field names and enums.

---

## Constitutional Terms

| Term | Definition | Schema / Source |
|------|------------|-----------------|
| **constitutional_phase** | Judgment behavior category: REF, CONF, DES, MIX, CODE, REACH. Defined in Constitutional Manifest. | `decision_response.v0.1`: `constitutional_phase_emitted`; `plan.v0.1`: `constitutional_phase_expected`; `ledger_row.v0.1`: `phase_emitted` |
| **dominance_source** | Phase whose dominance rule drove the decision: REF, CONF, or DES. | `decision_response.v0.1`: `dominance_source` |
| **terminal_posture** | Execution posture: refuse, defer, bounded_allow, safe_execute. | `plan.v0.1`, `ledger_row.v0.1` |

---

## Boundary Terms

| Term | Definition | Schema / Source |
|------|------------|-----------------|
| **irreversible_boundary_phrase** | Character-for-character invariant string describing the irreversible boundary. Must match exactly between plan and ledger. | `plan.v0.1`, `ledger_row.v0.1`, `decision_response.v0.1` |
| **boundary_phrase_hash** | SHA-256 of phrase per [boundary_hashing.v0.1.json](../runtime/ide/schemas/boundary_hashing.v0.1.json) canonicalization (UTF-8, \n, no trim). | `decision_response.v0.1`, `lineage.node.v0.1` |

---

## Identity and Join Keys

| Term | Definition | Schema / Source |
|------|------------|-----------------|
| **plan_hash** | SHA-256 of canonicalized plan JSON. Links ledger row and decision_response to plan. | `plan.v0.1` (integrity), `ledger_row.v0.1` (plan_link), `decision_response.v0.1` |
| **request_id** | Request-scoped identifier. Join key component with plan_hash. | `plan.v0.1`, `ledger_row.v0.1`, `plan_request.v0.1` |
| **event_id** | Ledger row event identifier. Field: `event.event_id` in ledger_row. | `ledger_row.v0.1`: `event.event_id` |
| **ledger_record** | Lineage node type (LEDGER_RECORD) linking runtime ledger to RUNTIME_MODEL_ARTIFACT. Distinct from ledger row `event_id`. | `lineage.node.v0.1` (node type) |

---

## Decision Terms

| Term | Definition | Schema / Source |
|------|------------|-----------------|
| **decision** | Plan-gate response: APPROVE, CONDITIONAL_BLOCK, REFUSAL, BOUNDING. | `decision_response.v0.1`: `decision` |
| **decision enum** | Value set for decision field. Defined in `decision_enums.v0.1.json`. | `runtime/ide/schemas/decision_enums.v0.1.json` |

---

## Compilation and Lineage

| Term | Definition | Schema / Source |
|------|------------|-----------------|
| **collapse_vector** | Drift classification: REF_SOFTENING, CONF_TO_DES, BOUNDARY_ALIASING, etc. Propagates through DAG. | `lineage.node.v0.1` (concept); COMPILATION_DAG, STAGE6_MUTATION_TAXONOMY |
| **routing_invariants** | legitimacy_state, irreversibility_state, ambiguity_state, dominance_applied. Used by plan-gate. | `plan.v0.1`, `ledger_row.v0.1` |
