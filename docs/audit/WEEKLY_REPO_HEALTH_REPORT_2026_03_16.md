# Weekly Repository Health Report — 2026-03-16

## 1. Purpose

This is the weekly m-coder repository health and consistency audit. This audit inspects the repository for drift against established structural rules, documentation conventions, and hygiene expectations.

**Audit date**: 2026-03-16  
**Auditor**: Automated weekly audit  
**Branch**: `cursor/weekly-repo-health-audit-a4b6` (base: `main`)  
**Last commit**: `92768e2` — Post-merge: tracker updated for M4.x on main; M4X_MAIN_MERGE_COMPLETION.md

---

## 2. Executive Summary

| Metric | Status |
|--------|--------|
| **Overall repo health** | ATTENTION NEEDED |
| **Most important issue** | Root-level planning files and debug artifacts still tracked |
| **Tiny safe fixes applied** | None (report-only audit) |

### Key Observations

- **M4.x milestone series (M4.1–M4.6) successfully merged to main** on 2026-03-15 with proper documentation in `docs/reports/M4X_MAIN_MERGE_COMPLETION.md`
- **Root hygiene has minor drift**: 3 planning prompt files and 1 debug tail artifact remain tracked at root level
- **Docs spine is coherent**: `MASTER_SYSTEM_SPEC.md`, `LIVE_ROADMAP_TRACKER.md`, and layer specs are aligned
- **No new tracked generated artifacts** detected since last major merge
- **`.gitignore` has a duplicate entry** for `ml/training/datasets/**/golden_exemplars*_*.jsonl` (lines 97-100)
- **File naming issue**: `docs/v16_1eval.xml` contains SVG content, not XML

---

## 3. Root Hygiene Findings

### Files at Root Level

| File | Classification | Issue |
|------|----------------|-------|
| `README.md` | Canonical | OK |
| `Makefile` | Canonical | OK |
| `.gitignore` | Canonical | Duplicate entry (see §4) |
| `AGENT_EXECUTION_RULES.md` | Operational | OK (agent guidance) |
| `Hardware-Profile.md` | Operational | OK |
| `motadata-coder-a-complete-guide_v1.7.md` | Governance doc | Acceptable (referenced by README) |
| `cuda-pytorch_test.py` | Test utility | Minor drift — could live in `tests/` or `scripts/` |
| `plan-artifactSegregation.prompt.md` | **Planning file** | **DRIFT** — should be in `docs/` or `archive/` |
| `plan-stage6cPassToStage7Freeze.prompt.md` | **Planning file** | **DRIFT** — should be in `docs/` or `archive/` |
| `plan-stage6c-ref-sanitizer.prompt.md` | **Planning file** | **DRIFT** — should be in `docs/` or `archive/` |
| `tail_stage6c_ledger.txt` | **Debug artifact** | **DRIFT** — sample JSONL output should not be tracked at root |

### Summary

- **3 planning prompt files** remain tracked at root (legacy from Stage-6C development)
- **1 debug tail artifact** (`tail_stage6c_ledger.txt`, 30 lines) is a sample JSONL ledger output that should not be tracked
- **1 test utility** (`cuda-pytorch_test.py`) at root is minor clutter but tolerable

**Recommendation**: Human review to determine if these should be archived or `.gitignore`d. No auto-fix per audit rules.

---

## 4. Generated Artifact / Large-File Findings

### .gitignore Duplicate Entry

```
Line 97-100 (duplicate):
# Dataset payloads (data-plane)
ml/training/datasets/**/golden_exemplars*_*.jsonl

# Dataset payloads (data-plane)
ml/training/datasets/**/golden_exemplars*_*.jsonl
```

**Issue**: The same pattern appears twice with identical comments. Harmless but indicates copy-paste error.

**Recommendation**: Human review to remove duplicate. No auto-fix per audit rules.

### Large Files in Tracked Directories

| Directory | Size | Notes |
|-----------|------|-------|
| `ml/datasets/` | 247 MB | V17 DPO training data — tracked intentionally |
| `docs/` | 2.1 MB | Documentation — acceptable |
| `archive/` | 14 MB | Archived materials — acceptable |
| `.venv/` | (ignored) | Virtual environment correctly ignored |

### Suspicious Artifacts

| File | Issue |
|------|-------|
| `docs/v16_1eval.xml` (22 KB) | **Misnamed**: Contains SVG content (Mermaid flowchart export), not XML |
| `docs/runtime/verification/SYSTEM_REPOSITORY_SNAPSHOT.json` | OK — snapshot metadata, part of audit system |

**Recommendation**: Consider renaming `docs/v16_1eval.xml` to `.svg` or relocating. No auto-fix per audit rules.

---

## 5. Docs Spine Findings

### Canonical Entry Points

| Document | Status | Last Updated |
|----------|--------|--------------|
| `docs/MASTER_SYSTEM_SPEC.md` | OK | Current |
| `docs/LIVE_ROADMAP_TRACKER.md` | OK | 2026-03-15 |
| `docs/ARCHITECTURE_4_LAYER.md` | OK | Current |
| `docs/LAYER1_GOVERNANCE_SPEC.md` | OK | Current |
| `docs/LAYER2_COMPILATION_SPEC.md` | OK | Current |
| `docs/LAYER3_RUNTIME_SPEC.md` | OK | Current |
| `docs/LAYER4_OBSERVATION_SPEC.md` | OK | Current |

### Governance Source-of-Truth Labels

- `docs/MASTER_SYSTEM_SPEC.md` correctly references `governance/CONSTITUTIONAL_MANIFEST_v1.0.md` as doctrine source
- Doctrine Immutability Clause remains intact
- Layer status in `LIVE_ROADMAP_TRACKER.md` updated for M4.x completion

### docs/README.md Status Drift

The `docs/README.md` contains legacy path references (e.g., `~/Harshil-PoCs/...`) that describe a different directory structure than the current repo. This appears to be historical documentation that predates the 4-layer refactor.

**Recommendation**: Consider updating `docs/README.md` directory structure section to match current repo layout. No auto-fix per audit rules.

---

## 6. Duplicate-Truth Findings

### M4.x Milestone Documentation

The M4.x milestone documentation is properly organized:
- Canonical specs: `docs/runtime/milestones/M4_*.md`
- Merge reports: `docs/reports/M4X_*.md`
- Branch notes: `docs/runtime/branch_execution_notes/`

No duplicate-truth issues detected in M4.x documentation.

### Potential Overlap

| Location | Content | Issue |
|----------|---------|-------|
| `docs/README.md` | V16 training status | Stale — mentions V16.1 training "In Progress" |
| `docs/LIVE_ROADMAP_TRACKER.md` | Layer-2 ML Compilation | Current — correctly shows COMPLETE/LOCKED |

**Recommendation**: The status sections in `docs/README.md` may need refresh to reflect current system state. No auto-fix per audit rules.

---

## 7. Report Placement Findings

### Recently Added Reports (Last 10 Commits)

| File | Location | Convention |
|------|----------|------------|
| `M4X_MAIN_MERGE_COMPLETION.md` | `docs/reports/` | Correct |
| `M4X_MAIN_MERGE_READINESS.md` | `docs/reports/` | Correct |
| `M4X_INTEGRATION_VERIFICATION_REPORT.md` | `docs/reports/` | Correct |
| `M4X_INTEGRATION_FREEZE_REPORT.md` | `docs/reports/` | Correct |
| `M4_1_OBSERVABILITY_CLOSURE.md` through `M4_6_RUNTIME_METRICS.md` | `docs/runtime/milestones/` | Correct |
| `feature-m4.1-observability-closure.md` | `docs/runtime/branch_execution_notes/` | Correct |

**Status**: All recent reports follow established placement conventions.

### docs/audit/ Directory

- Created for this report: `docs/audit/WEEKLY_REPO_HEALTH_REPORT_2026_03_16.md`
- No prior audit reports exist in this location (this is the first weekly audit)

---

## 8. Naming / Path-Contract Findings

### Naming Inconsistencies

| Pattern | Examples | Issue |
|---------|----------|-------|
| Milestone naming | `M3.10_...` vs `M4_1_...` | Mixed underscore vs dot separators |
| File extension | `docs/v16_1eval.xml` | Contains SVG, not XML |

The milestone naming inconsistency (M3.x uses dots, M4.x uses underscores in some cases) is minor and established by convention.

### Path-Contract-Sensitive Changes

Recent changes (M4.x merge) affected:
- `runtime/observation/*.py` — New observation stack modules
- `runtime/tests/test_*.py` — New test files

These changes are properly scoped to Layer-3/Layer-4 runtime paths and do not affect:
- Governance manifest paths
- ML training critical paths
- Canonical docs spine paths

### Stale Reference

The audit plan file `forensic_architectural_audit_plan_256cdb89.plan.md` is referenced in `docs/runtime/verification/SYSTEM_REPOSITORY_SNAPSHOT.json` but does not exist in the repository. This appears to be a reference to a planning document that was not committed.

**Recommendation**: Either commit the referenced plan file or update the snapshot reference. No auto-fix per audit rules.

---

## 9. Tiny Fixes Applied

**None.**

This audit is report-only. All identified issues require human review before modification.

---

## 10. Recommended Follow-Up Actions

### Priority: HIGH

1. **Root hygiene cleanup** (human decision required)
   - Review and decide on disposition of `plan-*.prompt.md` files
   - Review and decide on disposition of `tail_stage6c_ledger.txt`
   - Consider moving `cuda-pytorch_test.py` to `tests/` or `scripts/`

2. **Remove .gitignore duplicate entry**
   - Lines 97-100: duplicate `golden_exemplars*_*.jsonl` pattern
   - Safe to remove duplicate, but requires explicit approval

### Priority: MEDIUM

3. **docs/v16_1eval.xml file extension**
   - File contains SVG content, not XML
   - Consider renaming to `.svg` or relocating

4. **docs/README.md refresh**
   - Directory structure section uses legacy paths
   - Status sections may be stale

### Priority: LOW

5. **Stale reference in SYSTEM_REPOSITORY_SNAPSHOT.json**
   - References non-existent `forensic_architectural_audit_plan_256cdb89.plan.md`
   - Either commit the file or update the reference

---

## 11. Final Status

**REPO HEALTH ATTENTION NEEDED**

The repository is structurally sound and recently completed the M4.x milestone merge successfully. However, root-level hygiene has drifted with tracked planning/debug files that should be reviewed for archival or exclusion. No critical issues or blocking problems detected.

---

*Report generated: 2026-03-16*  
*Audit scope: Full repository health check*  
*Next audit: Weekly*
