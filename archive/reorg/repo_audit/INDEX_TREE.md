# Repository Index Tree (Depth 4)

Root: `/root/m-coder`

Generated as part of read-only structural audit. Excludes `.git/`, `.venv/`, `.cursor/` from file-count highlights.

---

## Top-Level Structure

```
/
├── .augment/
├── .cursor/
├── .git/
├── archive/
├── datasets/
├── docs/
├── governance/
├── ml/
├── observation/
├── repo_audit/
├── runtime/
├── scripts/
├── motadata-coder-a-complete-guide_v1.7.md
├── GREG_Pre-Review_Attack_Result.md
├── Hardware-Profile.md
├── README.md
├── backup-h100.sh
├── monitor_v16_1.sh
├── cuda-pytorch_test.py
└── chat-*.txt
```

---

## Directory Tree (Depth ≤ 4)

### governance/
- governance/golden-exemplars/
  - governance/golden-exemplars/GREG/
  - governance/golden-exemplars/Phases/
    - Phase-01/
    - Phase-02/
    - Phase-03/
    - Phase-04/
    - Phase-05/
    - Phase-06/
- governance/review-packages/
  - Phase-01_Review_Package/

### ml/
- ml/training/
  - ml/training/phase6c/
  - ml/training/phase08/
  - ml/training/sft/
  - ml/training/src/
  - ml/training/artifacts/
  - ml/training/data/
  - ml/training/evaluation/
  - ml/training/results/
- ml/evaluation/
  - ml/evaluation/results/
  - ml/evaluation/reports/
  - ml/evaluation/analysis/
  - ml/evaluation/diffs/
- ml/datasets/
  - ml/datasets/cpt/
  - ml/datasets/v16_2/
  - ml/datasets/generation/
- ml/scripts/

### runtime/
- runtime/rag/
  - runtime/rag/docs/
  - runtime/rag/src/
  - runtime/rag/tests/
  - runtime/rag/scripts/
  - runtime/rag/docker/
- runtime/policies/
- runtime/tests/

### observation/
- observation/judge_drift_suite/
  - observation/judge_drift_suite/cases/
  - observation/judge_drift_suite/historical/

### docs/
- docs/architecture/
- docs/guides/
- docs/datasets/
- docs/training/
- docs/reference/
- docs/status/
- docs/status_reports/
- docs/iterations/
- docs/agents/
- docs/benchmark/
- docs/evaluation/
- docs/rag/
- docs/troubleshooting/

### archive/
- archive/okr/
  - archive/okr/supporting-docs/
- archive/docs/
  - archive/docs/debug/
  - archive/docs/cleanup_20251231/
  - archive/docs/v15_training_logs/
  - archive/docs/test_project/
  - archive/docs/unsloth_compiled_cache/

### datasets/
- datasets/sft/

### scripts/
- scripts/ci/

---

## Directories with >20 Files (Approximate)

- `.git/**` — Git object store
- `ml/training/src/sources/Motadata/phase6/.venv/**` — Python virtualenv (~3000+ files)
- `ml/training/src/sources/Motadata/phase6/phase6c/**` — Phase-6C harness code
- `governance/golden-exemplars/Phases/**` — Exemplar definitions
- `ml/evaluation/results/phase_c/**` — Probe result files
- `ml/datasets/**` — Dataset artifacts

---

## Naming Patterns Detected

| Pattern | Locations |
|---------|-----------|
| `v1`, `v1.5`, `v1.6`, `v1.7` | Guide versions, GREG ratification |
| `v0.9` | GREG-Initiation-Ratification |
| `PHASE6*`, `PHASE6B*`, `Phase6C*` | ML compilation specs |
| `Phase-0*` | Governance phase directories |
| `draft`, `backup`, `old` | archive/, some doc names |
| `*_REPORT*`, `*_SPEC*` | Mutation and design specs |
| `*traces*.jsonl`, `*ledger*.jsonl` | Phase-6C outputs |
