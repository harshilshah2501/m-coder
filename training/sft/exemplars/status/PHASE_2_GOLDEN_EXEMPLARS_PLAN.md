# Phase-2: Golden Exemplars Scaling Plan

**Status**: Phase-1 Complete ✅ | Phase-2 Kickoff 🚀  
**Date**: January 27, 2026  
**Objective**: Scale 4 locked exemplars → 7.5K-10K golden variants with stable reasoning

---

## Phase-1 Completion Summary

### What We Locked
- ✅ **RCA-01, RCA-02** — Signal trust under ambiguity
- ✅ **ANOM-01** — Metric anomaly with delayed data
- ✅ **REF-01** — Governance baseline (unsafe automation refusal)

**Total**: 4 exemplars locked with B.R.A.I.N + D.N.A gates

### What We Learned
1. **B.R.A.I.N structure works** — Baseline → Reality → Ambiguity → Impact → (DNA-U-GATE) → Next Actions
2. **DNA-U-GATE is non-negotiable** — Uncertainty must precede action
3. **Mutation testing reveals brittleness** — Adversarial swaps expose positional bias
4. **Behavioral defaults matter** — SFT trains weight-level preferences, not surface instructions

---

## Phase-2 Strategy: Variant Explosion

### Core Insight
One golden exemplar → 3 adversarial variants → 100-200 SFT samples via:
- **Paraphrase**: Reword instruction, keep reasoning skeleton
- **Re-ground**: Apply to different services/failure patterns
- **Intensify**: Worse ambiguity, higher stakes, more pressure
- **Relax**: Easier constraints, clearer signals

### Target Breakdown

| Exemplar | Base | Variants | SFT Samples | Total |
|----------|------|----------|-------------|-------|
| RCA-01 | 1 | 3 | 150 | 154 |
| RCA-02 | 1 | 3 | 150 | 154 |
| ANOM-01 | 1 | 3 | 150 | 154 |
| REF-01 | 1 | 3 | 150 | 154 |
| **Subtotal** | **4** | **12** | **600** | **616** |

**Phase-2 Goal**: 7.5K-10K samples from 4 exemplars = 1,875-2,500 variants per exemplar

---

## Phase-2 Execution Plan

### Week 1: Variant Authoring (Manual)
1. **RCA-01 variants** (3 adversarial)
   - Variant A: Worse ambiguity (conflicting signals)
   - Variant B: Higher pressure (SLA breach imminent)
   - Variant C: Hidden incident (signal masked by noise)

2. **RCA-02 variants** (3 adversarial)
3. **ANOM-01 variants** (3 adversarial)
4. **REF-01 variants** (3 adversarial)

**Deliverable**: 12 variant exemplars (all pass D.N.A gates)

### Week 2: Variant Validation
- Mutation testing on all 12 variants
- Peer review (9-gate checklist)
- Team consensus on behavioral alignment

### Week 3: SFT Dataset Generation
- Parse exemplars → JSONL schema
- Generate paraphrases (5-10 per variant)
- Generate re-grounds (5-10 per variant)
- Generate intensified/relaxed versions (5-10 per variant)
- **Output**: `datasets/sft/processed/golden_phase2.jsonl` (7.5K-10K samples)

### Week 4: Training & Validation
- Train SFT model on golden_phase2.jsonl
- Baseline evaluation (before SFT)
- Post-SFT evaluation
- Measure: refusal rate, constraint compliance, uncertainty articulation

---

## Success Criteria

✅ All 12 variants pass D.N.A gates  
✅ Reasoning stable across variants (mutation testing)  
✅ 7.5K-10K SFT samples generated  
✅ 60%+ improvement on test set (vs baseline)  
✅ Team consensus: "This feels like senior-engineer thinking"

---

## Next Immediate Actions

1. **Today**: Review this plan with team
2. **Tomorrow**: Start RCA-01 variant authoring
3. **This week**: Complete all 12 variants
4. **Next week**: Validation + SFT dataset generation

---

**Owner**: Harshil Shah  
**Timeline**: 4 weeks (Feb 1-28, 2026)

