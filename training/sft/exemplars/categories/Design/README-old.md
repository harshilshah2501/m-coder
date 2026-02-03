# Design Thinking (DES) Exemplars (Engineering-First)

**Category**: Phase-3 (Complexity Layer 2)  
**Exemplar IDs**: DES-01 through DES-05+ (DES-06 optional depth)
**Context**: Engineering-first assistant for design decisions, architecture, rollout planning

## Purpose

These exemplars teach staged design thinking under uncertainty. They focus on phased rollout strategies (feature flags, incremental), validation gates, rollback planning, and explicit assumption documentation.

**Note**: These operate on engineering design artifacts (RFCs, ADRs, rollout plans) rather than operational deployment. Judgment DNA is identical—only the surface changes.

## What It Teaches

- Staged rollout framing (feature flags, incremental rollout) (DES-01)
- Phased testing and validation gates (DES-02)
- Rollback and safety mechanism design (DES-03)
- Assumption documentation and uncertainty framing (DES-04)
- Cross-team handoff and escalation decision points (DES-05)
- Bug response handoff (when to escalate vs. automate) (DES-06, optional)

## Key Principle

**Uncertainty requires staging.** Suggest phased rollouts, not all-at-once deployments.

## Success Metrics

- 100% of designs include phased approaches
- Rollback plans explicit for each design
- Assumptions documented (not hidden)
- Escalation criteria defined for each phase
- Cross-team handoff points clear

## Dependencies

- Phase-2 exemplars (CONF-01 through CONF-05) must pass mutation testing first
- Design examples build on constraint-awareness
- Multi-layer reasoning required (from Phase-1)

## File Structure

```
Design/
├── README.md (this file)
├── DES-01.md (staged rollouts)
├── DES-02.md (phased testing)
├── DES-03.md (rollbacks & circuit breakers)
├── DES-04.md (assumptions & uncertainty)
└── DES-05.md (cross-team handoff)
```

## Related Guides

- [EXEMPLAR_AUTHORING_GUIDE.md](../../guides/EXEMPLAR_AUTHORING_GUIDE.md) — Design sequencing rationale
- [REVIEW_CHECKLIST.md](../../guides/REVIEW_CHECKLIST.md) — 9 comprehensive review criteria (includes 3 D.N.A gates)
- [TAXONOMY_REFERENCE.md](../../guides/TAXONOMY_REFERENCE.md) — Design taxonomy

## Design Principles for These Exemplars

1. **Staged approach**: Always propose phased deployments
2. **Validation gates**: Clear go/no-go criteria at each stage
3. **Rollback ready**: Reverse procedures documented
4. **Assumption tracking**: Don't hide unknowns
5. **Team alignment**: Cross-functional signoff before execution
