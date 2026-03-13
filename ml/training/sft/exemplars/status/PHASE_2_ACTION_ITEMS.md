# Phase-2: Golden Exemplars — Action Items Checklist

**Phase**: 2 (Variant Scaling)  
**Status**: 🚀 KICKOFF  
**Target**: 7.5K-10K SFT samples from 4 locked exemplars

---

## Week 1: Variant Authoring (Manual)

### RCA-01 Variants
- [ ] **RCA-01__variant-A-worse-ambiguity.md**
  - Conflicting signals (metric up, logs down)
  - Same reasoning structure, higher epistemic uncertainty
  - DNA-U-GATE must acknowledge conflicting evidence

- [ ] **RCA-01__variant-B-higher-pressure.md**
  - SLA breach imminent (5 min to escalation)
  - Same root cause, time pressure added
  - DNA-U-GATE must resist rushing to action

- [ ] **RCA-01__variant-C-hidden-incident.md**
  - Real incident masked by alert noise
  - Same diagnostic logic, signal buried deeper
  - DNA-U-GATE must acknowledge incomplete visibility

### RCA-02 Variants
- [ ] **RCA-02__variant-A-worse-ambiguity.md**
- [ ] **RCA-02__variant-B-higher-pressure.md**
- [ ] **RCA-02__variant-C-hidden-incident.md**

### ANOM-01 Variants
- [ ] **ANOM-01__variant-A-worse-ambiguity.md**
- [ ] **ANOM-01__variant-B-higher-pressure.md**
- [ ] **ANOM-01__variant-C-hidden-incident.md**

### REF-01 Variants
- [ ] **REF-01__variant-A-worse-ambiguity.md**
- [ ] **REF-01__variant-B-higher-pressure.md**
- [ ] **REF-01__variant-C-hidden-incident.md**

---

## Week 2: Variant Validation

- [ ] Mutation testing on all 12 variants
- [ ] Peer review (9-gate checklist)
- [ ] D.N.A gate validation
- [ ] Team consensus meeting

---

## Week 3: SFT Dataset Generation

- [ ] Parse exemplars → JSONL schema
- [ ] Generate paraphrases (5-10 per variant)
- [ ] Generate re-grounds (5-10 per variant)
- [ ] Generate intensified versions (5-10 per variant)
- [ ] Generate relaxed versions (5-10 per variant)
- [ ] Output: `ml/datasets/sft/processed/golden_phase2.jsonl`

---

## Week 4: Training & Validation

- [ ] Baseline evaluation (before SFT)
- [ ] Train SFT model on golden_phase2.jsonl
- [ ] Post-SFT evaluation
- [ ] Measure: refusal rate, constraint compliance, uncertainty
- [ ] Generate improvement report

---

## Variant Authoring Template

Each variant must include:

```markdown
# {EXEMPLAR_ID}__variant-{LETTER}-{DESCRIPTOR}

## What Changed
- [Describe the mutation: ambiguity, pressure, or signal visibility]

## B.R.A.I.N Structure
- **B** — Baseline (same as base exemplar)
- **R** — Observed Reality (modified)
- **A** — Signal / Classification (modified)
- **I** — Potential Impact (modified)

--- DNA-U-GATE ---
[Uncertainty statement reflecting the change]
---

- **N** — Next Sensible Actions (same reasoning, adapted to new context)

## Mutation Validation
- [ ] DNA-U-GATE present before actions
- [ ] Reasoning stable under change
- [ ] No hallucinated authority
- [ ] Passes adversarial swap test
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Variants authored | 12/12 |
| Variants passing D.N.A gates | 12/12 |
| SFT samples generated | 7.5K-10K |
| Improvement on test set | 60%+ |
| Team consensus | ✅ Yes |

---

**Owner**: Harshil Shah  
**Start Date**: Jan 27, 2026  
**Target Completion**: Feb 28, 2026

