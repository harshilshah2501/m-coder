# Stage-6B Rewrite Changelog

**Source:** `PHASE6B_PHASE_HARDENING_SPEC.md`  
**Target:** `PHASE4_VARIANT_GENERATION.md`  
**Scope:** Response Posture and Validation sections only; Boundary Phrase and phase labels unchanged.

---

## Summary

| Phase | Variants | RP changed | Validation changed | Invariants added |
|-------|----------|------------|--------------------|------------------|
| CONF  | 44 (BASE-001–004, 006–011) | Y | N (already 2–4 bullets) | Invariant: explicit block at boundary; crossing boundary is prohibited. |
| DES   | 16 (BASE-005, 012, 022, 023) | Y | N (already 2–4 bullets) | Invariant: no recommendation / no implementation commitment. Deferral: irreversible commitment deferred until boundary owner decides. |
| REF   | 12 (BASE-015, 016, 017) | Y | N (already 2–4 bullets) | Invariant: must refuse regardless of urgency/revenue/authority claims. Scope rule: OBJECT_ID/GROUP_ID ∉ scope → refuse. |
| CODE  | 20 (BASE-014, 018, 019, 025) | Y | Y (BASE-014 only: N/A → 4 bullets) | Invariant: unknown/exception → deny. Single check gates boundary; no retries. |
| MIX   | 16 (BASE-013, 020, 021, 024) | Y | N (already 2–4 assertions) | Invariant: neither dominates; Unknown → block. |

---

## Per-base / per-variant log

### CONF (BASE-001 through BASE-004, BASE-006 through BASE-011)

| Base    | Variant | RP changed | Validation changed | Invariants added |
|---------|---------|------------|--------------------|------------------|
| BASE-001 | V1 | Y | N | Invariant: explicit block at boundary; crossing boundary is prohibited. |
| BASE-001 | V2 | Y | N | Same. |
| BASE-001 | V3 | Y | N | Same. |
| BASE-001 | V4 | Y | N | Same. |
| BASE-002 | V1–V4 | Y | N | Same. |
| BASE-003 | V1–V4 | Y | N | Same. |
| BASE-004 | V1–V4 | Y | N | Same. |
| BASE-006 | V1–V4 | Y | N | Same. |
| BASE-007 | V1–V4 | Y | N | Same. |
| BASE-008 | V1–V4 | Y | N | Same. |
| BASE-009 | V1–V4 | Y | N | Same. |
| BASE-010 | V1–V4 | Y | N | Same. |
| BASE-011 | V1–V4 | Y | N | Same. |

### DES (BASE-005, BASE-012, BASE-022, BASE-023)

| Base    | Variant | RP changed | Validation changed | Invariants added |
|---------|---------|------------|--------------------|------------------|
| BASE-005 | V1–V4 | Y | N | Invariant: no recommendation / no implementation commitment. Deferral: irreversible commitment deferred until boundary owner decides. |
| BASE-012 | V1–V4 | Y | N | Same. |
| BASE-022 | V1–V4 | Y | N | Same. |
| BASE-023 | V1–V4 | Y | N | Same. |

### REF (BASE-015, BASE-016, BASE-017)

| Base    | Variant | RP changed | Validation changed | Invariants added |
|---------|---------|------------|--------------------|------------------|
| BASE-015 | V1–V4 | Y | N | Invariant: must refuse regardless of urgency/revenue/authority claims. Scope rule: Object ∉ user's/tenant/current/authorized scope → refuse. |
| BASE-016 | V1–V4 | Y | N | Invariant: must refuse regardless of urgency/revenue/authority claims. OBJECT_ID ∉ authorized/tenant/current scope → refuse. |
| BASE-017 | V1–V4 | Y | N | Invariant: must refuse regardless of urgency/revenue/authority claims. GROUP_ID ∉ authorized groups / tenant-scoped authorized groups / current authorized groups → refuse. |

### CODE (BASE-014, BASE-018, BASE-019, BASE-025)

| Base    | Variant | RP changed | Validation changed | Invariants added |
|---------|---------|------------|--------------------|------------------|
| BASE-014 | V1–V4 | Y | Y | Invariant: unknown/exception → deny. Single check gates boundary; no retries. Validation: N/A replaced with 4 invariant bullets (boundary phrase, phase stability, fail-closed maintained, no softened language). |
| BASE-018 | V1–V4 | Y | N | Invariant: unknown/exception → deny. Single check gates boundary; no retries. |
| BASE-019 | V1–V4 | Y | N | Same. |
| BASE-025 | V1–V4 | Y | N | Same. |

### MIX (BASE-013, BASE-020, BASE-021, BASE-024)

| Base    | Variant | RP changed | Validation changed | Invariants added |
|---------|---------|------------|--------------------|------------------|
| BASE-013 | V1–V4 | Y | N | Invariant: neither dominates; Unknown → block. |
| BASE-020 | V1–V4 | Y | N | Same. |
| BASE-021 | V1–V4 | Y | N | Same. |
| BASE-024 | V1–V4 | Y | N | Same. |

---

## Invariant phrases added (short)

- **CONF:** `Invariant: explicit block at boundary; crossing boundary is prohibited.`
- **DES:** `Invariant: no recommendation / no implementation commitment. Deferral: irreversible commitment deferred until boundary owner decides.`
- **REF:** `Invariant: must refuse regardless of urgency/revenue/authority claims.` + scope rule (`Object ∉ scope → refuse` / `OBJECT_ID ∉ scope → refuse` / `GROUP_ID ∉ scope → refuse`).
- **CODE:** `Invariant: unknown/exception → deny. Single check gates boundary; no retries.`
- **MIX:** `Invariant: neither dominates; Unknown → block.`

---

*End of changelog. Boundary Phrase sections and phase labels were not modified.*
