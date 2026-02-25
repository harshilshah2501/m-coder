# Near-Duplicate Documents

Documents sharing similar titles, structure, or version lineage. Content comparison was **not performed**; groups are inferred from naming and path patterns.

---

## Golden Exemplars / Judgment Guide Versions

| candidate_canonical | near_duplicates | reason |
|---------------------|-----------------|--------|
| motadata-coder-a-complete-guide_v1.7.md | Golden_Exemplars_Guide_v1.5.md | version progression |
| motadata-coder-a-complete-guide_v1.7.md | GOLDEN_EXEMPLARS_GUIDE.md (legacy-v1.0-v1.4) | legacy archive |
| motadata-coder-a-complete-guide_v1.7.md | GOLDEN_EXEMPLARS_REFERENCE_ARCHIVE.md | reference archive |

**Preferred canonical:** `motadata-coder-a-complete-guide_v1.7.md`

---

## Phase-6 / Stage-6 Mutation Specs

| candidate_canonical | near_duplicates | reason |
|---------------------|-----------------|--------|
| ml/training/phase6c/PHASE6C_MUTATION_TAXONOMY.md | PHASE6_MUTATION_TAXONOMY.md | Layer-2 vs general |
| PHASE6B_COLLAPSE_TAXONOMY.md | PHASE6_MUTATION_TAXONOMY.md | related, distinct scope |

**Note:** Related specs, not strict duplicates.

---

## Phase-6 Mutation Reports

| candidate_canonical | near_duplicates | reason |
|---------------------|-----------------|--------|
| PHASE6_MUTATION_REPORT_STAGE6B.md | PHASE6_MUTATION_REPORT.md | Stage6B derivative |

---

## Output Schema (when implemented with content diff)

- group_id
- candidate_canonical
- near_duplicates: path, difference_summary
- why_canonical_preferred: newest | locked | most_referenced
