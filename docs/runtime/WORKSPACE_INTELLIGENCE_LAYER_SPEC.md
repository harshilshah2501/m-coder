# Workspace Intelligence Layer Spec (Anchor)

**Status:** canonical-current (anchor/pointer).  
**Purpose:** long-term anchor for workspace-local context retrieval boundaries and ownership.

---

## Canonical detailed specification

The full architecture specification lives at:

- [`docs/architecture/workspace_intelligence_layer_final_architecture_spec.md`](../architecture/workspace_intelligence_layer_final_architecture_spec.md)

This anchor exists to keep runtime-facing documentation discoverable without duplicating the full design text.

---

## Scope boundary (authoritative summary)

- **Workspace Intelligence Layer (WSL/local workspace):**
  - repo discovery and revision awareness
  - symbol/index retrieval
  - snippet/evidence bundling
  - selector provenance
- **Plan-Gate + vLLM (GPU):**
  - governance, reasoning, bounded planning/fix decisions
  - consumes structured evidence bundle
  - does not require direct workspace filesystem access in target mode
- **JetBrains plugin (Windows):**
  - interaction surface
  - orchestration client across workspace context layer and Plan-Gate

---

## Contract direction

Target production contract direction:

1. Retrieval and grounding happen near the workspace.
2. Ask/Explain send structured evidence bundles upstream.
3. Direct `repo_root` dependency at remote runtime is compatibility/demo path, not final architecture center.

---

## Related docs

- [`JETBRAINS_PLUGIN_DEMO_GUIDE.md`](JETBRAINS_PLUGIN_DEMO_GUIDE.md)
- [`motadata_ai_coding_assistant_final_closure_plan.md`](motadata_ai_coding_assistant_final_closure_plan.md)
- [`motadata_ai_coding_strategy_capability_roadmap.md`](motadata_ai_coding_strategy_capability_roadmap.md)
- [`../LIVE_ROADMAP_TRACKER.md`](../LIVE_ROADMAP_TRACKER.md)
