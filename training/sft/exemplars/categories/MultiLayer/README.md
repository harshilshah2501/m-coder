# Multi-Layer Pressure (MIX) Exemplars (Engineering-First)

**Category**: Phase-4 (Complexity Layer 3 — Stress Testing)  
**Exemplar IDs**: MIX-01 through MIX-05+ (MIX-06 optional depth)
**Context**: Engineering-first assistant under multi-faceted development pressure

## Purpose

These exemplars stress-test reasoning across all 7 architectural layers simultaneously. They combine multiple simultaneous pressures: release urgency, test signal ambiguity, ownership bottlenecks, automation risks, and decision paralysis.

**Note**: Uses engineering stress (release deadlines, test failures, code freeze conflicts) rather than ops stress (SLAs, incidents). Same judgment patterns, earlier lifecycle.

## What It Teaches

- Release pressure + test ambiguity: phased response under stress (MIX-01)
- Test storm + ownership bottleneck: prioritization (MIX-02)
- Conflicting signals + time pressure: safe deferral (MIX-03)
- Cascading test failures: when to break isolation (MIX-04)
- Unknown unknowns: escalation and learning loops (MIX-05)
- Sustained crunch: team fatigue and decision decay (MIX-06, optional)

## Key Principle

**Reasoning must be stable under multi-layer pressure.** Safe deferral beats confident mistakes.

## Success Metrics

- Refusal rate ≥80% on ambiguous multi-layer scenarios
- Deferral decisions include explicit trade-off reasoning
- No escalating loops (decision deadlocks)
- Prioritization logic clear when resources limited
- Team fatigue recognized (not ignored)

## Mutation Testing Focus

These exemplars **must survive mutation testing** — they validate generalization across complex scenarios.

## Dependencies

- Phase-1 exemplars (RCA, ANOM, REF) fully locked
- Phase-2 exemplars (CONF-01 through CONF-05) fully locked
- Phase-3 exemplars (DES-01 through DES-05) must pass calibration
- Each MIX exemplar builds on prior ones (MIX-01→02→03...)

## File Structure

```
MultiLayer/
├── README.md (this file)
├── MIX-01.md (SLA + ambiguity stress)
├── MIX-02.md (alert storm + governance)
├── MIX-03.md (conflicting signals + pressure)
├── MIX-04.md (cascading failures)
└── MIX-05.md (unknowns & escalation loops)
```

## Related Guides

- [EXEMPLAR_AUTHORING_GUIDE.md](../../guides/EXEMPLAR_AUTHORING_GUIDE.md) — Multi-layer stress sequencing
- [REVIEW_CHECKLIST.md](../../guides/REVIEW_CHECKLIST.md) — 9 comprehensive review criteria (includes 3 D.N.A gates)
- [DNA_REVIEWER_EXERCISE.md](../../guides/DNA_REVIEWER_EXERCISE.md) — Decision-making under pressure

## Scenario Construction Approach

Multi-layer exemplars combine:
1. **Test/Data layer failure**: Flaky tests, incomplete coverage, conflicting test results
2. **CI/Analysis layer failure**: False confidence from coverage tools, misleading benchmarks
3. **Quality Gate layer failure**: CI failures, broken builds, blocked PRs
4. **Automation layer failure**: Auto-fix loops, refactoring tools breaking code
5. **Ownership layer failure**: Review deadlock, unclear code ownership, conflicting reviewers
6. **Release layer failure**: Code freeze active, release deadline imminent, multiple stakeholders
7. **Time pressure**: All of the above, compressed into sprint end or release deadline

This is not a feature demo. This is **engineering judgment under real development stress**.
