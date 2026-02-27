# Governance Layer — Canonical Entry

## Purpose

- **What governance contains:** Constitution, phases (01–06), GREG ratification, golden exemplar doctrine, constitutional manifest.
- **What governance must NOT contain:** Runtime code, training scripts, dataset JSONL, mutation harness implementation.
- **Canonical > Convenient:** Prefer traceable references over ad-hoc copies.
- **Layer-1 only:** Governance is doctrine; compilation and enforcement live in ml/ and runtime/.

## Canonical Registry

| Item | Location |
|------|----------|
| Primary Guide v1.7 | `motadata-coder-a-complete-guide_v1.7.md` (repo root) |
| Golden Exemplars / Phases | `governance/golden-exemplars/Phases/` |
| GREG package | `governance/golden-exemplars/GREG/` (Initiation-Ratification, Pre-Review-Package, Pre-Review Attack Result) |
| Phase-4 variant generation | `governance/golden-exemplars/Phases/Phase-04/` (MIX schema, lifecycle, handoff) |
| Phase-5 stability | `governance/golden-exemplars/Phases/Phase-05/` (CODE enforcement, preamble) |
| Phase-6 mutation / lock | `governance/golden-exemplars/Phases/Phase-06/` (Lock, Exit Verification, Cross-Phase Audit) |
| Constitutional manifest | `governance/CONSTITUTIONAL_MANIFEST_v1.0.md` |

## Navigation Map (4-Layer Layout)

| Layer | Dir | Role |
|-------|-----|------|
| 1 | `governance/` | Doctrine, constitution, GREG |
| 2 | `ml/` | Compilation, exemplars/variants, mutation, datasets |
| 3 | `runtime/` | Enforcement, integrations |
| 4 | `observation/` | Probes, drift, audits |
| — | `archive/` | Historical, deprecated |

## Layer Boundaries

- **Allowed:** Constitutional manifest, phase definitions, GREG protocol, golden exemplar doctrine, dominance hierarchy, review packages.
- **Forbidden:** ML code, dataset artifacts, runtime code, compilation harnesses, training scripts, mutation implementation.

See [docs/ARCHITECTURE_4_LAYER.md](../docs/ARCHITECTURE_4_LAYER.md) for full 4-layer structure.

## Rules of Engagement

- **Structural changes:** See docs/ARCHITECTURE_4_LAYER.md. Legacy reorg planning artifacts archived to archive/reorg/.
- **All boundary phrases must remain verbatim:** Do not soften or reword constitutional language.
- **Stage gates must pass before SFT:** Phase-06 lock, GREG readiness, and dataset freeze precede training.
