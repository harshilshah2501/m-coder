# Wave-2 Decision Pack

**Source:** repo_reorg_plan/CANONICALS.md, REFERENCE_UPDATE_MAP.md, ORPHAN_TRIAGE.md, DUPLICATE_RESOLUTION_PLAN.md, CURRENT_STATE.md, CHECKLIST.md, MOVESET_PLAN.jsonl

**Read-only.** No moves, renames, or edits to existing docs. This file supports human decision-making only.

---

## 1) Decision A — Canonical home for the v1.7 guide

**File:** `motadata-coder-a-complete-guide_v1.7.md` (currently at repo root)

### Options

| Option | Description |
|--------|-------------|
| **A1. Keep at root** | Leave file at repo root |
| **A2. Move under governance/** | `git mv` to `governance/motadata-coder-a-complete-guide_v1.7.md` |

### Pros / Cons

| Option | Pros | Cons |
|--------|------|------|
| **A1. Keep at root** | Easy to discover; root README/linking already works; no reference churn | Root clutter; diverges from TARGET_LAYOUT; doctrine split between root and governance |
| **A2. governance/** | Aligns with 4-layer layout; doctrine co-located; cleaner root | Requires reference updates; maintainers must learn new path; breakage risk if refs missed |

### Maintainability, discoverability, risk

- **Maintainers:** Root → simpler paths; governance/ → clearer Layer-1 semantics.
- **Discoverability:** Root → obvious for new contributors; governance/ → clearer for governance-first workflows.
- **Risk:** High (per RISK_MAP). Primary guide is critical; any bad move hurts judgment/compilation workflows.

### Exact reference update impact

**Top referencing files** (from REFERENCE_UPDATE_MAP, repo_audit, plan docs):

1. repo_audit/DOC_INDEX.md  
2. repo_audit/DUPLICATES_NEAR.md  
3. repo_audit/INDEX_TREE.md  
4. repo_audit/MOVE_PLAN.md  
5. repo_audit/ORPHANS.md  
6. repo_audit/RISK_MAP.md  
7. repo_reorg_plan/* (CURRENT_STATE, CANONICALS, CHECKLIST, ORPHAN_TRIAGE, MOVESET_PLAN, etc.)  
8. docs/status/COMPLETE_SESSION_SUMMARY_FEB6.md  
9. governance review packages (indirect; they reference v1.5, not v1.7 path)

**Note:** Few docs reference the v1.7 path directly; many still cite v1.5. Moving v1.7 may cause low direct breakage today but increases confusion if v1.5 refs are not also migrated.

**Breakage risk if not updated:** Low–medium. Direct v1.7 path refs are sparse; risk is mainly from external links or scripts using root path.

### Recommended choice + alternatives

| Choice | Rationale |
|--------|-----------|
| **Recommended:** A1 (keep at root) | Lower risk; v1.7 is primary but refs are still v1.5-heavy; moving would require coordinated ref update |
| **Safe alternative:** A2 (move to governance) | Only if you plan a full ref migration (v1.5 → v1.7 + path update) in one change |
| **Do nothing:** A1 | Explicit no-op; leave at root until refs are standardized |

### Rollback plan

If moved to governance/ and rollback needed:

```bash
git mv governance/motadata-coder-a-complete-guide_v1.7.md .
# Revert any reference updates (sed/perl in reverse or git checkout -- <files>)
```

---

## 2) Decision B — Treatment of older guides (e.g., v1.5)

**File:** `ml/training/sft/exemplars/guides/Golden_Exemplars_Guide_v1.5.md` (superseded by v1.7)

### Options

| Option | Description |
|--------|-------------|
| **B1. Keep as historical reference** | Leave in guides/; treat as fallback for reviewers who need v1.5 |
| **B2. Archive to governance_history** | `git mv` to `archive/by_topic/governance_history/Golden_Exemplars_Guide_v1.5.md` |
| **B3. Keep + redirect** | Keep in place but add README/note: "v1.7 is canonical; v1.5 historical only" |

### Criteria for “historical canonical”

A guide is **historical canonical** if:

- It is explicitly superseded by a newer version (v1.7).
- It is still cited by governance/review packages for Phase-01 deep questions.
- Moving it would break many references.

v1.5 meets all three: superseded, heavily referenced, high breakage if moved without updates.

### Reference impact

**Top ~20 files that reference v1.5** (from REFERENCE_UPDATE_MAP, DUPLICATE_RESOLUTION_PLAN):

1. governance/review-packages/Phase-01_Review_Package/DISTRIBUTION_SUMMARY.txt  
2. governance/review-packages/Phase-01_Review_Package/PACKAGE_MANIFEST.md  
3. governance/review-packages/Phase-01_Review_Package/COORDINATOR_QUICK_START.md  
4. governance/review-packages/Phase-01_Review_Package/01_START_HERE/PHASE_01_REVIEW_GUIDE.md  
5. governance/review-packages/Phase-01_Review_Package/README.md  
6. governance/golden-exemplars/Phases/Phase-01/PHASE_01_REVIEW_GUIDE.md  
7. governance/golden-exemplars/Phases/Phase-01/REVIEW_DISTRIBUTION_SUMMARY.md  
8. ml/training/sft/exemplars/guides/README.md  
9. ml/training/sft/exemplars/guides/CLEANUP_SUMMARY.md  
10. ml/training/sft/exemplars/guides/DOCUMENTATION_AUDIT_REPORT.md  
11. ml/training/sft/exemplars/guides/JUDGMENT_SYSTEM_README.md  
12. ml/training/sft/exemplars/guides/Reviewer_Pack_v1.0_README.md  
13. ml/training/sft/exemplars/guides/archives/README.md  
14. ml/training/sft/exemplars/guides/archives/session-reports/*.md  
15. docs/status/COMPLETE_SESSION_SUMMARY_FEB6.md  
16. MIGRATION_NOTES.md, QUICK_REFERENCE.md, sft/README.md (per DUPLICATE_RESOLUTION_PLAN)

**Breakage risk:** High. Many governance and guides docs use v1.5 as the main authoring reference.

### Recommended placement

| Choice | Rationale |
|--------|-----------|
| **Recommended:** B1 (keep as historical reference) | Avoid ref churn; governance packages depend on v1.5; migration to v1.7 is a separate task |
| **Alternative:** B2 (archive) | Only after migrating all refs from v1.5 to v1.7 (or to archived path) |
| **Alternative:** B3 | Keep in place + add a canonical note pointing to v1.7; reduces confusion without moves |

---

## 3) Decision C — Placement of GREG attack results / adversarial reports

**File:** `GREG_Pre-Review_Attack_Result.md` (currently at repo root)

### Options

| Option | Description |
|--------|-------------|
| **C1. governance/golden-exemplars/GREG/** | Co-locate with GREG-Initiation-Ratification, GREG-Pre-Review-Package |
| **C2. observation/** | Layer-4 probe/drift/audit; adversarial results as "observation" |
| **C3. archive/** | Treat as historical; e.g. `archive/by_topic/governance_history` |
| **C4. Keep at root** | No move |

### Rationale: who needs it, when, how often

| Audience | When | How often |
|----------|------|-----------|
| GREG ratifiers | Pre-ratification review | Once per GREG cycle |
| Phase gate reviewers | Phase-06 lock / mutation stability | Per phase progression |
| Maintainers | Mutation stability / attack landscape | Rarely, for context |

**Reference:** `governance/golden-exemplars/GREG/GREG-Initiation-Ratification-v0.9.md` cites it: "8 attacks, READY FOR GREG."

### Recommended placement

| Choice | Rationale |
|--------|-----------|
| **Recommended:** C1 (governance/golden-exemplars/GREG/) | Directly supports GREG ratification; used in Phase-06 lock; belongs with GREG doctrine |
| **Alternative:** C4 (keep at root) | No ref churn; single known reference (GREG-Initiation-Ratification) can be updated easily |
| **Alternative:** C2 (observation/) | Fits Layer-4 semantics but divorces from GREG docs; weaker discoverability for ratification workflow |

---

## 4) Decision D — Mutation specs / phase ladders near-duplicate consolidation

**Source:** DUPLICATE_RESOLUTION_PLAN, CANONICALS

### Canonical naming standard

| Scope | Canonical prefix | Location |
|-------|------------------|----------|
| Stage-6C (agent-loop harness) | PHASE6C_* | ml/.../phase6c/ |
| Stage-6B (compilation) | PHASE6B_* | PHASE6B_COLLAPSE_TAXONOMY, PHASE6B_PHASE_HARDENING_SPEC |
| General Phase-6 taxonomy | PHASE6_MUTATION_TAXONOMY | ml/.../ (Motadata) |

### Near-duplicate groups

1. **PHASE6_MUTATION_REPORT vs PHASE6_MUTATION_REPORT_STAGE6B**  
   - Different scope; archive PHASE6_MUTATION_REPORT only if STAGE6B fully supersedes it.

2. **PHASE6_MUTATION_TAXONOMY vs PHASE6C_MUTATION_TAXONOMY**  
   - Not duplicates; different scopes (general vs loop-induced collapse). Keep both.

3. **smoke_traces.jsonl** (out/, out_m3/, out_m4/)  
   - Likely distinct runs; hash to confirm before archiving duplicates.

### Archive policy for older iterations

- **deprecated_mutation:** For mutation specs that are superseded (e.g. PHASE6_MUTATION_REPORT if STAGE6B replaces it).
- **Keep in place:** PHASE6B_*, PHASE6C_*, PHASE6_MUTATION_TAXONOMY until supersession is confirmed.
- **Do not archive** without explicit decision; mutation specs are high-risk.

### Risk controls

- Do not move or rename mutation specs without human approval.
- Do not archive PHASE6* until supersession is documented.
- Run hash script (EXECUTE=1) before archiving any smoke_traces.jsonl copies.

---

## 5) Human Decisions Required — Checklist

Items marked `needs_decision` in MOVESET_PLAN.jsonl:

| # | Source path | Decision needed | Default if forced |
|---|-------------|-----------------|-------------------|
| 1 | **motadata-coder-a-complete-guide_v1.7.md** | Keep at root vs move to governance/ | Keep at root |
| 2 | **GREG_Pre-Review_Attack_Result.md** | Keep at root vs move to governance/golden-exemplars/GREG/ | Keep at root |
| 3 | **Golden_Exemplars_Guide_v1.5.md** | Keep in guides/ vs archive to governance_history | Keep in guides/ |

### Additional decisions (from DUPLICATE_RESOLUTION_PLAN, not in MOVESET_PLAN)

| # | Item | Decision needed | Default if forced |
|---|------|-----------------|-------------------|
| 4 | **smoke_traces.jsonl** (out/, out_m3/, out_m4/) | Archive duplicates after hash? | Keep all (assume distinct runs) |
| 5 | **EXEMPLAR_AUTHORING_GUIDE** (2 copies) | Archive one/both to draft_docs/misc_orphans? | Keep both in place |
| 6 | **PHASE6_MUTATION_REPORT vs PHASE6_MUTATION_REPORT_STAGE6B** | Archive PHASE6_MUTATION_REPORT? | Keep both |

---

*End of Wave-2 Decision Pack*
