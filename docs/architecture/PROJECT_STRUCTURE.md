# RAG-Datastore Project Structure

## Overview
This is the Motadata Coder RAG system - a code intelligence platform that combines semantic search (Qdrant), graph-based relationships (Neo4j), and LLM inference (vLLM) to provide context-aware code assistance.

## Directory Organization

```
RAG-Datastore/
├── README.md                    # Main project documentation
├── PROJECT_STRUCTURE.md         # This file
│
├── rag-system/                  # Core RAG implementation
│   ├── rag_api.py              # Main FastAPI server (port 8081)
│   ├── qdrant_indexer.py       # Vector database indexing
│   ├── project_indexer.py      # Project-wide indexing orchestrator
│   ├── diagnostic_logger.py    # Debugging and tracing utilities
│   ├── docker-compose.yml      # Infrastructure setup (Qdrant, Neo4j)
│   ├── logs/                   # Runtime logs and debug sessions
│   ├── systemd/                # Systemd service files
│   └── qdrant_storage/         # Qdrant vector database storage
│
├── docs/                        # Documentation and reports
│   ├── Motadata-Coder.md       # System design and architecture
│   ├── ITERATION_8_PLAN.md     # Current iteration plan
│   ├── PHASE_2_PROGRESS.md     # Dataset preparation progress
│   ├── EVALUATION_REPORT.txt   # Model evaluation results
│   ├── FUNCTIONAL_TEST_REPORT.txt
│   ├── RAG_STATUS_REPORT_*.md  # System status reports
│   └── RD_ACTION_PLAN.md       # Research & development roadmap
│
├── evaluation/                  # Model evaluation suite
│   ├── evaluate_finetuned_model.py      # Standard evaluation (10 tests)
│   ├── evaluate_agentic.py              # Agentic evaluation (5 tests)
│   ├── evaluation_report_iter6.json     # Iter 6 results
│   ├── evaluation_report_iter7.json     # Iter 7 results
│   └── evaluation_report_agentic_iter7.json
│
├── training-artifacts/          # Training datasets
│   ├── dataset_b_multifile.jsonl        # Multi-file planning examples (691)
│   └── benchmark_jira.jsonl             # JIRA-sourced examples
│
├── scripts/                     # Utility scripts
│   └── test_graph_population.py         # Neo4j graph testing
│
├── archive/                     # Historical/deprecated code
│   └── 1-context-engine/       # Legacy context engine implementation
│
└── test_project/                # Sample project for testing
