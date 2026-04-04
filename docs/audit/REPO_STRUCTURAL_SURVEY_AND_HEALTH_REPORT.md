# m-coder Repo Survey and Structural Health Report

**Generated:** 2026-03-24  
**Doc status:** canonical-current (planning pass)

---

## 1. Executive Judgment

### Overall Repo State

**Grade: B+ (Structurally Sound, Cleanup Needed)**

The m-coder repository demonstrates strong architectural discipline around its 4-layer model. The canonical layer boundaries are well-documented, governance doctrine is locked, and the Layer-2 compilation pipeline is complete. However, significant structural debt has accumulated:

- **Doc drift and duplication** across multiple areas
- **Stale historical materials** scattered in active paths
- **Naming inconsistencies** between directories (e.g., `observation/` vs `runtime/observation/`)
- **Root-level clutter** with mixed-purpose files
- **Cross-layer code placement** requiring attention

### Main Strengths

1. **Clear 4-layer doctrine**: Governance, ML, Runtime, Observation boundaries are well-defined
2. **Strong canonical entry points**: `docs/MASTER_SYSTEM_SPEC.md`, `docs/ARCHITECTURE_4_LAYER.md`
3. **Mature ML pipeline**: Stages 1-8 complete with freeze certificates
4. **Functioning archive system**: `archive/` properly isolates historical material
5. **Schema-driven contracts**: JSON schemas exist for plan, ledger, IDE, shadow protocols
6. **Comprehensive test coverage**: ~2,000+ test files across runtime subsystems
7. **Active roadmap tracking**: `docs/LIVE_ROADMAP_TRACKER.md` is artifact-driven

### Main Risks

1. **Doc proliferation**: 588 markdown files, 55 README.md instances — discoverability is degraded
2. **Duplicate content**: Same-named files in multiple locations (V15/V17 docs, training summaries)
3. **Layer-4/Layer-5 boundary blur**: `runtime/observation/` vs `observation/` creates confusion
4. **Root-level pollution**: `README.md` contains unrelated backup system docs and iteration notes
5. **Ghost directories**: `workspace_intelligence/spikes/` appears to be exploratory/abandoned
6. **Audit report accumulation**: `docs/audit/` has 30+ reports from prior cleanup passes

### Cleanup Urgency

**Moderate — Staged cleanup recommended**

The repo is functional. Critical paths work. But cognitive load for new contributors is unnecessarily high. A 4-phase cleanup (tag → mark → relocate → prune) is advisable before significant new development.

---

## 2. Current Repo Structure Survey

### 2.1 Top-Level Layout

```
/workspace/
├── AGENT_EXECUTION_RULES.md       # Governance-adjacent (should be in docs/governance or governance/)
├── cuda-pytorch_test.py           # Orphan test script (should be in tests/ or scripts/)
├── Hardware-Profile.md            # Operational doc (misplaced)
├── Makefile                       # Build entrypoint (OK)
├── MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md   # Canonical master doc (heavy; consider moving to docs/)
├── README.md                      # Polluted with backup system + iteration notes
├── archive/                       # Historical materials (correct placement)
├── docs/                          # Primary documentation tree
├── governance/                    # Layer-1: Constitutional doctrine
├── jetbrains-plugin/              # IDE plugin source
├── ml/                            # Layer-2: ML compilation
├── observation/                   # Layer-4: Drift detection
├── packaging/                     # Deployment artifacts
├── runtime/                       # Layer-3: Enforcement
├── scripts/                       # Operational scripts
├── tests/                         # Top-level tests (sparse)
└── workspace_intelligence/        # Layer-5 spike (unclear status)
```

### 2.2 Major Subtrees

| Directory | File Count | Purpose | Health |
|-----------|------------|---------|--------|
| `docs/` | 236 .md | Documentation | **Cluttered** — needs curation |
| `runtime/` | 14,492+ .py | Layer-3 enforcement | **Active** — well-structured |
| `ml/` | Multiple subdirs | Layer-2 compilation | **Complete** — locked |
| `governance/` | ~50 files | Layer-1 doctrine | **Clean** — properly locked |
| `observation/` | ~80 files | Layer-4 drift | **Active** — coherent |
| `archive/` | ~150 files | Historical | **Correct** — inert material |

### 2.3 Structural Observations

**Positive:**
- 4-layer directories exist at top level as intended
- Each layer has its own README.md with boundary definitions
- Schemas are co-located with their runtime components
- Archive follows append-only principle

**Negative:**
- `runtime/observation/` duplicates Layer-4 concept name (confusing)
- `runtime/layer5/` suggests Layer-5 exists but it's not a top-level directory
- `workspace_intelligence/` appears orphaned
- `packaging/` is nascent but placement is reasonable
- `docs/audit/` has become a dumping ground for cleanup reports

---

## 3. Canonical Architecture Alignment

### 3.1 4-Layer Mapping

| Layer | Expected Directory | Actual Directory | Alignment |
|-------|-------------------|------------------|-----------|
| L1 — Governance | `governance/` | `governance/` | ✅ **Strong** |
| L2 — ML Compilation | `ml/` | `ml/` | ✅ **Strong** |
| L3 — Runtime | `runtime/` | `runtime/` | ✅ **Strong** |
| L4 — Observation | `observation/` | `observation/` + `runtime/observation/` | ⚠️ **Split** |
| L5 — Workspace Intelligence | (emerging) | `runtime/layer5/` + `workspace_intelligence/` | ⚠️ **Fragmented** |

### 3.2 Strong Alignment Areas

1. **Layer-1 (Governance)**: Perfect alignment. `governance/` contains only constitutional materials.
2. **Layer-2 (ML)**: Perfect alignment. `ml/` contains datasets, training, lineage, artifacts.
3. **Layer-3 (Runtime)**: Good alignment. `runtime/` contains enforcement stack.

### 3.3 Drift Zones

1. **Layer-4 Split**:
   - `observation/` (top-level) — baseline, ingest, judge_drift_suite
   - `runtime/observation/` — runtime metrics, collapse vectors, trace builders
   - **Issue**: Names collide; unclear which owns what
   - **Recommendation**: Either merge or rename `runtime/observation/` to `runtime/metrics/`

2. **Layer-5 Fragmentation**:
   - `runtime/layer5/` — active workspace resolver, evidence bundle
   - `workspace_intelligence/` — appears to be an earlier spike
   - **Issue**: Layer-5 identity unclear
   - **Recommendation**: Consolidate under `runtime/layer5/` or promote to top-level

3. **Root-Level Files**:
   - `MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md` — 90KB canonical doc at root
   - `AGENT_EXECUTION_RULES.md` — should be under `docs/governance/`
   - `Hardware-Profile.md` — operational, should be under `docs/`
   - `cuda-pytorch_test.py` — orphan test script

---

## 4. Document Landscape Survey

### 4.1 Canonical Docs (Clear Current)

| Document | Path | Purpose |
|----------|------|---------|
| `MASTER_SYSTEM_SPEC.md` | `docs/` | Canonical entry point |
| `ARCHITECTURE_4_LAYER.md` | `docs/` | Layer boundaries and axes |
| `LIVE_ROADMAP_TRACKER.md` | `docs/` | Artifact-driven milestone tracker |
| `CONSTITUTIONAL_MANIFEST_v1.0.md` | `governance/` | Phase definitions, dominance |
| `LAYER1_GOVERNANCE_SPEC.md` | `docs/` | L1 comprehensive spec |
| `LAYER2_COMPILATION_SPEC.md` | `docs/` | L2 comprehensive spec |
| `LAYER3_RUNTIME_SPEC.md` | `docs/` | L3 comprehensive spec |
| `LAYER4_OBSERVATION_SPEC.md` | `docs/` | L4 comprehensive spec |

### 4.2 Stale / Duplicate / Legacy Docs

| File | Location(s) | Status | Recommendation |
|------|-------------|--------|----------------|
| `V15_FINAL_DATASET_SUMMARY.md` | `ml/datasets/`, `archive/okr/supporting-docs/` | **Duplicate** | Archive one |
| `V17_DATASET_SUMMARY.md` | `ml/datasets/`, `archive/okr/supporting-docs/` | **Duplicate** | Archive one |
| `STREAMING_FIX_SUMMARY.md` | `docs/status/`, `archive/okr/supporting-docs/` | **Duplicate** | Remove from `docs/status/` |
| `TRAINING_MONITOR.md` | `docs/status/`, `archive/okr/supporting-docs/` | **Duplicate** | Remove from `docs/status/` |
| `ORCHESTRATOR_SERVICE_GUIDE.md` | `docs/guides/`, `archive/okr/supporting-docs/` | **Duplicate** | Archive one |
| `Notes.md` (9 instances) | Various | **Scattered** | Review and consolidate |
| `KPI-Implementation-Quick-Start.md` | `docs/evaluation/`, `docs/guides/` | **Duplicate** | Remove from one |

### 4.3 Misplaced Docs

| Document | Current Location | Correct Location |
|----------|-----------------|------------------|
| `AGENT_EXECUTION_RULES.md` | Root | `docs/governance/` or `governance/` |
| `Hardware-Profile.md` | Root | `docs/reference/` |
| `MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md` | Root | `docs/` (keep reference at root) |
| `Backend Production Validation Sheet.md` | `docs/` | `docs/validation/` or `docs/runtime/` |
| `JetBrains Plugin Defect Isolation Sheet.md` | `docs/` | `docs/runtime/` or `docs/troubleshooting/` |

### 4.4 Doc Spine Quality

**Current Entry Path:**
```
README.md (polluted) 
  → docs/MASTER_SYSTEM_SPEC.md (clean)
    → docs/ARCHITECTURE_4_LAYER.md (clean)
      → Layer-specific specs
```

**Issues:**
- Root `README.md` is heavily polluted with iteration notes, backup system docs
- No clear "start here" for new contributors
- `docs/README.md` exists but is thin

**Recommended Doc Spine:**
```
README.md (cleaned — system overview + quick links only)
  → docs/README.md (doc index with clear navigation)
    → docs/MASTER_SYSTEM_SPEC.md (entry)
      → Layer specs
      → Layer-specific READMEs
```

### 4.5 Recommended Doc Actions

1. **Archive**: 30+ audit reports in `docs/audit/` → move older ones to `archive/docs/audit/`
2. **Merge**: Duplicate doc pairs (retain one canonical, archive other)
3. **Relocate**: Misplaced root-level docs to proper directories
4. **Prune**: Empty or near-empty files (`effort-benefits-risks_analysis.md` is 0 bytes)
5. **Index**: Create `docs/INDEX.md` with categorized links

---

## 5. Layer-by-Layer Health Assessment

### 5.1 Layer-1 — Governance

**Status:** ✅ **LOCKED — Healthy**

#### Strengths
- Clear canonical registry in `governance/README.md`
- Constitutional manifest properly versioned (`v1.0`)
- Golden exemplars organized by phase (`Phases/Phase-01/` through `Phase-06/`)
- GREG protocol documented (`golden-exemplars/GREG/`)
- Review packages well-structured (`review-packages/Phase-01_Review_Package/`)

#### Weaknesses
- Some `archives/` subdirectories within phases (e.g., `Phase-01/archives/`, `Phase-02/archives/`) — acceptable but adds navigation depth
- `Notes.md` files scattered in phase directories

#### Structural Concerns
- None significant

#### Cleanup Needs
- **Low priority**: Consider consolidating phase-level `archives/` into `archive/governance/`

#### Testing/Documentation Health
- **Documentation**: Excellent
- **Testing**: N/A (doctrine layer, not code)

---

### 5.2 Layer-2 — ML Compilation

**Status:** ✅ **COMPLETE / LOCKED — Healthy**

#### Strengths
- Clear directory structure: `datasets/`, `training/`, `lineage/`, `evaluation/`, `artifacts/`
- Stage-based pipeline documentation (`STAGE1_*.md` through `STAGE6_*.md`)
- Freeze certificates present (`FREEZE_CERTIFICATE_v1.json`)
- Lineage schemas exist (`ml/lineage/schemas/`)
- Artifact registry maintained (`ml/artifacts/REGISTRY.md`)

#### Weaknesses
- Dataset versioning creates clutter (`v15_*`, `v16_*`, `v17_*` files in `ml/datasets/`)
- Some duplicate summary docs across versions

#### Structural Concerns
- `ml/training/sft/exemplars/` — contains exemplar categories with own `Notes.md` files; could be better indexed
- `ml/training/pipeline/` vs `ml/training/` — slight hierarchy confusion

#### Cleanup Needs
- **Medium priority**: Archive older dataset version files to `archive/ml/datasets/`
- **Low priority**: Consolidate training pipeline documentation

#### Testing/Documentation Health
- **Documentation**: Comprehensive
- **Testing**: `ml/lineage/tests/`, `ml/training/pipeline/stage08/tests/` — adequate

---

### 5.3 Layer-3 — Runtime

**Status:** ⚠️ **ACTIVE — Structurally Complex**

#### Strengths
- Rich subsystem structure:
  - `plangate/` — Plan-Gate service
  - `plan_gate_stub/` — Protocol testing stub
  - `plan_gate_service/` — HTTP service
  - `sandbox/` — Execution sandbox
  - `ledger/` — Ledger emission
  - `orchestrator/` — Loop controller
  - `state/` — State machine
  - `shadow/` — Shadow mode
  - `layer5/` — Workspace resolver + evidence
  - `ask_service/` + `ask_validation/` — Ask flow
  - `execute_service/` — Execute flow
- Schema-driven: `runtime/schemas/`, `runtime/ide/schemas/`, `runtime/shadow/schemas/`
- Tests co-located with modules
- 37 `__init__.py` files indicating well-structured Python packages

#### Weaknesses
- `runtime/observation/` — name collision with Layer-4
- `runtime/rag/` — large subsystem with own docs, tests, scripts; feels like it could be its own layer
- `runtime/context/` vs `runtime/layer5/` — context engine appears in two places
- `plan_gate_stub/` vs `plan_gate_service/` vs `plangate/` — three similar-sounding directories

#### Structural Concerns
- **Naming collision**: `runtime/observation/` vs top-level `observation/`
- **Subsystem sprawl**: 32 subdirectories in `runtime/`
- **RAG autonomy**: `runtime/rag/` has its own `docs/`, `tests/`, `scripts/`, `docker/` — behaves like separate project

#### Cleanup Needs
- **High priority**: Rename `runtime/observation/` to `runtime/metrics/` or `runtime/observation_lib/`
- **Medium priority**: Document subsystem ownership more clearly
- **Low priority**: Consider whether `runtime/rag/` should be a separate top-level directory

#### Testing/Documentation Health
- **Documentation**: Good — `runtime/README.md`, `docs/runtime/` both exist
- **Testing**: Extensive — `runtime/tests/`, plus tests in each subsystem

---

### 5.4 Layer-4 — Observation

**Status:** ⚠️ **PARTIAL — Boundary Confusion**

#### Strengths
- Clear purpose: drift detection, baseline comparison, GREG triggers
- Well-organized subsystems:
  - `baseline/` — Day-0 baseline comparison
  - `ingest/` — Ingestion validation
  - `judge_drift_suite/` — Drift test cases
- Tests present: `observation/tests/`, `observation/baseline/tests/`, `observation/ingest/tests/`
- Golden outputs for validation

#### Weaknesses
- **Boundary overlap**: `runtime/observation/` contains observation-related code (collapse vectors, reconciliation, GREG escalation)
- **Unclear ownership**: Where does baseline detection live vs runtime metrics?

#### Structural Concerns
- Top-level `observation/` focuses on drift/baseline
- `runtime/observation/` focuses on runtime metrics and GREG bundles
- **No clear contract** defining the boundary

#### Cleanup Needs
- **High priority**: Define and document the boundary between `observation/` and `runtime/observation/`
- **Medium priority**: Consider consolidating or renaming to eliminate confusion

#### Testing/Documentation Health
- **Documentation**: Adequate — `observation/README.md` exists
- **Testing**: Good — tests in multiple subsystems

---

## 6. Cross-Layer and Shared-Contract Health

### 6.1 Duplicated Concepts

| Concept | Occurrences | Recommendation |
|---------|-------------|----------------|
| "Observation" | `observation/`, `runtime/observation/` | Rename runtime module |
| "Context Engine" | `runtime/context/`, `runtime/layer5/` | Clarify ownership |
| "Plan Gate" | `plangate/`, `plan_gate_stub/`, `plan_gate_service/` | Document distinctions |
| "Ledger" | `runtime/ledger/`, `docs/runtime/ledger/` | Align names |

### 6.2 Ownership Ambiguities

1. **Observation metrics**: Should GREG escalation logic live in `observation/` or `runtime/observation/`?
2. **Context layer**: Is `runtime/context/` superseded by `runtime/layer5/`?
3. **IDE integration**: `jetbrains-plugin/` vs `runtime/ide/` — who owns what?

### 6.3 Misplaced Shared Logic/Docs

| Item | Current Location | Suggested Location |
|------|-----------------|-------------------|
| `docs/GLOSSARY.md` | `docs/` | Good placement |
| `docs/CONTRACTS/README.md` | `docs/CONTRACTS/` | Consider `docs/contracts/` (lowercase) |
| Schema examples | Scattered in `runtime/*/schemas/examples/` | Consider unified `docs/schemas/examples/` |

### 6.4 Recommended Shared-Contract Areas

1. **Schema registry**: Centralized index of all JSON schemas across layers
2. **Error code registry**: Unified error codes for all services
3. **API version manifest**: Track which version of each API is current
4. **Cross-layer handoff docs**: Explicit handoff contracts between layers

---

## 7. Cleanup and Restructuring Recommendations

### 7.1 Immediate (This Sprint)

1. **Clean root `README.md`**: Remove iteration notes, backup system docs; keep only system overview + quick links
2. **Relocate root files**:
   - `AGENT_EXECUTION_RULES.md` → `docs/governance/`
   - `Hardware-Profile.md` → `docs/reference/`
   - `cuda-pytorch_test.py` → `scripts/` or delete
3. **Remove empty files**: `docs/effort-benefits-risks_analysis.md` (0 bytes)

### 7.2 Near-Term (Next 2 Sprints)

1. **Rename `runtime/observation/`** → `runtime/runtime_observation/` or `runtime/metrics/`
2. **Deduplicate docs**:
   - Archive one copy of each duplicate pair
   - Update references in canonical docs
3. **Archive stale audit reports**: Move older `docs/audit/*.md` to `archive/docs/audit/`
4. **Consolidate `docs/status/`**: Move to archive or merge with roadmap

### 7.3 Later (Backlog)

1. **Layer-5 consolidation**: Decide whether Layer-5 gets top-level directory or stays in `runtime/`
2. **RAG extraction**: Evaluate whether `runtime/rag/` should be separate
3. **Unified schema index**: Create `docs/schemas/INDEX.md` linking all schemas
4. **Doc index overhaul**: Create comprehensive `docs/INDEX.md`

### 7.4 Archive/Rename/Move/Merge Candidates

| Action | Item | Destination |
|--------|------|-------------|
| **Archive** | `docs/status/*.md` | `archive/docs/status/` |
| **Archive** | `docs/iterations/*.md` | `archive/docs/iterations/` |
| **Archive** | Older `docs/audit/*.md` | `archive/docs/audit/` |
| **Archive** | `workspace_intelligence/` | `archive/spikes/workspace_intelligence/` |
| **Rename** | `runtime/observation/` | `runtime/runtime_observation/` |
| **Move** | `AGENT_EXECUTION_RULES.md` | `docs/governance/AGENT_EXECUTION_RULES.md` |
| **Move** | `Hardware-Profile.md` | `docs/reference/Hardware-Profile.md` |
| **Merge** | Duplicate V15/V17 docs | Keep in `ml/datasets/`, archive others |
| **Delete** | `docs/effort-benefits-risks_analysis.md` | (empty file) |
| **Delete** | `runtime/rag/=0.13.0` | (artifact from failed pip install) |

---

## 8. Recommended Target Repo Layout

### 8.1 Proposed Structure

```
/workspace/
├── README.md                  # Clean: 1-page overview + quick links
├── Makefile                   # Build entrypoint
├── .gitignore
│
├── governance/                # Layer-1: Constitutional (unchanged)
│   ├── README.md
│   ├── CONSTITUTIONAL_MANIFEST_v1.0.md
│   ├── golden-exemplars/
│   └── review-packages/
│
├── ml/                        # Layer-2: Compilation (unchanged)
│   ├── README.md
│   ├── artifacts/
│   ├── datasets/
│   ├── evaluation/
│   ├── lineage/
│   ├── scripts/
│   └── training/
│
├── runtime/                   # Layer-3: Enforcement
│   ├── README.md
│   ├── ask_service/
│   ├── ask_validation/
│   ├── ci_gate/
│   ├── context/
│   ├── context_layer_service/
│   ├── emulator/
│   ├── execute_service/
│   ├── ide/
│   ├── integrity/
│   ├── layer5/                # Workspace intelligence (L5 lives here)
│   ├── ledger/
│   ├── orchestrator/
│   ├── plangate/
│   ├── plan_gate_service/
│   ├── plan_gate_stub/
│   ├── policies/
│   ├── rag/
│   ├── replay/
│   ├── runtime_metrics/       # Renamed from runtime/observation/
│   ├── sandbox/
│   ├── schemas/
│   ├── scripts/
│   ├── shadow/
│   ├── shadow_runner/
│   ├── state/
│   ├── task/
│   └── tests/
│
├── observation/               # Layer-4: Drift detection (unchanged)
│   ├── README.md
│   ├── baseline/
│   ├── ingest/
│   ├── judge_drift_suite/
│   └── tests/
│
├── docs/                      # Documentation
│   ├── README.md              # Doc index with navigation
│   ├── INDEX.md               # Comprehensive doc index (new)
│   ├── MASTER_SYSTEM_SPEC.md
│   ├── ARCHITECTURE_4_LAYER.md
│   ├── LIVE_ROADMAP_TRACKER.md
│   ├── GLOSSARY.md
│   ├── architecture/          # Architecture docs
│   ├── audit/                 # Current audit reports only
│   ├── contracts/             # Contract specs (renamed from CONTRACTS)
│   ├── evaluation/
│   ├── governance/            # Governance-related docs
│   ├── guides/
│   ├── layer5/
│   ├── reference/             # Reference materials (new)
│   ├── reports/
│   ├── runtime/
│   ├── training/
│   └── validation/            # Validation sheets (new)
│
├── jetbrains-plugin/          # IDE plugin (unchanged)
│
├── packaging/                 # Deployment artifacts (unchanged)
│
├── scripts/                   # Operational scripts
│   ├── ci/
│   └── *.py, *.sh
│
├── tests/                     # Top-level integration tests
│
└── archive/                   # Historical materials
    ├── README.md
    ├── by_topic/
    ├── docs/
    │   ├── audit/             # Older audit reports
    │   ├── iterations/        # Archived iterations
    │   ├── status/            # Archived status docs
    │   └── ...
    ├── okr/
    ├── planning/
    ├── reorg/
    └── spikes/                # Archived spikes (new)
        └── workspace_intelligence/
```

### 8.2 Rationale

1. **Clean root**: Only essential files at root level
2. **Layer-5 in runtime**: Workspace intelligence is runtime behavior, not a separate layer
3. **Renamed `runtime/observation/`**: Eliminates collision with Layer-4
4. **Structured docs**: Clear categorization and index
5. **Archive spikes**: Historical exploration moved to archive
6. **Reference directory**: Place for operational docs like Hardware-Profile

### 8.3 Migration Notes

1. **Incremental**: Can be done in phases without breaking builds
2. **Reference updates**: Will need grep-and-replace for moved docs
3. **Git history**: Consider `git mv` to preserve history
4. **Test coverage**: Verify imports after `runtime/observation/` rename

---

## 9. Integrated Repo-Intelligence Tool Proposal

### 9.1 Problem Statement

Contributors frequently ask:
- "What file am I in, and which layer owns it?"
- "Is this file canonical or stale?"
- "What specs/tests should I look at?"
- "Does this file violate any layout rules?"
- "What cleanup actions apply to this file?"

Currently, answering these questions requires manual cross-referencing of multiple docs and directory conventions.

### 9.2 V1 Feature Set

```
repo-intel <path>              # Report on file/directory
repo-intel --layer <layer>     # List all files in layer
repo-intel --stale             # Find stale files
repo-intel --duplicates        # Find duplicate filenames
repo-intel --violations        # Find layout violations
repo-intel --related <path>    # Find related docs/tests
```

### 9.3 Required Metadata/Indexes

1. **Layer map**: `layer_map.json` — directory → layer assignment
2. **Canonical registry**: `canonical_files.json` — list of canonical docs
3. **Stale markers**: Files with specific patterns (e.g., version in name, date stamps)
4. **Test map**: `test_map.json` — source file → test file mapping
5. **Doc map**: `doc_map.json` — component → documentation mapping

### 9.4 Query Response Design

**For a given file path:**
```json
{
  "path": "runtime/observation/collapse_vectors.py",
  "layer": 3,
  "layer_name": "Runtime",
  "component": "runtime_metrics",
  "status": "active",
  "violations": [
    "naming_collision: 'observation' conflicts with Layer-4 namespace"
  ],
  "related_docs": [
    "docs/LAYER3_RUNTIME_SPEC.md",
    "docs/runtime/README.md"
  ],
  "related_tests": [
    "runtime/tests/test_collapse_vectors.py"
  ],
  "suggested_actions": [
    "Consider renaming parent directory to 'runtime_metrics'"
  ]
}
```

### 9.5 Where It Should Live

**Recommended:** `scripts/repo_intel.py` (CLI tool)

**Alternatives:**
- `runtime/layer5/repo_intel/` — if it becomes a service
- `.cursor/repo_intel/` — if it's editor-specific

### 9.6 What It Should NOT Do (Initially)

1. **No auto-fix**: Report only, no mutations
2. **No deep AST analysis**: File-level granularity only
3. **No remote lookups**: Pure local analysis
4. **No build-time integration**: Standalone CLI only
5. **No code generation**: Report generation only

---

## 10. Staged Execution Plan

### Phase A: Survey + Tagging (This PR)

**Objective:** Complete structural survey; tag files with status markers

**Artifacts:**
- This document (`REPO_STRUCTURAL_SURVEY_AND_HEALTH_REPORT.md`)
- Optional: `canonical_files.json` if useful for Phase B

**Exit Criteria:**
- Survey document reviewed and merged
- Open questions documented

**Risks:**
- None — read-only phase

---

### Phase B: Canonical Marking

**Objective:** Mark canonical docs; identify duplicates/stale explicitly

**Artifacts:**
- Updated canonical docs with `Doc status: canonical-current` headers
- `docs/INDEX.md` — doc navigation index
- `stale_candidates.md` — list of files to archive/delete

**Exit Criteria:**
- All canonical docs marked
- Stale candidates listed with rationale

**Risks:**
- Mistagging canonical vs stale (mitigation: PR review)

---

### Phase C: Doc Cleanup

**Objective:** Deduplicate and relocate misplaced docs

**Artifacts:**
- Moved/archived files
- Updated references in remaining docs
- Archive additions to `archive/docs/`

**Exit Criteria:**
- Zero duplicate doc pairs
- Root-level files relocated
- References updated

**Risks:**
- Broken links (mitigation: grep-verify before merge)

---

### Phase D: Layout Cleanup

**Objective:** Rename ambiguous directories; consolidate structure

**Artifacts:**
- Renamed `runtime/observation/` → `runtime/runtime_metrics/`
- Archived `workspace_intelligence/`
- Cleaned root `README.md`

**Exit Criteria:**
- No naming collisions
- Clean root directory
- Tests pass after renames

**Risks:**
- Import breakage (mitigation: comprehensive grep, test runs)

---

### Phase E: Tool Foundation

**Objective:** Implement basic `repo-intel` CLI

**Artifacts:**
- `scripts/repo_intel.py` — CLI tool
- `layer_map.json` — layer assignment data
- `canonical_files.json` — canonical file list

**Exit Criteria:**
- `repo-intel <path>` returns correct layer and status
- `repo-intel --violations` finds known issues

**Risks:**
- Maintenance burden (mitigation: keep v1 minimal)

---

### Phase F: Deeper Component Refactors

**Objective:** Address structural issues requiring code changes

**Artifacts:**
- Refactored `runtime/rag/` (if extracted)
- Consolidated context engine
- Schema registry

**Exit Criteria:**
- Clear ownership per component
- Updated specs

**Risks:**
- Higher complexity (mitigation: separate PRs per refactor)

---

## 11. Real Blockers and Open Questions

### Blockers

1. **None critical**: All cleanup can proceed incrementally

### Open Questions

1. **Layer-5 placement**: Should `runtime/layer5/` become top-level `layer5/` directory?
   - **Current answer**: Keep in `runtime/` — workspace intelligence is runtime behavior
   - **Revisit if**: Layer-5 grows substantially or has non-runtime components

2. **RAG extraction**: Should `runtime/rag/` be a separate project/directory?
   - **Current answer**: Keep in `runtime/` — it's part of the runtime stack
   - **Revisit if**: RAG becomes independently deployable/versionable

3. **Observation boundary**: Exactly what belongs in `observation/` vs `runtime/runtime_metrics/`?
   - **Proposed answer**: `observation/` = drift detection, baselines, audit evidence
   - `runtime/runtime_metrics/` = runtime metric collection, GREG bundle building
   - **Action**: Document boundary explicitly

4. **Archive policy**: When should archived files be deleted permanently?
   - **Proposed answer**: Never auto-delete; manual cleanup after 6+ months if no references

---

## 12. Final Recommendation

**Proceed with staged cleanup**

The m-coder repository has strong architectural foundations but has accumulated structural debt that degrades contributor experience. The recommended approach:

1. **Immediate**: Clean root README, relocate orphan files
2. **Near-term**: Rename `runtime/observation/`, deduplicate docs
3. **Later**: Implement `repo-intel` tool, consider RAG extraction

**Priority order:**
1. Phase C (doc cleanup) — high value, low risk
2. Phase D (layout cleanup) — medium value, medium risk
3. Phase E (tool foundation) — force multiplier for future work

**Do not defer indefinitely**: The naming collisions and doc clutter will compound if not addressed.

---

*End of Survey Report*
