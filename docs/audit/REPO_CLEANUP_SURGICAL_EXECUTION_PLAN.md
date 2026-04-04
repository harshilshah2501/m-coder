# Repo Cleanup Surgical Execution Plan

**Generated:** 2026-03-24  
**Doc status:** canonical-current (execution plan)  
**Parent:** `REPO_STRUCTURAL_SURVEY_AND_HEALTH_REPORT.md`

---

## Overview

This document transforms the survey findings into a sequenced, executable plan. Each task is:
- **Atomic**: Can be done in a single PR
- **Verifiable**: Has clear pass/fail criteria
- **Reversible**: Can be undone if issues arise
- **Ordered**: Dependencies are explicit

---

## Execution Waves

| Wave | Focus | Risk | PRs | Effort |
|------|-------|------|-----|--------|
| **Wave 1** | Root cleanup + orphan files | Low | 2-3 | Small |
| **Wave 2** | Doc deduplication + archival | Low | 3-4 | Medium |
| **Wave 3** | Naming collision fix (`runtime/observation/`) | Medium | 1-2 | Medium |
| **Wave 4** | Doc index + navigation | Low | 1-2 | Small |
| **Wave 5** | Spike archival + structure polish | Low | 1-2 | Small |
| **Wave 6** | Repo-intel tool foundation | Medium | 2-3 | Medium |

**Total estimated PRs:** 10-16  
**Recommended pacing:** 1-2 PRs per session

---

## Wave 1: Root Cleanup + Orphan Files

**Objective:** Clean the repository root; relocate misplaced files

### Task 1.1: Clean Root README.md

**File:** `/workspace/README.md`

**Current state:** Contains ~360 lines including:
- System overview (good)
- Backup system documentation (wrong place)
- Iteration notes and troubleshooting (wrong place)
- Training solution options (wrong place)

**Action:** Rewrite to contain only:
1. Project title and 1-paragraph description
2. Current system status (4-layer summary)
3. Quick start section (essential commands only)
4. Navigation links to canonical docs
5. Brief model/dataset artifact note

**Target length:** ~80-100 lines

**Verification:**
```bash
wc -l README.md  # Should be < 120 lines
grep -c "backup" README.md  # Should be 0
grep -c "Iter10\|Iter11\|Iter12" README.md  # Should be 0
```

**PR:** `cleanup/wave1-root-readme`

---

### Task 1.2: Relocate Root-Level Files

**Files to move:**

| File | From | To | Rationale |
|------|------|-----|-----------|
| `AGENT_EXECUTION_RULES.md` | `/` | `docs/governance/` | Governance-adjacent doc |
| `Hardware-Profile.md` | `/` | `docs/reference/` | Reference material |
| `cuda-pytorch_test.py` | `/` | `scripts/` or delete | Orphan test script |

**Actions:**
```bash
# Create reference directory if needed
mkdir -p docs/reference

# Move files (preserving git history)
git mv AGENT_EXECUTION_RULES.md docs/governance/
git mv Hardware-Profile.md docs/reference/
git mv cuda-pytorch_test.py scripts/  # or: git rm cuda-pytorch_test.py
```

**Verification:**
```bash
ls -la *.md *.py 2>/dev/null | grep -v README  # Should show only Makefile-related or nothing
```

**PR:** `cleanup/wave1-relocate-root-files`

---

### Task 1.3: Remove Empty/Broken Files

**Files to delete:**

| File | Reason |
|------|--------|
| `docs/effort-benefits-risks_analysis.md` | 0 bytes (empty) |
| `runtime/rag/=0.13.0` | Artifact from failed pip install |

**Actions:**
```bash
git rm docs/effort-benefits-risks_analysis.md
git rm "runtime/rag/=0.13.0"
```

**Verification:**
```bash
find /workspace -empty -type f -name "*.md"  # Should return nothing
```

**PR:** Can be combined with Task 1.2

---

## Wave 2: Doc Deduplication + Archival

**Objective:** Eliminate duplicate docs; archive stale materials

### Task 2.1: Deduplicate Training/Dataset Docs

**Duplicate pairs identified:**

| Canonical Location | Duplicate Location | Action |
|-------------------|-------------------|--------|
| `ml/datasets/V15_FINAL_DATASET_SUMMARY.md` | `archive/okr/supporting-docs/V15_FINAL_DATASET_SUMMARY.md` | Keep in `ml/`, verify archive copy exists |
| `ml/datasets/V17_DATASET_SUMMARY.md` | `archive/okr/supporting-docs/V17_DATASET_SUMMARY.md` | Keep in `ml/`, verify archive copy exists |

**Verification:** These are already properly duplicated (one live, one archived). No action needed unless the archive version is missing.

```bash
diff ml/datasets/V15_FINAL_DATASET_SUMMARY.md archive/okr/supporting-docs/V15_FINAL_DATASET_SUMMARY.md
# If identical or archive is older, no action needed
```

**PR:** `cleanup/wave2-verify-dataset-docs` (if changes needed)

---

### Task 2.2: Deduplicate Status Docs

**Duplicate pairs:**

| File | Location 1 | Location 2 | Action |
|------|-----------|-----------|--------|
| `STREAMING_FIX_SUMMARY.md` | `docs/status/` | `archive/okr/supporting-docs/` | Archive `docs/status/` version |
| `TRAINING_MONITOR.md` | `docs/status/` | `archive/okr/supporting-docs/` | Archive `docs/status/` version |

**Actions:**
```bash
# Verify archive versions exist and are equivalent or newer
diff docs/status/STREAMING_FIX_SUMMARY.md archive/okr/supporting-docs/STREAMING_FIX_SUMMARY.md
diff docs/status/TRAINING_MONITOR.md archive/okr/supporting-docs/TRAINING_MONITOR.md

# If archive is good, remove from docs/status/
git rm docs/status/STREAMING_FIX_SUMMARY.md
git rm docs/status/TRAINING_MONITOR.md
```

**Verification:**
```bash
find /workspace -name "STREAMING_FIX_SUMMARY.md" | wc -l  # Should be 1
find /workspace -name "TRAINING_MONITOR.md" | wc -l  # Should be 1
```

**PR:** `cleanup/wave2-dedup-status-docs`

---

### Task 2.3: Deduplicate Guide Docs

**Duplicate pairs:**

| File | Location 1 | Location 2 | Action |
|------|-----------|-----------|--------|
| `KPI-Implementation-Quick-Start.md` | `docs/evaluation/` | `docs/guides/` | Keep in `docs/guides/`, remove from `docs/evaluation/` |
| `ORCHESTRATOR_SERVICE_GUIDE.md` | `docs/guides/` | `archive/okr/supporting-docs/` | Verify archive, keep canonical in `docs/guides/` |

**Actions:**
```bash
# Compare and keep the more complete version
diff docs/evaluation/KPI-Implementation-Quick-Start.md docs/guides/KPI-Implementation-Quick-Start.md

# Remove duplicate (keep guides version as it's more discoverable)
git rm docs/evaluation/KPI-Implementation-Quick-Start.md
```

**PR:** `cleanup/wave2-dedup-guide-docs`

---

### Task 2.4: Archive Stale docs/status/ Directory

**Current state:** `docs/status/` contains status snapshots that are point-in-time

**Contents:**
- `COMPLETE_SESSION_SUMMARY_FEB6.md`
- `progress-2026-01-08.md`
- `README.md`
- `STREAMING_FIX_SUMMARY.md` (to be removed in 2.2)
- `TRAINING_MONITOR.md` (to be removed in 2.2)

**Action:** Archive entire directory after removing duplicates

```bash
# After Task 2.2 completes
mkdir -p archive/docs/status
git mv docs/status/* archive/docs/status/
rmdir docs/status
```

**Verification:**
```bash
ls docs/status 2>/dev/null  # Should fail (directory gone)
ls archive/docs/status/  # Should show moved files
```

**PR:** `cleanup/wave2-archive-status-dir`

---

### Task 2.5: Archive Stale docs/iterations/ Directory

**Current state:** `docs/iterations/` contains historical iteration analyses

**Contents:**
- `AGENTIC_FRAMEWORK_MASTER.md`
- `BALANCED_OPTIMIZATION_SUMMARY.md`
- `COMPARISON_BEFORE_AFTER.md`
- `COMPLETE_ITERATIONS_ANALYSIS.md`
- `OPTION_A_COMPLETION_SUMMARY.md`

**Action:** Archive entire directory

```bash
mkdir -p archive/docs/iterations
git mv docs/iterations/* archive/docs/iterations/
rmdir docs/iterations
```

**PR:** `cleanup/wave2-archive-iterations-dir`

---

### Task 2.6: Thin Out docs/audit/

**Current state:** 30+ audit reports accumulated from prior cleanup passes

**Strategy:** Keep only:
1. Current survey report (`REPO_STRUCTURAL_SURVEY_AND_HEALTH_REPORT.md`)
2. This execution plan (`REPO_CLEANUP_SURGICAL_EXECUTION_PLAN.md`)
3. Most recent per-layer audits (1 each for L1-L4)
4. Active remediation plans

**Files to archive:**

| Keep | Archive |
|------|---------|
| `REPO_STRUCTURAL_SURVEY_AND_HEALTH_REPORT.md` | `ARCHIVE_EXPORT_EXECUTION_PLAN.md` |
| `REPO_CLEANUP_SURGICAL_EXECUTION_PLAN.md` | `BATCH_*_EXECUTION_REPORT.md` (all) |
| `END_TO_END_SYSTEM_AUDIT_REPORT.md` | `PHASE_14*_*.md` (all) |
| `SURGICAL_NEXT_STEPS_PLAN.md` | `PHASE_15*_*.md` (all) |
| Per-layer audits (L1-L4) | Older structural reports |

**Action:**
```bash
mkdir -p archive/docs/audit

# Move older batch reports
git mv docs/audit/BATCH_*_EXECUTION_REPORT.md archive/docs/audit/
git mv docs/audit/PHASE_14*_*.md archive/docs/audit/
git mv docs/audit/PHASE_15*_*.md archive/docs/audit/
git mv docs/audit/ARCHIVE_EXPORT_EXECUTION_PLAN.md archive/docs/audit/

# Keep: LAYER*_AUDIT.md, END_TO_END_*, SURGICAL_*, REPO_*
```

**PR:** `cleanup/wave2-thin-audit-dir`

---

## Wave 3: Naming Collision Fix

**Objective:** Resolve `runtime/observation/` vs `observation/` naming collision

### Task 3.1: Rename runtime/observation/ to runtime/runtime_metrics/

**Rationale:**
- Top-level `observation/` = Layer-4 (drift detection, baselines, audit)
- `runtime/observation/` = Runtime metric collection, GREG bundles, collapse vectors
- Rename eliminates confusion about ownership

**Scope:**
- Directory: `runtime/observation/` → `runtime/runtime_metrics/`
- ~20 Python files affected
- Import statements need updating across runtime/

**Pre-flight checks:**
```bash
# Find all imports of runtime.observation
grep -r "from runtime.observation" /workspace --include="*.py" | wc -l
grep -r "import runtime.observation" /workspace --include="*.py" | wc -l
grep -r "runtime\.observation" /workspace --include="*.py" | wc -l
```

**Actions:**
```bash
# 1. Rename directory
git mv runtime/observation runtime/runtime_metrics

# 2. Update all imports (use sed or IDE refactor)
find /workspace -name "*.py" -exec sed -i 's/runtime\.observation/runtime.runtime_metrics/g' {} \;
find /workspace -name "*.py" -exec sed -i 's/from runtime\.observation/from runtime.runtime_metrics/g' {} \;

# 3. Update __init__.py if needed
# 4. Update any docs referencing the path
```

**Verification:**
```bash
# No remaining references to old path
grep -r "runtime\.observation" /workspace --include="*.py" | grep -v runtime_metrics  # Should be empty
grep -r "runtime/observation" /workspace --include="*.md"  # Update these docs

# Tests pass
python -m pytest runtime/tests/ -v --tb=short
```

**Risk mitigation:**
- Run full test suite before and after
- Keep a list of changed files for rollback
- Do in isolated PR

**PR:** `cleanup/wave3-rename-runtime-observation`

---

### Task 3.2: Update Documentation References

**After Task 3.1, update docs:**

| Doc | Section to update |
|-----|------------------|
| `docs/ARCHITECTURE_4_LAYER.md` | Layer-3 allowed list |
| `docs/LAYER3_RUNTIME_SPEC.md` | Component references |
| `docs/runtime/README.md` | Directory listing |
| `runtime/README.md` | Component references |

**PR:** Can be combined with Task 3.1 or separate

---

## Wave 4: Doc Index + Navigation

**Objective:** Improve doc discoverability

### Task 4.1: Create docs/INDEX.md

**Content:** Categorized index of all canonical docs

```markdown
# Documentation Index

## Entry Points
- [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md) — Canonical system specification
- [ARCHITECTURE_4_LAYER.md](ARCHITECTURE_4_LAYER.md) — 4-layer architecture
- [LIVE_ROADMAP_TRACKER.md](LIVE_ROADMAP_TRACKER.md) — Milestone tracker

## Layer Specifications
- [LAYER1_GOVERNANCE_SPEC.md](LAYER1_GOVERNANCE_SPEC.md)
- [LAYER2_COMPILATION_SPEC.md](LAYER2_COMPILATION_SPEC.md)
- [LAYER3_RUNTIME_SPEC.md](LAYER3_RUNTIME_SPEC.md)
- [LAYER4_OBSERVATION_SPEC.md](LAYER4_OBSERVATION_SPEC.md)

## By Topic
### Governance
- [governance/README.md](../governance/README.md)
- [GLOSSARY.md](GLOSSARY.md)
...

### Runtime
- [runtime/README.md](runtime/README.md)
- [RUNTIME_PLAN_AND_LEDGER_V0_1.md](RUNTIME_PLAN_AND_LEDGER_V0_1.md)
...

### Guides
- [guides/E2E-flow.md](guides/E2E-flow.md)
- [guides/INTEGRATION_GUIDE.md](guides/INTEGRATION_GUIDE.md)
...
```

**PR:** `cleanup/wave4-doc-index`

---

### Task 4.2: Update docs/README.md

**Current state:** Thin or generic

**Action:** Make it a proper navigation hub pointing to INDEX.md and key entry points

**PR:** Can be combined with Task 4.1

---

## Wave 5: Spike Archival + Structure Polish

**Objective:** Clean up abandoned spikes; finalize structure

### Task 5.1: Archive workspace_intelligence/

**Current state:** `workspace_intelligence/` appears to be an early spike superseded by `runtime/layer5/`

**Contents:**
- `__init__.py`
- `spikes/README.md`

**Action:**
```bash
mkdir -p archive/spikes
git mv workspace_intelligence archive/spikes/workspace_intelligence
```

**Verification:**
```bash
ls workspace_intelligence 2>/dev/null  # Should fail
ls archive/spikes/workspace_intelligence/  # Should show files
```

**PR:** `cleanup/wave5-archive-workspace-intel`

---

### Task 5.2: Verify Layer-5 Consolidation

**Current state:** `runtime/layer5/` is the active Layer-5 implementation

**Action:** Ensure no orphan references to `workspace_intelligence` remain

```bash
grep -r "workspace_intelligence" /workspace --include="*.py" --include="*.md"
# Update any found references to point to runtime/layer5/
```

**PR:** Can be combined with Task 5.1

---

### Task 5.3: Create docs/reference/ if Missing

**Action:** Ensure `docs/reference/` exists for operational docs

```bash
mkdir -p docs/reference
# Already created in Wave 1 if Hardware-Profile.md was moved
```

**PR:** Part of Wave 1

---

## Wave 6: Repo-Intel Tool Foundation

**Objective:** Create lightweight tooling for repo navigation

### Task 6.1: Create Layer Map Data File

**File:** `scripts/repo_intel/layer_map.json`

```json
{
  "schema_version": "layer_map.v1",
  "layers": {
    "1": {
      "name": "Governance",
      "directories": ["governance/"],
      "doc_prefix": "LAYER1_"
    },
    "2": {
      "name": "ML Compilation", 
      "directories": ["ml/"],
      "doc_prefix": "LAYER2_"
    },
    "3": {
      "name": "Runtime",
      "directories": ["runtime/"],
      "doc_prefix": "LAYER3_"
    },
    "4": {
      "name": "Observation",
      "directories": ["observation/"],
      "doc_prefix": "LAYER4_"
    },
    "5": {
      "name": "Workspace Intelligence",
      "directories": ["runtime/layer5/"],
      "doc_prefix": "L5"
    }
  },
  "archive": ["archive/"],
  "docs": ["docs/"],
  "support": ["scripts/", "tests/", "packaging/", "jetbrains-plugin/"]
}
```

**PR:** `cleanup/wave6-layer-map`

---

### Task 6.2: Create Canonical Files Registry

**File:** `scripts/repo_intel/canonical_files.json`

```json
{
  "schema_version": "canonical_files.v1",
  "canonical_docs": [
    "docs/MASTER_SYSTEM_SPEC.md",
    "docs/ARCHITECTURE_4_LAYER.md",
    "docs/LIVE_ROADMAP_TRACKER.md",
    "docs/LAYER1_GOVERNANCE_SPEC.md",
    "docs/LAYER2_COMPILATION_SPEC.md",
    "docs/LAYER3_RUNTIME_SPEC.md",
    "docs/LAYER4_OBSERVATION_SPEC.md",
    "governance/CONSTITUTIONAL_MANIFEST_v1.0.md"
  ],
  "canonical_schemas": [
    "runtime/schemas/plan.v0.1.schema.json",
    "runtime/schemas/ledger_row.v0.1.schema.json",
    "runtime/schemas/task.v0.1.schema.json",
    "runtime/layer5/evidence/evidence_bundle.v1.schema.json"
  ]
}
```

**PR:** Can be combined with Task 6.1

---

### Task 6.3: Create Basic repo-intel CLI

**File:** `scripts/repo_intel.py`

**Minimal v1 features:**
```bash
repo-intel <path>           # Show layer, status, related docs
repo-intel --layer 3        # List Layer-3 directories
repo-intel --canonical      # List canonical files
repo-intel --violations     # Find known issues
```

**Implementation:** ~200 lines Python, reads JSON data files

**PR:** `cleanup/wave6-repo-intel-cli`

---

## Execution Checklist

### Wave 1 Checklist
- [ ] Task 1.1: Clean root README.md
- [ ] Task 1.2: Relocate root-level files
- [ ] Task 1.3: Remove empty/broken files

### Wave 2 Checklist
- [ ] Task 2.1: Verify dataset doc duplicates
- [ ] Task 2.2: Deduplicate status docs
- [ ] Task 2.3: Deduplicate guide docs
- [ ] Task 2.4: Archive docs/status/ directory
- [ ] Task 2.5: Archive docs/iterations/ directory
- [ ] Task 2.6: Thin out docs/audit/

### Wave 3 Checklist
- [ ] Task 3.1: Rename runtime/observation/ → runtime/runtime_metrics/
- [ ] Task 3.2: Update documentation references

### Wave 4 Checklist
- [ ] Task 4.1: Create docs/INDEX.md
- [ ] Task 4.2: Update docs/README.md

### Wave 5 Checklist
- [ ] Task 5.1: Archive workspace_intelligence/
- [ ] Task 5.2: Verify Layer-5 consolidation
- [ ] Task 5.3: Ensure docs/reference/ exists

### Wave 6 Checklist
- [ ] Task 6.1: Create layer_map.json
- [ ] Task 6.2: Create canonical_files.json
- [ ] Task 6.3: Create repo-intel CLI

---

## Verification Commands

### After Each Wave

```bash
# Verify no broken imports
python -c "import runtime" 2>&1 | grep -i error

# Verify tests still pass
python -m pytest runtime/tests/ -v --tb=short -q

# Verify no orphan references
grep -r "REMOVED_FILE_NAME" /workspace --include="*.md" --include="*.py"
```

### Final Verification

```bash
# Count reduction in duplicate files
find /workspace -name "*.md" | xargs -I {} basename {} | sort | uniq -c | sort -rn | head -20

# Verify clean root
ls *.md *.py 2>/dev/null | wc -l  # Should be 1 (README.md only) or 2 with Makefile

# Verify archive structure
ls archive/docs/
ls archive/spikes/
```

---

## Rollback Procedures

### If Import Breaks After Wave 3

```bash
# Revert the rename
git mv runtime/runtime_metrics runtime/observation

# Revert import changes
git checkout HEAD~1 -- $(git diff --name-only HEAD~1 | grep "\.py$")
```

### If Tests Fail

```bash
# Identify failing tests
python -m pytest runtime/tests/ -v --tb=long 2>&1 | tee test_failures.log

# Revert specific files if needed
git checkout HEAD~1 -- <specific_file>
```

---

## Success Criteria

| Metric | Before | After Target |
|--------|--------|--------------|
| Root-level .md files | 4 | 1 (README.md) |
| Duplicate file names (top 5) | 55, 19, 9, 3, 3 | <30, <10, <5, 1, 1 |
| `runtime/observation/` exists | Yes | No (renamed) |
| `workspace_intelligence/` exists | Yes | No (archived) |
| docs/INDEX.md exists | No | Yes |
| Layer map data file exists | No | Yes |
| All tests pass | Yes | Yes |

---

## Timeline Recommendation

| Wave | Estimated Sessions | Dependencies |
|------|-------------------|--------------|
| Wave 1 | 1 session | None |
| Wave 2 | 1-2 sessions | Wave 1 |
| Wave 3 | 1 session | Wave 1, Wave 2 |
| Wave 4 | 1 session | Wave 1, Wave 2 |
| Wave 5 | 1 session | Wave 1 |
| Wave 6 | 1-2 sessions | Waves 1-5 |

**Total:** 6-9 sessions

**Recommended approach:** Complete Waves 1-2 first (low risk, high value), then Wave 3 (medium risk), then Waves 4-6.

---

*End of Surgical Execution Plan*
