# Layer-1 — Comprehensive Governance Spec

**Entry point:** [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)

**Constitutional doctrine source of truth:** [governance/CONSTITUTIONAL_MANIFEST_v1.0.md](../governance/CONSTITUTIONAL_MANIFEST_v1.0.md). This spec restates and expands for readability; the manifest is authoritative.

## Purpose and Authority Model

Layer-1 is semantic authority. It defines what judgment means and how it must behave. Nothing below Layer-1 may reinterpret it. Judgment precedes execution. Refusal precedes automation. Authority precedes action. If a lower layer disagrees with Layer-1, Layer-1 wins. Always.

Layer-1 does not train models, intercept runtime, optimize datasets, or write policy code. It is structural doctrine only.

---

## Building Blocks

### Constitutional Manifest

**What it is:** The highest authority document. Defines what judgment is and is not, what "safe" means, what drift means, what rollback means, what layers are allowed to do.

**Artifact:** `governance/CONSTITUTIONAL_MANIFEST_v1.0.md`

**Invariants:** Immutable except via governance version increment. Signed off via GREG. Changes require formal ratification.

### Phase Doctrine

Phases define allowed cognitive behavior. These are semantic roles; they describe *how reasoning must behave*, not workflow steps.

| Phase | Name | Meaning |
|-------|------|---------|
| Phase-1 | REF | Legitimacy refusal — absolute illegitimacy; authority or scope violation; must refuse entirely |
| Phase-2 | CONF | Bounded allowance — conditional allowance; pre-boundary reasoning permitted; explicit block at irreversible boundary |
| Phase-3 | DES | Design reasoning only — no execution commitment; no boundary blocking instruction; no prescriptive deployment language |
| Phase-4 | MIX | Collision arbitration — two or more independent pressures collide at same irreversible boundary; requires arbitration; cannot collapse into CONF; cannot collapse into REF unless illegitimacy exists |
| Phase-5 | CODE | Enforcement encoding — implementation-level fail-closed enforcement; no abstract reasoning; execution prevented via guard condition |
| Phase-6 | REACH | Endurance proof — governance-level; not counted in the 29 locked exemplars; stress-tests existing doctrine |

### Dominance Hierarchy

Authority > Irreversibility > Design Preference

- REF dominates ambiguity
- MIX requires multi-pressure
- DES cannot recommend execution
- CODE cannot reason abstractly
- No collapse-to-implementation logic allowed
- Boundary invariance is mandatory

**Routing invariant:** `dominance_applied: "REF>CONF>DES"`

### Boundary Doctrine

- Exact boundary phrase must remain character-for-character identical between Phase-3 and Phase-4
- CONF must include explicit `Allow:` and `Block at boundary:` sections
- REF must not contain conditional allowance structure
- MIX must include two or more independent pressures
- CODE must not include reasoning abstraction

### Stress Surface Taxonomy

Seven stress surfaces govern judgment under multi-surface pressure:

| Surface | Governing Variable | Typical Posture Under Stress |
|---------|-------------------|------------------------------|
| Automation | Irreversibility / Coordination Cost | Block / Isolate |
| Governance | Legitimacy | Escalate |
| Analytics | Epistemic Confidence | Design / Sandbox |
| Processing | Transformation Integrity | Audit-only |
| Data | Signal Integrity | Defer |
| Business | Urgency | Accelerate within bounds |

The surface with highest irreversible downside risk dominates. Severity dominates probability.

### Golden Exemplars

29 locked exemplars (Phases 01–05 per GREG). Phase-06 hardening excluded from the 29. Each exemplar encodes exactly one dominant risk pattern, declares one irreversible boundary, terminates in a stable safe state.

### D.N.A Validation Protocol

Two-stage locking rule for exemplar validation. Structural integrity gates before semantic lock.

### GREG Governance Protocol

GREG (Governance Review and Exemplar Governance) is the ratification and version-lock mechanism. Admissible evidence: locked exemplars, phase semantics, D.N.A artifacts, ledgers, enforcement definitions. Inadmissible: future roadmap, proposed improvements, unlocked variants.

---

## Structural Invariants

- Governance definitions cannot be redesigned
- Runtime enforcement logic cannot be altered
- Boundary anchors cannot be relocated
- Phase definitions are immutable unless version increment occurs
- Exact boundary phrase invariance between Phase-3 and Phase-4

---

## Drift Definition

Drift is observed behavior that diverges from constitutional expectation: REF collapses, boundary softening, MIX-to-CONF collapse, CODE abstraction drift, or phase migration in model output.

---

## Governance Escalation Rules

- **Rollback:** REF collapse above threshold; boundary relocation detected; MIX-to-CONF collapse above threshold; CODE erosion. Rollback = freeze deployment; revert to last approved checkpoint; do not change doctrine.
- **Governance revision (rare):** Persistent drift despite dataset/harness fixes; structural evidence that doctrine itself is incomplete. Only governance (GREG, constitutional manifest) may authorize exemplar or phase changes.

---

## Versioning and Ratification Lifecycle

- Version increment required for any phase or boundary change
- GREG ratification required for lock
- No edits during review; no new exemplars after freeze; no mutation runs after Phase-06 LOCK

---

## Definition of Done (Layer-1)

- Constitutional manifest ratified
- Phase doctrine locked
- Dominance hierarchy frozen
- Golden exemplars (29) locked per GREG
- Boundary invariance doctrine established
- GREG protocol operational

---

## Failure Modes

- Phase semantics softened or blended
- Boundary phrase altered or relocated
- Dominance hierarchy violated
- Exemplar count or structure changed without ratification
- GREG bypassed

---

## What Layer-1 Must Never Contain

- Runtime mechanics
- Training details
- ML code or dataset artifacts
- Compilation harnesses
- Mutation implementation
