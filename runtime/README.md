## Runtime Namespace

This directory contains **runtime and deployment** components:

- `runtime/rag/` – RAG API, orchestrator, indexing, and retrieval code.
- `runtime/.config/` – runtime configuration (e.g., service settings, environment templates).

The goal of the `runtime/` namespace is to isolate **live system behavior** from:

- `governance/` – policy and Golden Exemplars,
- `ml/` – training and evaluation workflows, and
- `docs/` – narrative documentation.

Runtime enforces Phase-05 CODE semantics; it cannot redefine doctrine.

## Layer Boundaries

- **Allowed:** Plan gate, judge gate, authority validator, irreversibility detector, ledger emission, RAG/orchestrator integrations.
- **Forbidden:** Redefining doctrine; training pipelines; dataset compilation.

See [docs/ARCHITECTURE_4_LAYER.md](../docs/ARCHITECTURE_4_LAYER.md) for full 4-layer structure.

