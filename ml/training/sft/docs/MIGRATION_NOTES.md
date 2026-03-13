# Documentation Cleanup & Migration Notes

**Date**: January 21, 2026  
**Status**: Updated for new directory structure (golden-exemplars/ → exemplars/)

---

## Directory Restructure (January 2026)

The `golden-exemplars/` directory has been reorganized into `exemplars/` with a clearer structure:

```
exemplars/
├── guides/              ← All authoring and review guides
├── categories/          ← Exemplar files organized by type
│   ├── RCA/
│   ├── Anomaly/
│   ├── Refusal/
│   ├── Constraint/     ← NEW
│   ├── Design/         ← NEW
│   ├── MultiLayer/     ← NEW
│   └── Coding/         ← NEW
└── status/              ← Progress tracking
```

---

## Files Removed (Historical Duplicates)

The following files were removed in prior cleanup (January 20, 2026):

1. ~~`GOLDEN_EXEMPLARS_GUIDE.md`~~ (duplicate)
2. ~~`golden_exemplars_sft_taxonomy_refactored_canonical_guide.md`~~ (duplicate)
3. ~~`how_to_review_golden_exemplars_engineer_guide.md`~~ (duplicate)
4. ~~`sft_golden_exemplars_30_item_authoring_todo.md`~~ (duplicate)

**Verification**: All were byte-for-byte identical to files in the old structure.

---

## Canonical Document Locations (Updated)

### **Core Reference Documents**
- **Philosophy & Overview**: `exemplars/README.md`
- **Complete Authoring Guide**: `exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md`
- **Legacy Reference**: `exemplars/guides/GOLDEN_EXEMPLARS_GUIDE.md`
- **Framework Guide**: `docs/SFT_FRAMEWORK.md`

### **Authoring Workflow**
- **Authoring Guide**: `exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md`
- **Taxonomy Reference**: `exemplars/guides/TAXONOMY.md`
- **Progress Tracker**: `exemplars/status/AUTHORING_TODO.md`
- **Phase Checklist**: `exemplars/status/PHASE_1_CHECKLIST.md`

### **Review & Validation**
- **Comprehensive Review Checklist**: `exemplars/guides/REVIEW_CHECKLIST.md` (9 criteria including 3 D.N.A gates)
- **D.N.A Framework**: `exemplars/guides/DNA_VALIDATION.md`

### **Exemplar Categories** (7 Total)
- **Phase 1 (Complete)**:
  - `exemplars/categories/RCA/` — Root cause analysis (RCA-01, RCA-02)
  - `exemplars/categories/Anomaly/` — Anomaly detection (ANOM-01, ANOM-02)
  - `exemplars/categories/Refusal/` — Safety refusals (REF-01)
  
- **Phase 2+ (Planned)**:
  - `exemplars/categories/Constraint/` — Constraint-aware config (CONF-01–05)
  - `exemplars/categories/Design/` — Design thinking (DES-01–05)
  - `exemplars/categories/MultiLayer/` — Multi-layer pressure (MIX-01–05)
  - `exemplars/categories/Coding/` — Safe code scaffolds (CODE-01–07)

---

## Document Hierarchy (Read in This Order)

### For New Team Members
1. `exemplars/README.md` — What are golden exemplars?
2. `docs/SFT_FRAMEWORK.md` — Why this approach? (B.R.A.I.N → D.N.A framework)
3. `exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md` — Complete authoring reference
4. Browse locked exemplars: `exemplars/categories/RCA/RCA-01.md`, `exemplars/categories/Refusal/REF-01.md`

### For Exemplar Authors
1. `exemplars/guides/EXEMPLAR_AUTHORING_GUIDE.md` — Comprehensive authoring guide with chronology
2. `exemplars/guides/TAXONOMY.md` — Category taxonomy and stress-surface mapping
3. `exemplars/status/AUTHORING_TODO.md` — Track your progress

### For Reviewers
1. `exemplars/guides/REVIEW_CHECKLIST.md` — 9 comprehensive review criteria (includes 3 D.N.A gates)
2. `exemplars/guides/GOLDEN_EXEMPLARS_GUIDE.md` — Detailed reference
3. `exemplars/guides/DNA_VALIDATION.md` — D.N.A validation framework (Decomposition, Negative Capability, Adversarial Swap)

---

## What Changed in Structure

Updated `training/sft/` to:
- ✅ Reorganize golden-exemplars/ → exemplars/ with clear subdirectories
- ✅ Separate guides/, categories/, and status/ for clarity
- ✅ Add 4 new category folders (Constraint, Design, MultiLayer, Coding)
- ✅ Update all cross-references in documentation
- ✅ Create comprehensive READMEs for each new category
- ✅ Update category taxonomy from 5 to 7 categories

---

## Breaking Changes

**Path Changes**: All references to `golden-exemplars/` should now use `exemplars/` with appropriate subdirectories:
- `golden-exemplars/RCA/` → `exemplars/categories/RCA/`
- `golden-exemplars/GOLDEN_EXEMPLARS_GUIDE.md` → `exemplars/guides/GOLDEN_EXEMPLARS_GUIDE.md`
- File paths updated in all documentation

**Category Changes**: Category taxonomy expanded from 5 to 7:
- Old: RCA, Anomaly, Config, Refusal, Mixed
- New: RCA, Anomaly, Refusal, Constraint, Design, MultiLayer, Coding

If you have external references or bookmarks, update them to reflect the new structure.

---

## File Count Summary

**January 20, 2026**: 30 files → 27 files (removed 3 duplicates)  
**January 21, 2026**: Added 4 new category directories with READMEs  
**Current Structure**: 7 category directories, organized guides/, clearer navigation

---

## Next Steps

1. **Verify links**: All internal documentation updated; check external references
2. **Update bookmarks**: Point to new `exemplars/` structure
3. **Continue authoring**: Begin Phase-2 CONF exemplars using new category structure
4. **No code changes required**: This was documentation organization only
