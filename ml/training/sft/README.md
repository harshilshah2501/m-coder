# SFT Training: Supervised Fine-Tuning for Motadata Engineering Assistant

**Reorganized**: January 21, 2026  
**Re-grounded**: January 28, 2026 (Engineering-First Context)  
**Status**: Phase-1 exemplar authoring (5/30 locked, re-grounded)

---

## 🔄 Re-Grounding Update (January 2026)

**What Changed**: The assistant's scope shifted from **production decision-making** (operations on alerts, incidents, SLAs) to **engineering-first** (development on PRs, tests, code reviews, CI/CD, releases).

**What Did NOT Change**: Judgment DNA — B.R.A.I.N authoring discipline, D.N.A validation gates, refusal as first-class behavior, ambiguity handling, and constraint awareness remain identical.

**Key Transformation**: Ops artifacts → Engineering artifacts (same judgment patterns, earlier lifecycle)

**References**:
- [REGROUNDING_STRATEGIC_FAQ.md](exemplars/guides/REGROUNDING_STRATEGIC_FAQ.md) — Strategic context for the shift
- [REGROUNDING_HYPOTHESIS.md](exemplars/guides/REGROUNDING_HYPOTHESIS.md) — Transformation methodology
- [GROUNDING_TRANSFORMATION_REFERENCE.md](exemplars/guides/GROUNDING_TRANSFORMATION_REFERENCE.md) — Authoritative ops→engineering mapping table

**Status**: 5 foundational exemplars successfully re-grounded (RCA-01, RCA-02, ANOM-01, ANOM-02, REF-01). All documentation updated to reflect engineering-first context.

---

## 📁 Directory Structure

### 📋 [`docs/`](docs/) — Executive & Strategic Documentation
Strategic R&D direction, frameworks, and high-level guides.

- **[EXECUTIVE_R_AND_D_SCORECARD.md](docs/EXECUTIVE_R_AND_D_SCORECARD.md)** — Decision gates, uncertainty retirement, 50% coding output metric
- **[SFT_FRAMEWORK.md](docs/SFT_FRAMEWORK.md)** — Overall SFT approach and architecture
- **[GOLDEN_EXEMPLARS_REFERENCE_ARCHIVE.md](docs/GOLDEN_EXEMPLARS_REFERENCE_ARCHIVE.md)** — Full-depth reference (archived; use guides/ for current work)
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** — Quick lookup guide
- **[MIGRATION_NOTES.md](docs/MIGRATION_NOTES.md)** — Migration history and decisions

### 🎯 [`exemplars/`](exemplars/) — Golden Exemplars (Core R&D Asset)

#### Guides & References: [`exemplars/guides/`](exemplars/guides/)
- **[EXEMPLAR_AUTHORING_GUIDE.md](exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md)** ⭐ START HERE — Comprehensive guide with chronology, sequencing, and stress-surface mapping (updated for engineering-first)
- **[GROUNDING_TRANSFORMATION_REFERENCE.md](exemplars/guides/GROUNDING_TRANSFORMATION_REFERENCE.md)** ⭐ REGROUNDING REFERENCE — Authoritative ops→engineering artifact mapping table
- **[REGROUNDING_STRATEGIC_FAQ.md](exemplars/guides/REGROUNDING_STRATEGIC_FAQ.md)** — Strategic context for engineering-first shift
- **[REGROUNDING_HYPOTHESIS.md](exemplars/guides/REGROUNDING_HYPOTHESIS.md)** — Transformation methodology and rules
- **[REVIEW_CHECKLIST.md](exemplars/guides/REVIEW_CHECKLIST.md)** — 9 comprehensive review criteria (including 3 D.N.A validation gates)
- **[REVIEWER_ENGINEER_GUIDE.md](exemplars/guides/REVIEWER_ENGINEER_GUIDE.md)** — How to review exemplars like an engineer
- **[TAXONOMY_REFERENCE.md](exemplars/guides/TAXONOMY_REFERENCE.md)** — SFT taxonomy mapping
- **[DATASET_TAXONOMY_REFERENCE.md](exemplars/guides/DATASET_TAXONOMY_REFERENCE.md)** — From D.N.A to 25K samples
- **[DNA_REVIEWER_EXERCISE.md](exemplars/guides/DNA_REVIEWER_EXERCISE.md)** — Decision-making reviewer training
- **[GOLDEN_EXEMPLARS_GUIDE.md](exemplars/guides/GOLDEN_EXEMPLARS_GUIDE.md)** — Authoritative reference (canonical source)

#### Exemplar Categories: [`exemplars/categories/`](exemplars/categories/)
Actual exemplars organized by failure mode and phase:

**Phase-1 (Foundation)**:
- **[RCA/](exemplars/categories/RCA/)** — Root Cause Analysis exemplars (RCA-01, RCA-02)
- **[Anomaly/](exemplars/categories/Anomaly/)** — Anomaly Handling exemplars (ANOM-01, ANOM-02)
- **[Refusal/](exemplars/categories/Refusal/)** — Refusal Posture exemplars (REF-01)

**Phase-2+ (Complexity Layers)**:
- **[Constraint/](exemplars/categories/Constraint/)** — Constraint-aware config (CONF-01–05+)
- **[Design/](exemplars/categories/Design/)** — Staged design thinking (DES-01–05+)
- **[MultiLayer/](exemplars/categories/MultiLayer/)** — Multi-layer stress testing (MIX-01–05+)
- **[Coding/](exemplars/categories/Coding/)** — Safe code implementation (CODE-01–07+)

#### Authoring Status: [`exemplars/status/`](exemplars/status/)
Checklists, todos, and progress tracking:

- **[PHASE_1_CHECKLIST.md](exemplars/status/PHASE_1_CHECKLIST.md)** — Phase-1 completion criteria (5–15 exemplars locked)
- **[AUTHORING_TODO.md](exemplars/status/AUTHORING_TODO.md)** — Current authoring tasks and blockers
- **[RESTRUCTURING_SUMMARY.md](exemplars/status/RESTRUCTURING_SUMMARY.md)** — Recent restructuring decisions

### ⚙️ [`config/`](config/) — Configuration & Build
- **[sft_config.yaml](config/sft_config.yaml)** — SFT training configuration

### 🔬 [`variants/`](variants/) — Experimental Variants
Alternative approaches and experiments:

- **[VARIANT_A.md](variants/VARIANT_A.md)** — Variant A approach (under evaluation)

### 📊 [`assets/`](assets/) — Media & Diagrams
- **[SFT_DATASET_LAYERS_DESIGN.png](assets/SFT_DATASET_LAYERS_DESIGN.png)** — Visual architecture of data layers

---

## 🎯 Quick Navigation

**I want to...**

- **Understand the re-grounding** → Start with [REGROUNDING_STRATEGIC_FAQ.md](exemplars/guides/REGROUNDING_STRATEGIC_FAQ.md) and [GROUNDING_TRANSFORMATION_REFERENCE.md](exemplars/guides/GROUNDING_TRANSFORMATION_REFERENCE.md)
- **Understand the big picture** → Read [EXECUTIVE_R_AND_D_SCORECARD.md](docs/EXECUTIVE_R_AND_D_SCORECARD.md)
- **Learn how to author exemplars** → Read [EXEMPLAR_AUTHORING_GUIDE.md](exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md) (updated for engineering context)
- **Review an exemplar** → Use [REVIEW_CHECKLIST.md](exemplars/guides/REVIEW_CHECKLIST.md) and [REVIEWER_ENGINEER_GUIDE.md](exemplars/guides/REVIEWER_ENGINEER_GUIDE.md)
- **Check Phase-1 progress** → See [PHASE_1_CHECKLIST.md](exemplars/status/PHASE_1_CHECKLIST.md) and [AUTHORING_TODO.md](exemplars/status/AUTHORING_TODO.md)
- **Understand taxonomy** → Refer to [TAXONOMY_REFERENCE.md](exemplars/guides/TAXONOMY_REFERENCE.md)
- **See actual exemplars** → Browse [exemplars/categories/](exemplars/categories/) (RCA, Anomaly, Refusal folders have locked examples)

---

## 📊 Current Status

**Re-Grounding Complete** (Jan 28, 2026): All documentation updated for engineering-first context

**Phase-1 (Reasoning DNA)**: In Progress
- Target: 30 exemplars (RCA, ANOM, REF, CONF, DES, MIX, CODE categories)
- Phase-1 Completed & Re-grounded: RCA-01, RCA-02, ANOM-01, ANOM-02, REF-01 (5/5 locked ✓)
- Phase-2 In progress: CONF-01, CONF-02 (require re-grounding before scaling)
- Phase-3 Planned: DES-01 through DES-05
- Phase-4 Planned: MIX-01 through MIX-05
- Phase-5 Planned: CODE-01 through CODE-07
- Timeline: Jan 31, 2026 target completion

**Documentation Updates** (Jan 28, 2026):
- ✅ All guides updated with engineering-first language
- ✅ Created [GROUNDING_TRANSFORMATION_REFERENCE.md](exemplars/guides/GROUNDING_TRANSFORMATION_REFERENCE.md) — authoritative mapping table
- ✅ Updated all category READMEs (Constraint, Design, Coding, MultiLayer)
- ✅ Updated status tracking docs (PHASE_1_CHECKLIST, AUTHORING_TODO)
- ✅ Root README updated with regrounding summary

**Key Metrics**:
- Comprehensive review pass rate: ~100% (exemplars pass all 9 criteria including 3 D.N.A gates)
- D.N.A validation: All exemplars pass Decomposition, Negative Capability, Adversarial Swap tests
- Mutation testing survivors: 10+ (adversarial robustness verified)
- Unsafe suggestion rate: Target ≤5% (baseline ~40%)

---

## 🔗 Related Work

- **Main codebase**: `/home/harshil/Harshil-PoCs/agents/`
- **Datasets**: `/home/harshil/Harshil-PoCs/datasets/v17_*`
- **Evaluation framework**: See [docs/](docs/) for eval references

---

## 📝 Notes

- **Naming convention**: UPPERCASE_WITH_UNDERSCORES for clarity
- **Exemplar IDs**: RCA-01, ANOM-01, REF-01, CONF-01, DES-01, MIX-01, CODE-01 (plus variants)
- **Review checklist**: [9 comprehensive review criteria](exemplars/guides/REVIEW_CHECKLIST.md) (includes 3 D.N.A gates) before advancement
- **Next phase**: Phase-2 (Operational Grounding) begins after Phase-1 exemplars lock and mutation testing validates robustness

---

**Last updated**: January 21, 2026
