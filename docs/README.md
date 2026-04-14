# Motadata AI System - Documentation Index

Comprehensive documentation for the Motadata AI system including model training, RAG implementation, and evaluation.

**Entry discipline:** This file is a **supporting index**, not the canonical repo entry. Prefer root [README.md](../README.md) → [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md); live status stays in [LIVE_ROADMAP_TRACKER.md](LIVE_ROADMAP_TRACKER.md).

## Documentation Authority Model (Canonical vs Supporting)

To avoid multiple competing sources of truth, use this authority model:

- Canonical system truth: [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)
- Canonical live status and closures: [LIVE_ROADMAP_TRACKER.md](LIVE_ROADMAP_TRACKER.md)
- Canonical production closure declaration: [mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md](mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md)
- Supporting closure narrative (not competing sign-off): [production_closure_handbook_corrected_canonical_version.md](production_closure_handbook_corrected_canonical_version.md)

**Tooling / process meta (not product behavior):** [archive/tooling/CODERABBIT_AUDIT_COVERAGE_MATRIX.md](archive/tooling/CODERABBIT_AUDIT_COVERAGE_MATRIX.md) — optional audit matrix for CodeRabbit-style reviews.

### Golden Path (Operator + Demo)

Use only these in sequence for setup and usage:

1. [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md) - setup/configure (GPU -> WSL -> Windows)
2. [runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md](runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md) - plugin-mediated usage and checks
3. [demo/NEAR_PRODUCTION_VERTICAL_SLICE_RUNBOOK.md](demo/NEAR_PRODUCTION_VERTICAL_SLICE_RUNBOOK.md) - end-to-end operator demo flow

### Latest Inclusions (2026-04)

- Stage 2.5 Assist Layer v1 implemented and evaluated as advisory-only (no runtime query authority)
- Assist v2 evaluation artifacts and policy published under [validation/artifacts/assist_layer_v2_eval/](validation/artifacts/assist_layer_v2_eval/)
- MVP closure evidence index maintained in [mvp_declaration/MVP_EVIDENCE_INDEX.md](mvp_declaration/MVP_EVIDENCE_INDEX.md)

### Historical / Supporting Docs

Obsolete or non-canonical material: **[archive/README.md](archive/README.md)** (indexed list).

**Canonical reading path:** root [README.md](../README.md) → [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md). **Master system guide (long-form, Layer-3/Layer-4 demos):** [MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md](../MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md).

**Motadata AI Coding Assistant (Windows / WSL / GPU):** [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md) (setup), [MOTADATA_DEMO_SCENARIOS.md](MOTADATA_DEMO_SCENARIOS.md) (demo + success criteria), [MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md](MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md) (architecture).

**Artifact governance:** Model/checkpoint and runtime packaging policy is defined in [Artifact Governance — LoRA, Checkpoints, and Runtime](architecture/ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md). Do not commit large adapters, checkpoints, or merged model binaries to the repo.

**Current Program Status:** ✅ **Production closure baseline achieved**
- Governed production vertical slice closed and accepted (see [LIVE_ROADMAP_TRACKER.md](LIVE_ROADMAP_TRACKER.md) and [mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md](mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md)).
- Stage 2.5 Assist Layer v1: implemented + evaluated, advisory-only (no runtime query authority).

**Parallel ML Stream Status (separate from closure baseline):**
- V16.1 model training and dataset iteration documents remain available under `docs/training/`, `docs/evaluation/`, and `docs/datasets/`.

## Repository layout (this codebase)

**Do not treat a generic `~/…` or top-level `rag/` sketch as the source of truth.** This **m-coder** repository uses:

- **Inventory + map:** [audit/REPO_LAYOUT_INVENTORY.md](audit/REPO_LAYOUT_INVENTORY.md)
- **Runtime audit:** [audit/RUNTIME_DIRECTORY_AUDIT.md](audit/RUNTIME_DIRECTORY_AUDIT.md)
- **Root entry:** [README.md](../README.md)

**Observation surfaces** (easy to confuse): Layer-4 doc index [OBSERVATION/README.md](OBSERVATION/README.md); CLI packages under repo-root `observation/`; trace library under `runtime/observation/`; Stage 3 mini-ledger under `runtime/obs/`.

ML streams (`ml/`, `training/`, local venvs) are **environment-specific** — see inventory and [training/](training/).

**Obsolete / superseded docs:** [archive/README.md](archive/README.md) — notes, old status journals, [TEMP Motadata integration guide](archive/guides/TEMP_MOTADATA_REPO_INTEGRATION_GUIDE.md), CodeRabbit matrices, historical [integrated demo guide](archive/demo/INTEGRANTED_EXECUTION_GUIDE.md). Prefer the **golden path** runbooks for current procedure.

## Report and verification document placement

**Going-forward convention:** New report-like docs should be placed as follows. Existing documents may remain where they are; do not mass-move historical material without a dedicated migration plan.

- **docs/reports/** — Milestone completion, integration, merge, and freeze reports (e.g. merge readiness, verification, completion).
- **docs/status/** — Status snapshots, session summaries, and short-term operational context (living journal).
- **docs/runtime/verification/** — Runtime and structure verification: audits, E2E validation, constitutional reference, completion reports for Layer-3/runtime.

**Historical tolerance:** Materials already in these locations remain valid; this convention defines placement for new documents only.

## Documentation by Component

### Tests (pytest)

Primary runtime integration suite (repo root):

```bash
cd /path/to/m-coder && python3 -m pytest runtime/tests/ -q
```

Marker registration: [`pytest.ini`](../pytest.ini). Approximate collection count varies; check with `python3 -m pytest runtime/tests/ --collect-only -q` (on the order of **~1000** tests as of 2026-04).

Some subtrees under `ml/` or `scripts/` may not collect cleanly without extra deps — prefer **`runtime/tests/`** for a green default.

### 🏛️ Core Architecture Docs

- **[ARCHITECTURE_4_LAYER.md](ARCHITECTURE_4_LAYER.md)** — Directory philosophy, layer boundaries, axis separation
- **[ROADMAP_L2_L3_L4.md](ROADMAP_L2_L3_L4.md)** — L2/L3/L4 milestone roadmap, snapshot, sequencing

### 📊 Evaluation & Benchmarking
- **[evaluation/](evaluation/)** - Model evaluation reports and analysis
  - Comprehensive evaluation reports
  - Benchmark results
  - Evaluation workflows
- **[benchmark/](benchmark/)** - Benchmark methodology and results

### 🤖 Model Documentation
- **[training/](training/)** — Training guides and checklists
  - Training procedures
  - Finetuning checklists
  - Training examples

### 📚 Dataset Documentation
- **[datasets/](datasets/)** - Dataset analysis and specifications
  - Dataset quality verification
  - Dataset analysis and recommendations
  - Audit reports

### 🔌 RAG System
- **[runtime/rag/](../runtime/rag/)** — **Implementation** (API, indexing, retrieval code in this repo)
- **[rag/](rag/)** — Narrative / iteration notes (`ENHANCED_RAG_IMPLEMENTATION.md`, etc.); not a second code tree

### 🏗️ Architecture & Design
- **[architecture/](architecture/)** - System architecture and design
  - System design documents
  - Project structure
  - Architecture overview

### 🚀 Getting Started & Guides
- **[guides/](guides/)** - How-to guides for all components
  - Setup instructions
  - Training guides
  - RAG guides
  - Orchestrator guides
  - Integration guides

### 🔧 API Documentation
- **[api/README.md](api/README.md)** — Index of HTTP surfaces and schemas (no single OpenAPI bundle)

### 🐛 Troubleshooting
- **[troubleshooting/](troubleshooting/)** - Debugging guides and FAQs
  - Debugging guides
  - Common issues and solutions
  - FAQ

### 🤖 Agent Framework
- **[agents/](agents/)** - Agent framework documentation (future)

### 📚 Historical Documentation
- **[iterations/](iterations/)** — Per-iteration notes and progress
- **Ad-hoc historical docs** — may live under `docs/reports/`, `docs/validation/artifacts/`, or **[docs/archive/](archive/README.md)** (obsolete / superseded material)

### 📌 Core 4-Layer Architecture (Golden Exemplars) + Product Extensions
- **[MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md)** - Canonical entry point; Doctrine Immutability; links to GOVERNANCE, COMPILATION, RUNTIME, OBSERVATION, CONTRACTS
- **[MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md](../MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md)** - Master system guide (judgment, compilation, runtime, observation; Appendix H: Layer-3/Layer-4 demos)

### 📌 Core References
- **[reference/MODEL_VERIFICATION_REPORT.md](reference/MODEL_VERIFICATION_REPORT.md)** - Model verification and rollback decisions
- **[reference/DIRECTORY_STRUCTURE_ANALYSIS.md](reference/DIRECTORY_STRUCTURE_ANALYSIS.md)** - Repository structure and disk usage analysis

## V16 Documentation

### 📊 V16 Evaluation Reports
- **[evaluation/V16_POST_TRAINING_EVALUATION.md](evaluation/V16_POST_TRAINING_EVALUATION.md)** - Post-training evaluation metrics
- **[evaluation/V16_INFERENCE_TEST_REPORT.md](evaluation/V16_INFERENCE_TEST_REPORT.md)** - Inference test results (7/7 passed)
- **[evaluation/V16_COMPREHENSIVE_EVALUATION_REPORT.md](evaluation/V16_COMPREHENSIVE_EVALUATION_REPORT.md)** - Complete evaluation analysis
- **[evaluation/v16_inference_results.json](evaluation/v16_inference_results.json)** - Raw inference test results

### 🤖 V16 Training
- **[training/V16_TRAINING_SUMMARY.md](training/V16_TRAINING_SUMMARY.md)** - V16 training overview and metrics

### 📚 V16 Dataset
- **[datasets/V16_DATASET_SUMMARY.md](datasets/V16_DATASET_SUMMARY.md)** - V16 dataset analysis and improvements

### 📈 V16 Status
✅ **Production Ready**
- Training: Complete (85 min, 1,510 steps)
- Validation Loss: 0.1425 (25.8% improvement over V15)
- Inference: 100% pass rate (7/7 capabilities)
- Model Location: `training/artifacts/results/v16_merged/`

## Quick Start

### m-coder governed stack (vLLM + Plan-Gate)

From repo root with **`runtime/config/demo_stack.env`** configured (**`VLLM_BASE_MODEL`** set):

```bash
./runtime/scripts/governed_services.sh start
./runtime/scripts/governed_services.sh status
./runtime/scripts/governed_services.sh stop
./runtime/scripts/governed_services.sh restart   # clean stop → port cleanup → start
```

See **`docs/guides/ORCHESTRATOR_GUIDE.md`**. Optional systemd: **`docs/guides/ORCHESTRATOR_SERVICE_GUIDE.md`** (no unit file is shipped in-repo).

### Test Endpoints
```bash
# Health check
curl http://localhost:8081/health

# Chat with RAG context
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "motadata-coder", "messages": [{"role": "user", "content": "Which class is inherited by all API classes?"}]}'

# Semantic search
curl -X POST http://localhost:8081/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "email notification", "top_k": 5}'
```

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| vLLM Base | 8000 | LLM inference server |
| vLLM Wrapper | 8080 | Anti-repetition wrapper |
| RAG API | 8081 | Main API (OpenAI-compatible) |
| Qdrant | 6333 | Vector database |
| Neo4j HTTP | 7474 | Graph database UI |
| Neo4j Bolt | 7687 | Graph database driver |

## System Stats (example snapshot)

**Environment-specific** — one deployment sample, **not** an invariant spec. Your vectors, graph size, and GPU will differ.

| Component | Details (illustrative) |
|-----------|---------|
| Qdrant | e.g. thousands of vectors (768 dim) |
| Neo4j | e.g. node/edge counts from a given index run |
| GPU | e.g. datacenter-class GPU; utilization varies |

## Service Management (governed stack)

Use **`runtime/scripts/governed_services.sh`** (`start` | `stop` | `restart` | `status`). Logs: **`runtime/.run/`** (`vllm.log`, `plan_gate.log`). Optional systemd: **`docs/guides/ORCHESTRATOR_SERVICE_GUIDE.md`**.

### View Component Logs

**Governed stack (this repo):** logs under **`runtime/.run/`** (e.g. `vllm.log`, `plan_gate.log`) — see [guides/ORCHESTRATOR_GUIDE.md](guides/ORCHESTRATOR_GUIDE.md).

If your deployment writes service logs next to a separate `rag/` checkout or custom paths, use those paths; they are **not** fixed in-tree.

### Documentation
- **[guides/ORCHESTRATOR_GUIDE.md](guides/ORCHESTRATOR_GUIDE.md)** — Governed stack (`governed_services.sh`)
- **[guides/ORCHESTRATOR_SERVICE_GUIDE.md](guides/ORCHESTRATOR_SERVICE_GUIDE.md)** — Optional systemd

**Startup Sequence (automatic with health checks):**
1. Docker containers (Qdrant + Neo4j) - waits for HTTP health (60s timeout)
2. vLLM server (port 8000) - waits up to 180s for model load
3. vLLM wrapper (port 8080) - waits for health (30s timeout)
4. RAG API (port 8081) - waits for health (60s timeout)
5. Health monitor

**Startup Time:** ~90-120 seconds (mostly vLLM model loading)

**Service Paths:**
| Component | Path | Port |
|-----------|------|------|
| Governed launcher | `runtime/scripts/governed_services.sh` | vLLM + Plan-Gate |
| vLLM | `venv/vllm/bin/python -m vllm.entrypoints.openai.api_server` | 8000 |
| API Wrapper | `training/src/utils/api_server.py` | 8080 |
| RAG API | `runtime/rag/src/api/rag_api.py` | 8081 |
| Qdrant | Docker container | 6333 |
| Neo4j | Docker container | 7474 |

## Model Training History

**Current Production:** Iteration 9 (Full Precision)

| Iteration | Dataset Size | Pass Rate (Std/Agentic) | Tool Obsession | Key Learning |
|-----------|--------------|-------------------------|----------------|--------------|
| **Iter6** | ~10k | 60% / N/A | 0% | Baseline model |
| **Iter7** | ~12k | 50% / 20% | 40% | 93% agentic caused tool obsession |
| **Iter8** | 15.6k | 40% / 60% | 60% | 79.5% agentic still too high |
| **Iter9 (4-bit)** | 12.7k | **0% / N/A** | 0% | ❌ **CORRUPTED** - 4-bit→16-bit merge failure |
| **Iter9 (Full)** | 12.7k | **60% / 80%** | **0%** | ✅ **PRODUCTION** - Full precision resolved corruption |

**Critical Discovery (Iter9):**
- 4-bit quantization during training caused catastrophic weight corruption during merge to 16-bit
- Symptoms: 0% pass rate, 80% repetition loops, gibberish output ("{baselte")
- Solution: Full precision training (bfloat16 throughout)
- H100 GPU has 80GB memory, full precision only uses 17GB (21% utilization)
- **Lesson: Never mix quantization levels between training and deployment**

**Documentation:**
- 📊 **[ITER8_AND_ITER9_RESULTS.md](evaluation/ITER8_AND_ITER9_RESULTS.md)** - Comparative performance analysis


## Documentation

- **[README.md](README.md)** — This documentation index
- **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** — System architecture
- **[evaluation/](evaluation/)** — Evaluation reports and analysis (no separate `README.md` index)
