# Non-Negotiable Invariants

System behaviors that must not be weakened or bypassed. These are fail-closed semantics.

---

## Gate Down → Block

When the plan-gate or judge-gate is unreachable (timeout, error, network failure):

- **Client policy:** If `fail_closed_if_gate_unreachable` is true, the client MUST block execution.
- **No bypass path:** There is no fallback that allows execution when the gate cannot be reached.

---

## No Bypass Path

- No path exists to execute tool calls or cross irreversible boundaries without plan-gate approval when enforcement is enabled.
- REF phase MUST yield REFUSAL; no conditional allowance.
- Authority failure at risky boundary MUST yield refuse or defer.

---

## Append-Only Ledger

- Ledger rows are append-only. No deletion or modification of emitted ledger rows.
- Every intercepted action (success or failure) MUST emit a ledger row in shadow and live modes.

---

## Boundary Invariance

- `irreversible_boundary_phrase` must match exactly between plan and ledger.
- Exact boundary phrase must remain character-for-character identical between Phase-3 and Phase-4 (per Constitutional Manifest).
- Boundary hashing follows [boundary_hashing.v0.1.json](../runtime/ide/schemas/boundary_hashing.v0.1.json).

---

## REF Dominance

- REF dominates ambiguity.
- REF phase MUST yield decision REFUSAL.
- Authority violations cannot be overridden by lower phases.
