# Motadata AI System - Documentation Index

Comprehensive documentation for the Motadata AI system including model training, RAG implementation, and evaluation.

**Canonical reading path:** root [README.md](../README.md) → [MASTER_SYSTEM_SPEC.md](MASTER_SYSTEM_SPEC.md). **Master system guide (long-form, Layer-3/Layer-4 demos):** [MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md](../MOTADATA_MASTER_SYSTEM_GUIDE_v1.7.md).

**Motadata AI Coding Assistant (Windows / WSL / GPU):** [MOTADATA_DEMO_SETUP_RUNBOOK.md](MOTADATA_DEMO_SETUP_RUNBOOK.md) (setup), [MOTADATA_DEMO_SCENARIOS.md](MOTADATA_DEMO_SCENARIOS.md) (demo + success criteria), [MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md](MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md) (architecture).

**Artifact governance:** Model/checkpoint and runtime packaging policy is defined in [Artifact Governance — LoRA, Checkpoints, and Runtime](architecture/ARTIFACT_GOVERNANCE_LORA_CHECKPOINTS_AND_RUNTIME.md). Do not commit large adapters, checkpoints, or merged model binaries to the repo.

**Current Status:** 🚀 **V16.1 Model - Training In Progress**
- Model: Qwen/Qwen2.5-Coder-14B-Instruct (Fine-tuning V16.1)
- Dataset: v16_1_surgical.jsonl (3,912 examples, 100% valid, 0 duplicates)
  - V15: 2,598 real Motadata code edits (66.4%)
  - Motadata: 1,314 JavaDoc Q&A pairs (33.6%)
- Training: Started (screen session: v16_1_training)
- Splits: Train 3,129 | Val 391 | Test 392
- Previous V16: ✅ Production Ready (7/7 capability tests passed)

## Directory Structure

```
~/Harshil-PoCs/
├── venv/                        # Virtual Environments
│   ├── training/                # Training/Finetuning venv
│   ├── vllm/                    # vLLM Inference venv
│   └── rag/                     # RAG API venv
│
├── models/                      # Finetuned Models
│   ├── v15/                     # V15 Model (previous)
│   └── v16/                     # V16 Model (current)
│
├── training/                    # Training & Finetuning
│   ├── src/                     # Training source code
│   │   ├── finetuning/          # Finetuning scripts
│   │   ├── dataset_creation/    # Dataset generation
│   │   ├── evaluation/          # Evaluation scripts
│   │   └── utils/               # Utility functions
│   ├── data/                    # Training data
│   │   ├── raw/                 # Raw datasets
│   │   └── processed/           # Processed datasets
│   ├── checkpoints/             # Training checkpoints
│   └── artifacts/               # Training outputs
│       ├── logs/                # Training logs
│       └── results/             # Training results
│
├── rag/                         # RAG System
│   ├── src/                     # RAG source code
│   │   ├── api/                 # RAG API implementation
│   │   ├── indexing/            # Vector/Graph indexing
│   │   ├── retrieval/           # Retrieval logic
│   │   └── utils/               # Utility functions
│   ├── config/                  # Configuration files
│   ├── docker/                  # Docker setup
│   ├── data/                    # RAG data
│   ├── logs/                    # Service logs
│   ├── tests/                   # RAG tests
│   └── scripts/                 # Orchestration scripts
│
├── evaluation/                  # Evaluation & Benchmarking
│   ├── src/                     # Evaluation scripts
│   ├── results/                 # Benchmark results
│   ├── reports/                 # Evaluation reports
│   └── diffs/                   # Diff analysis
│
├── datasets/                    # Training Datasets
│   ├── raw/                     # Raw source data
│   ├── generation/              # Generated datasets
│   ├── v16_1_splits/            # V16.1 training splits (current)
│   ├── v16_1_surgical.jsonl     # V16.1 final dataset (3,912 examples)
│   └── v15_enhanced_splits/     # V16 training data (archived)
│
├── docs/                        # Documentation (this directory)
│   ├── README.md                # Documentation index (this file)
│   ├── architecture/            # System architecture
│   ├── guides/                  # How-to guides
│   ├── reference/               # Canonical technical references
│   ├── status/                  # Status, incidents, and session summaries
│   ├── api/                     # API documentation
│   ├── troubleshooting/         # Troubleshooting guides
│   ├── iterations/              # Iteration notes
│   ├── benchmark/               # Benchmark reports
│   ├── training/                # Training documentation
│   └── archive/                 # Historical documentation
│
├── scripts/                     # Utility Scripts
│   ├── setup/                   # Setup scripts
│   ├── maintenance/             # Maintenance scripts
│   └── analysis/                # Analysis scripts
│
├── logs/                        # System Logs
│   ├── training/                # Training logs
│   ├── rag/                     # RAG service logs
│   └── evaluation/              # Evaluation logs
│
├── agents/                      # Agent Framework (Future)
│   ├── src/                     # Agent implementations
│   ├── config/                  # Agent configurations
│   └── tests/                   # Agent tests
│
└── README.md                    # Project overview
```

## Report and verification document placement

**Going-forward convention:** New report-like docs should be placed as follows. Existing documents may remain where they are; do not mass-move historical material without a dedicated migration plan.

- **docs/reports/** — Milestone completion, integration, merge, and freeze reports (e.g. merge readiness, verification, completion).
- **docs/status/** — Status snapshots, session summaries, and short-term operational context (living journal).
- **docs/runtime/verification/** — Runtime and structure verification: audits, E2E validation, constitutional reference, completion reports for Layer-3/runtime.

**Historical tolerance:** Materials already in these locations remain valid; this convention defines placement for new documents only.

## Documentation by Component

### Full Test Command

Canonical command to run all tests (runtime, ide, shadow, lineage, observation):

```bash
cd /path/to/m-coder && python3 -m unittest discover -s . -p 'test_*.py' -q
```

**Expected total test count:** 186 (as of this commit)

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
- **[models/](models/)** - Model-specific documentation
  - Model summaries and specifications
  - Architecture details
- **[training/](training/)** - Training guides and checklists
  - Training procedures
  - Finetuning checklists
  - Training examples

### 📚 Dataset Documentation
- **[datasets/](datasets/)** - Dataset analysis and specifications
  - Dataset quality verification
  - Dataset analysis and recommendations
  - Audit reports

### 🔌 RAG System
- **[runtime/rag/](../runtime/rag/)** - RAG system documentation
  - Implementation details
  - System iterations and analysis

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
- **[api/](api/)** - API documentation for all services
  - RAG API
  - vLLM API
  - Agent API (future)

### 🐛 Troubleshooting
- **[troubleshooting/](troubleshooting/)** - Debugging guides and FAQs
  - Debugging guides
  - Common issues and solutions
  - FAQ

### 🤖 Agent Framework
- **[agents/](agents/)** - Agent framework documentation (future)

### 📚 Historical Documentation
- **[iterations/](iterations/)** - Per-iteration notes and progress
- **[archive/](archive/)** - Historical and deprecated documentation

### 📌 4-Layer Architecture (Golden Exemplars)
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

## System Stats

| Component | Details |
|-----------|---------|
| Qdrant | 4,306 vectors (768 dim) |
| Neo4j | 10,262 nodes, 337K edges |
| GPU | H100 (90% VRAM, 32K context) |

## Service Management (governed stack)

Use **`runtime/scripts/governed_services.sh`** (`start` | `stop` | `restart` | `status`). Logs: **`runtime/.run/`** (`vllm.log`, `plan_gate.log`). Optional systemd: **`docs/guides/ORCHESTRATOR_SERVICE_GUIDE.md`**.

### View Component Logs
```bash
# vLLM logs
tail -f rag/logs/vllm.log

# RAG API logs
tail -f rag/logs/rag_api.log

# Health monitor logs
tail -f rag/logs/monitor.log
```

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
| RAG API | `rag/src/api/rag_api.py` | 8081 |
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

- **[README.md](README.md)** - This documentation index
- **[architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)** - System architecture
- **[evaluation/README.md](evaluation/README.md)** - Evaluation guide
