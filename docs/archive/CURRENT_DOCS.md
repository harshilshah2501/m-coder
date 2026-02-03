# Current Documentation Guide

**Last Updated:** December 17, 2025

## �� Active Documentation

### Core System
- **[Motadata-Coder.md](docs/Motadata-Coder.md)** - System overview and architecture
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Commands and quick reference

### Current Iteration
- **[ITERATION_9_JOURNAL.md](docs/ITERATION_9_JOURNAL.md)** - Iteration 9 progress and journal
- **[MOTADATA_BENCH_PLAN.md](docs/MOTADATA_BENCH_PLAN.md)** - Benchmark strategy and plan

### Phase 2: Real JIRA Tasks
- **[PHASE_2_REAL_TASKS_MIGRATION.md](docs/PHASE_2_REAL_TASKS_MIGRATION.md)** - Migration from synthetic to real tasks
- **[PHASE_2_REVIEW_SUMMARY.md](docs/PHASE_2_REVIEW_SUMMARY.md)** - Phase 2 completion summary

### Evaluation Results
- **[ITER8_AND_ITER9_RESULTS.md](evaluation/ITER8_AND_ITER9_RESULTS.md)** - Iteration 8 & 9 results
- **[ITER8_RESULTS_SUMMARY.md](evaluation/ITER8_RESULTS_SUMMARY.md)** - Iteration 8 summary
- **[RAG_INTEGRATION_COMPLETE.md](evaluation/RAG_INTEGRATION_COMPLETE.md)** - RAG integration status
- **[REAL_VS_SYNTHETIC_COMPARISON.md](evaluation/REAL_VS_SYNTHETIC_COMPARISON.md)** - Task comparison analysis

## 🗄️ Archived Documentation

Historical documents moved to archive directories:
- **[docs/archive/](docs/archive/)** - 8 archived strategy/status documents
- **[evaluation/archive/](evaluation/archive/)** - 1 archived evaluation document

See respective `README.md` files in archive directories for details.

## 📊 Current Status Summary

**Last Updated:** December 17, 2025 - 12:30 PM

**Benchmark:** 5 real JIRA tasks from production (analyzed 2,731 candidates)
- Ranks: 1, 2, 9, 10, 47 (scores 80-100)
- Types: TYPE_B multifile, TYPE_D direct
- Source: Git history from `training-artifacts/benchmark_jira.jsonl`

**Model:** Iter9 (motadata-coder) via RAG API
- Service: motadata-rag (port 8081) ✅ Running and healthy
- vLLM Service: motadata-coder (port 8000) ✅ Running (18GB memory, 8h+ uptime)
- Integration: Qdrant ✅ + Neo4j ✅ + vLLM ✅

**Infrastructure Status:**
- ✅ RAG API: Fixed port conflict, running on 8081
- ✅ Endpoint: Corrected to /v1/chat/completions (OpenAI-compatible)
- ✅ Model name: motadata-coder
- ✅ Max tokens: Increased to 16,000
- ✅ Diff extraction: Pattern fixed, captures 4 blocks
- ✅ Path resolution: Strips motadata/ prefix correctly
- ✅ Diff application: 1/4 diffs applied successfully with sudo patch

**Test Results (Task A - Rank 1):**
- Model generates: 15,724 tokens (unified diffs for 4 files)
- Extraction: ✅ 4 diff blocks found
- Application: ⚠️ 1/4 successful (SNMPOIDGroup.java)
- Issues identified:
  1. Baseline YAML has escaping bugs (from task creation)
  2. Model output has line wrapping in long diff lines
  3. Some diffs incomplete/truncated

**Known Issues:**
1. **Baseline code quality**: YAML escaping creates syntax errors (33 errors in baseline)
2. **Line wrapping in diffs**: Model wraps long lines, causing patch failures
3. **Output truncation**: 16K tokens not enough for all 4 complete diffs

## 🔧 Next Steps

1. **Option A - Fix diffs approach:**
   - Fix baseline YAML escaping in all 5 task files
   - Improve line unwrapping logic
   - Increase max_tokens to 32K

2. **Option B - Switch to full files:**
   - Simpler parsing (no patch command needed)
   - Higher token cost but more reliable
   - Better for smaller files

3. **Expand task count:**
   - After validation, expand from 5 → 20/50/91 candidates
   - More comprehensive baseline
