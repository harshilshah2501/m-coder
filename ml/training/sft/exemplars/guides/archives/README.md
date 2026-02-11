# Archives — Historical Documentation

**Purpose:** Preserve historical documentation versions and session reports  
**Organization Date:** February 6, 2026  
**Policy:** No documents are deleted, only archived

---

## What's In This Folder

This archive contains **16 documents** organized into 3 categories:

### 1. Session Reports (5 files)

Historical records of major documentation work sessions:

- `IMPLEMENTATION_SUMMARY.md` — Documentation integration details (Feb 6, 2026)
- `INTEGRATION_STATUS.md` — System integration status (Feb 6, 2026)
- `COMPLETION_REPORT.md` — Executive completion summary (Feb 6, 2026)
- `SESSION_SUMMARY.md` — Comprehensive session overview (Feb 6, 2026)
- `CASE_STUDIES_UPDATE_LOG.md` — Case studies update log (Feb 6, 2026)

**Use these to:**
- Understand how the current documentation structure was built
- Review the rationale behind integration decisions
- Track the evolution of the document ecosystem

---

### 2. Legacy Versions — v1.0 through v1.4 (7 files)

Earlier versions of the Golden Exemplars program, superseded by v1.5:

- `GOLDEN_EXEMPLARS_GUIDE.md` — Early complete guide (pre-v1.5)
- `REVIEWER_ENGINEER_GUIDE.md` — Early review guidance
- `REVIEW_CHECKLIST.md` — Early review checklist
- `DNA_REVIEWER_EXERCISE.md` — Early D.N.A exercise
- `GATES_CLARIFICATION.md` — Early gate terminology
- `TAXONOMY_REFERENCE.md` — Early taxonomy
- `DATASET_TAXONOMY_REFERENCE.md` — Early dataset taxonomy

**Key Differences from v1.5:**
- Mentioned 20-30 exemplars (v1.5 has 35)
- Less mature phase semantics (no Phase-6)
- Different coverage mapping structure
- No integration with Reviewer Pack

**Use these to:**
- Understand the program's evolution
- See how judgment frameworks matured over time
- Reference early decisions if questions arise

---

### 3. Engineering-First Regrounding Era (4 files)

Documents from the strategic pivot to engineering artifacts:

- `EXEMPLAR_AUTHORING_GUIDE.md` — Engineering-first authoring
- `GROUNDING_TRANSFORMATION_REFERENCE.md` — Ops→Engineering mapping
- `REGROUNDING_HYPOTHESIS.md` — Regrounding strategy
- `REGROUNDING_STRATEGIC_FAQ.md` — Strategic FAQ

**Historical Context:**

The program initially focused on operations/production contexts (alerts, incidents, SLAs). In January 2026, the team pivoted to engineering artifacts (PRs, tests, code reviews, CI/CD). These documents guided that transition.

v1.5 absorbed this shift into a more general framework that works across any context without artificial constraints.

**Use these to:**
- Understand the ops→engineering pivot rationale
- See artifact mapping tables (useful for context)
- Reference the strategic thinking behind the shift

---

## What's NOT In This Folder

### Production Documents (in parent guides/ folder)

The current, authoritative documentation:

1. **JUDGMENT_SYSTEM_README.md** — Entry point (start here)
2. **Golden_Exemplars_Guide_v1.5.md** — Constitutional source
3. **Judgement_Governed_Architecture.md** — System enforcement
4. **Reviewer Pack v1.0** (5 files) — Human validation process

**Always use production documents for:**
- Authoring new exemplars
- Reviewing exemplars
- Understanding current judgment semantics
- Navigating the documentation system

---

## When to Reference Archives

### ✅ Good Reasons to Use Archives

1. **Historical Context:** "How did we get here?"
2. **Decision Rationale:** "Why did we choose this approach?"
3. **Evolution Understanding:** "What changed between versions?"
4. **Audit Trail:** "What decisions were made and when?"

### ❌ Bad Reasons to Use Archives

1. **Authoring New Exemplars** — Use v1.5, not legacy docs
2. **Reviewing Exemplars** — Use Reviewer Pack v1.0
3. **Understanding Current System** — Use production docs
4. **Training New Team Members** — Start with JUDGMENT_SYSTEM_README.md

---

## Archive Maintenance Policy

### Retention

- **Session Reports:** Keep for 1 year, then summarize into change log
- **Legacy Versions:** Keep indefinitely (small file size, historical value)
- **Regrounding Era:** Keep indefinitely (strategic pivot documentation)

### When New Versions Release

When v1.6 is released:
1. Move v1.5 to `archives/legacy-v1.5/`
2. Update parent folder with v1.6 production files
3. Create new audit report in parent folder
4. Update this README with v1.5 archive information

---

## File Listing

```
archives/
├── README.md (this file)
├── session-reports/
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── INTEGRATION_STATUS.md
│   ├── COMPLETION_REPORT.md
│   ├── SESSION_SUMMARY.md
│   └── CASE_STUDIES_UPDATE_LOG.md
├── legacy-v1.0-v1.4/
│   ├── GOLDEN_EXEMPLARS_GUIDE.md
│   ├── REVIEWER_ENGINEER_GUIDE.md
│   ├── REVIEW_CHECKLIST.md
│   ├── DNA_REVIEWER_EXERCISE.md
│   ├── GATES_CLARIFICATION.md
│   ├── TAXONOMY_REFERENCE.md
│   └── DATASET_TAXONOMY_REFERENCE.md
└── engineering-first-regrounding/
    ├── EXEMPLAR_AUTHORING_GUIDE.md
    ├── GROUNDING_TRANSFORMATION_REFERENCE.md
    ├── REGROUNDING_HYPOTHESIS.md
    └── REGROUNDING_STRATEGIC_FAQ.md
```

**Total Archived Files:** 16  
**Total Archive Size:** ~300 KB

---

## Quick Reference

**Need current documentation?** → Go to parent `guides/` folder  
**Starting fresh?** → Read `JUDGMENT_SYSTEM_README.md` in parent folder  
**Authoring exemplar?** → Use `Golden_Exemplars_Guide_v1.5.md`  
**Reviewing exemplar?** → Use Reviewer Pack v1.0 files  
**Understanding history?** → You're in the right place

---

**Archive Created:** February 6, 2026  
**Last Updated:** February 6, 2026  
**Maintained By:** Golden Exemplars Program Team
