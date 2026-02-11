## Runtime Namespace

This directory contains **runtime and deployment** components:

- `runtime/rag/` – RAG API, orchestrator, indexing, and retrieval code.
- `runtime/.config/` – runtime configuration (e.g., service settings, environment templates).

The goal of the `runtime/` namespace is to isolate **live system behavior** from:

- `governance/` – policy and Golden Exemplars,
- `ml/` – training and evaluation workflows, and
- `docs/` – narrative documentation.

