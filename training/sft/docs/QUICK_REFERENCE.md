# SFT Golden Exemplars — Quick Reference Card (Engineering-First)

**Location**: `/home/harshil/Harshil-PoCs/training/sft/`  
**Updated**: January 28, 2026  
**Status**: 5/30 exemplars locked | Target: Jan 31, 2026

**Context**: Exemplars train an **engineering-first assistant** operating on PRs, tests, code reviews, CI/CD, and releases. See [GROUNDING_TRANSFORMATION_REFERENCE.md](../exemplars/guides/GROUNDING_TRANSFORMATION_REFERENCE.md) for ops→engineering mappings.

---

## 🎯 What to Read Right Now

| Your Goal | Read This | Location |
|-----------|-----------|----------|
| **Understand the concept** | Golden Exemplars Overview | [exemplars/README.md](../exemplars/README.md) |
| **See why it matters** | Architecture Alignment & Metrics | [SFT_FRAMEWORK.md](SFT_FRAMEWORK.md) |
| **Author an exemplar** | Authoring Guide | [exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md](../exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md) |
| **Review an exemplar** | Comprehensive Review (9 criteria, includes 3 D.N.A gates) | [exemplars/guides/REVIEW_CHECKLIST.md](../exemplars/guides/REVIEW_CHECKLIST.md) |
| **Understand edge cases** | Mutation Testing | [variants/variant-A.md](../variants/variant-A.md) |
| **See working examples** | Locked Exemplars | [exemplars/categories/RCA/](../exemplars/categories/RCA/), [exemplars/categories/Refusal/](../exemplars/categories/Refusal/) |

---

## 📋 Phase-1 Workflow (30 Exemplars)

```
1. Pick category (RCA, Anomaly, Refusal, Constraint, Design, MultiLayer, Coding)
   └─→ Alternate categories to prevent bias
   
2. Declare B.R.A.I.N layers (Boundary, Reality, Ambiguity, Intent, Narrative)
   └─→ Use: exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md
   
3. Draft exemplar (Instruction, Input, Reasoning, Output)
   └─→ Reference: exemplars/guides/GOLDEN_EXEMPLARS_GUIDE.md
   
4. Pass comprehensive review (9 criteria including 3 D.N.A gates)
   └─→ Use: exemplars/guides/REVIEW_CHECKLIST.md
   
5. Validate D.N.A gates (Decomposition, Negative Capability, Adversarial Swap)
   └─→ These are Gates 6-D, 6-N, 6-A in the review checklist
   
6. Lock exemplar (no changes after mutation testing)
   └─→ Track: exemplars/status/AUTHORING_TODO.md
```

---

## ✅ Success Criteria (Don't Proceed Without)

### Phase-1 Exit Gates
- [ ] All 30 exemplars locked
- [ ] 100% pass 9 comprehensive review criteria
- [ ] 100% pass 3 D.N.A validation gates (Decomposition, Negative Capability, Adversarial Swap)
- [ ] ≥10 exemplars survived mutation testing
- [ ] Team consensus: "This reflects senior-engineer thinking"
- [ ] Base model baseline test completed

### Phase-2 Exit Gates
- [ ] 20K-30K variants generated
- [ ] SFT model shows ≥60% reduction in unsafe suggestions
- [ ] Constraint compliance: 100% of code includes safety gates
- [ ] Refusal accuracy: ≥80% on dangerous requests
- [ ] Multi-turn conversation stability verified

---

## 🗂️ Canonical File Locations

### Root Level (`training/sft/`)
```
├── README.md                                  ← Start here (navigation hub)
├── GOLDEN_EXEMPLARS_COMPLETE_GUIDE.md         ← Full reference (v1.1)
├── sft_golden_exemplar_framework.md           ← Streamlined authoring
├── Reservations_on_exemplars_importance.md    ← Why manual authoring?
├── variant-A.md                               ← Mutation example
├── sft_config.yaml                            ← Training hyperparameters
└── MIGRATION_NOTES.md                         ← Cleanup history
```

### Exemplar Repository (`exemplars/`)
```
├── README.md                                  ← Philosophy & framework
├── guides/
│   ├── EXEMPLAR_AUTHORING_GUIDE.md           ← Complete authoring reference
│   ├── GOLDEN_EXEMPLARS_GUIDE.md             ← Legacy detailed reference
│   ├── REVIEW_CHECKLIST.md                   ← 9-gate review
│   ├── TAXONOMY.md                           ← Category taxonomy
│   └── DNA_VALIDATION.md                     ← Validation framework
├── categories/
│   ├── RCA/          ← Root cause analysis (RCA-01, RCA-02)
│   ├── Anomaly/      ← Anomaly detection (ANOM-01, ANOM-02)
│   ├── Refusal/      ← Safety refusal (REF-01)
│   ├── Constraint/   ← Constraint-aware config (CONF-01–05 planned)
│   ├── Design/       ← Design thinking (DES-01–05 planned)
│   ├── MultiLayer/   ← Multi-layer pressure (MIX-01–05 planned)
│   └── Coding/       ← Safe code scaffolds (CODE-01–07 planned)
└── status/
    ├── AUTHORING_TODO.md                     ← Progress tracker
    └── PHASE_1_CHECKLIST.md                  ← Phase 1 gates
```

---

## 🚀 Common Tasks

### Start Authoring Your First Exemplar
```bash
cd exemplars/
# Read the framework
cat guides/EXEMPLAR_AUTHORING_GUIDE.md

# Pick a category folder (e.g., RCA/)
cd RCA/

# Copy template from existing exemplar
cp RCA-01.md RCA-03.md

# Edit with your scenario
vim RCA-03.md
```

### Review an Exemplar
```bash
# Use 9-gate checklist
cat exemplars/guides/REVIEW_CHECKLIST.md

# Check against full guide
cat exemplars/guides/GOLDEN_EXEMPLARS_GUIDE.md

# Validate D.N.A
cat exemplars/guides/DNA_VALIDATION.md
```

### Track Progress
```bash
# Open TODO tracker
cat exemplars/status/AUTHORING_TODO.md

# Current status: 5/30 locked
# Remaining: 25 (3 RCA, 3 Anomaly, 4 Refusal, 5 Config, 5 Design, 5 Mixed)
```

---

## 🔥 Quick Decisions

| Question | Answer | Reference |
|----------|--------|-----------|
| How many exemplars? | **30 total** (7 categories, varied distribution) | [exemplars/guides/TAXONOMY.md](../exemplars/guides/TAXONOMY.md) |
| How long per exemplar? | **1.5–2 hours** (ideation + draft + validation + review) | [docs/SFT_FRAMEWORK.md](SFT_FRAMEWORK.md) |
| Can I use automation? | **No** — manual authoring is required | [Reservations_on_exemplars_importance.md](Reservations_on_exemplars_importance.md) |
| Why so few exemplars? | **Quality > quantity** — scale comes from variants (250+ per exemplar) | [exemplars/guides/TAXONOMY.md](../exemplars/guides/TAXONOMY.md) |
| Are they product-specific? | **No (Phase-1)** — intentionally abstract; grounding comes in Phase-2 | [docs/SFT_FRAMEWORK.md](SFT_FRAMEWORK.md) |
| How do I know it's good? | **Pass 9 review criteria** (including 3 D.N.A gates) | [exemplars/guides/REVIEW_CHECKLIST.md](../exemplars/guides/REVIEW_CHECKLIST.md) |

---

## 📊 Current Progress (Jan 20, 2026)

| Category | Target | Locked | Remaining | Status |
|----------|--------|--------|-----------|--------|
| RCA | 5 | 2 | 3 | 🟡 In Progress |
| Anomaly | 5 | 2 | 3 | 🟡 In Progress |
| Refusal | 5 | 1 | 4 | 🟡 In Progress |
| Constraint | 5 | 0 | 5 | ⏳ Planned |
| Design | 5 | 0 | 5 | ⏳ Planned |
| MultiLayer | 5 | 0 | 5 | ⏳ Planned |
| Coding | 2-5 | 0 | 2-5 | ⏳ Planned |
| **TOTAL** | **30+** | **5** | **25+** | **⏳ 17% Complete** |

**Target**: Jan 31, 2026 (11 days remaining)  
**Pace Required**: ~2.3 exemplars/day  
**Realistic Adjustment**: Recommend Feb 5 for quality assurance

---

## 🆘 Need Help?

| Issue | Solution |
|-------|----------|
| Don't know where to start | Read [exemplars/README.md](../exemplars/README.md) + [exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md](../exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md) |
| Exemplar feels too generic | Check [docs/SFT_FRAMEWORK.md](SFT_FRAMEWORK.md) — this is intentional (Phase-1) |
| Failing D.N.A validation | Review [variants/variant-A.md](../variants/variant-A.md) for mutation testing example |
| Unsure about quality | Use [exemplars/guides/REVIEW_CHECKLIST.md](../exemplars/guides/REVIEW_CHECKLIST.md) |
| Need working example | Study [exemplars/categories/RCA/RCA-01.md](../exemplars/categories/RCA/RCA-01.md) or [exemplars/categories/Refusal/REF-01.md](../exemplars/categories/Refusal/REF-01.md) |

---

**Pro Tip**: Bookmark this file and use it as your daily reference. Everything else is deep-dive material.
