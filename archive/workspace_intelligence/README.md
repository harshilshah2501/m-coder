# Archived — workspace intelligence spikes

**Status:** Moved from repo root (`workspace_intelligence/`) — **2026-04-14**.

Layer‑5 **production** retrieval and evidence live under **`runtime/layer5/`** and **`runtime/context_layer_service/`**. This tree kept only the **Wave‑1 / A1 grounded retrieval spike** (`spikes/`).

## Running the spike harness (optional)

From repository root, put `archive` on `PYTHONPATH` so the `workspace_intelligence` package resolves:

```bash
PYTHONPATH=archive python -m workspace_intelligence.spikes.grounded_retrieval_harness /path/to/workspace
```

Do **not** treat this as a supported operator path; prefer the governed Context Layer + runtime tests.
