# Duplicate Resolution Plan

**Source:** repo_audit/DUPLICATES_EXACT.md, DUPLICATES_NEAR.md, RISK_MAP.md

---

## Exact Duplicates (Hash Required)

Hashes were **not computed** in the audit. Run `repo_reorg_plan/tools/compute_duplicate_hashes.py` (only when EXECUTE=1) to confirm.

### Group: smoke_traces.jsonl

| field | value |
|-------|-------|
| candidate_canonical | Keep all if distinct runs; else ml/.../phase6c/out_m4/smoke_traces.jsonl (newest) |
| copies | out/, out_m3/ — archive if identical |
| risk | low |
| references | Phase-6C harness code; unlikely to reference by path |
| action | needs_decision until hashed |

### Group: EXEMPLAR_AUTHORING_GUIDE

| field | value |
|-------|-------|
| candidate_canonical | archive/okr/supporting-docs/EXEMPLAR_AUTHORING_GUIDE.md (or keep both; different contexts) |
| copies | ml/.../engineering-first-regrounding/EXEMPLAR_AUTHORING_GUIDE.md |
| risk | low |
| references | Unknown; low ref_count per DOC_INDEX |
| action | needs_decision until hashed; likely archive both to draft_docs or misc_orphans |

---

## Near-Duplicates (Guide Versions)

### Group: Golden Exemplars / Judgment Guide

| field | value |
|-------|-------|
| candidate_canonical | motadata-coder-a-complete-guide_v1.7.md |
| copies_to_archive | ml/.../Golden_Exemplars_Guide_v1.5.md → archive/by_topic/governance_history |
| copies_already_archived | ml/.../legacy-v1.0-v1.4/GOLDEN_EXEMPLARS_GUIDE.md (keep in place) |
| reference_archive | ml/.../GOLDEN_EXEMPLARS_REFERENCE_ARCHIVE.md — keep as reference index; do not archive |
| risk | high |
| references_that_break | governance/review-packages (Golden_Exemplars_Guide_v1.5), ml/.../guides/README.md, JUDGMENT_SYSTEM_README, CLEANUP_SUMMARY, DOCUMENTATION_AUDIT_REPORT, Reviewer_Pack, MIGRATION_NOTES, QUICK_REFERENCE, sft/README |
| update_required | Yes: point references from v1.5 to v1.7 (or to archived path if historical) |

### Group: Phase-6 Mutation Reports

| field | value |
|-------|-------|
| candidate_canonical | PHASE6_MUTATION_REPORT_STAGE6B.md (if supersedes) |
| copies | PHASE6_MUTATION_REPORT.md |
| risk | medium |
| references | Low; check ml/ and docs |
| action | needs_decision — both may be valuable; archive PHASE6_MUTATION_REPORT to deprecated_mutation only if confirmed superseded |

### Group: Phase-6 Mutation Taxonomies

| field | value |
|-------|-------|
| note | NOT duplicates — distinct scope |
| PHASE6C_MUTATION_TAXONOMY | Stage-6C loop-induced collapse classes |
| PHASE6_MUTATION_TAXONOMY | General Phase-6 mutation |
| PHASE6B_COLLAPSE_TAXONOMY | Stage-6B collapse taxonomy |
| action | keep all; no archival |

---

## Hash Script

See `repo_reorg_plan/tools/compute_duplicate_hashes.py`. Do NOT run unless EXECUTE=1.
