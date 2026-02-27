# Current State Overview

**Source:** repo_audit/INDEX_TREE.md, DOC_INDEX.md, ORPHANS.md, TARGET_LAYOUT.md

---

## Quick Repo Overview

- **Root:** `/root/m-coder`
- **Architecture:** 4-layer (governance, ml, runtime, observation) + docs, scripts, archive
- **High-density dirs:** `.git/`, `ml/.../phase6/.venv/`, `ml/.../phase6c/`, `governance/golden-exemplars/Phases/`, `ml/datasets/`, `ml/evaluation/results/phase_c/`
- **Key files at root:** motadata-coder-a-complete-guide_v1.7.md, GREG_Pre-Review_Attack_Result.md, Hardware-Profile.md, README.md, chat-*.txt

---

## Top Clutter Sources

### 1. Duplicates and Near-Duplicates

- **Guide versions:** motadata-coder-a-complete-guide_v1.7 (canonical) vs Golden_Exemplars_Guide_v1.5 vs GOLDEN_EXEMPLARS_GUIDE (legacy-v1.0-v1.4) vs GOLDEN_EXEMPLARS_REFERENCE_ARCHIVE
- **smoke_traces.jsonl:** 3 copies (out/, out_m3/, out_m4/) — likely distinct runs; hash will confirm
- **EXEMPLAR_AUTHORING_GUIDE:** 2 copies in archive contexts

*Source: repo_audit/DUPLICATES_EXACT.md, DUPLICATES_NEAR.md*

### 2. Orphans / Low-Reference

- archive/okr, archive/docs (Introspection, EVALUATION_REPORT.txt, FUNCTIONAL_TEST_REPORT.txt, reorganization_plan.txt)
- chat-*.txt at root (session logs)
- Hardware-Profile.md, GREG_Pre-Review_Attack_Result.md (root; governance-adjacent)

*Source: repo_audit/ORPHANS.md*

### 3. Version Ladders

- v1.0-v1.4 → v1.5 → v1.7 for guides
- PHASE6_MUTATION_REPORT vs PHASE6_MUTATION_REPORT_STAGE6B
- PHASE6_MUTATION_TAXONOMY (Motadata) vs PHASE6C_MUTATION_TAXONOMY (phase6c)

*Source: repo_audit/DUPLICATES_NEAR.md, DOC_INDEX.md*

---

## Where Doctrine Lives vs Where It Should Live (per TARGET_LAYOUT)

| current | should live (per TARGET_LAYOUT) | gap |
|---------|---------------------------------|-----|
| motadata-coder-a-complete-guide_v1.7.md (root) | governance/ | root clutter |
| GREG_Pre-Review_Attack_Result.md (root) | governance/ | root clutter |
| governance/golden-exemplars/GREG/* | governance/ | correct |
| governance/golden-exemplars/Phases/* | governance/ | correct |
| ml/training/phase6c/PHASE6C_* | ml/ | correct |
| ml/training/src/sources/Motadata/PHASE6* | ml/phase6 or phase6c | scattered in src tree |
| Golden_Exemplars_Guide_v1.5 (ml/.../guides/) | archive/by_topic/governance_history | superseded by v1.7 |
| chat-*.txt (root) | archive/by_topic/misc_orphans | root clutter |

*Source: repo_audit/TARGET_LAYOUT.md "Belongs" / "Does NOT belong", ORPHANS.md "Outside Canonical Layers"*
