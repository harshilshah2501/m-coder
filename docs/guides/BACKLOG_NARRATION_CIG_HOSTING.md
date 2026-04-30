# Backlog — narration quality + CIG browser hosting

**Purpose:** Prioritized work for **human-friendly, explanation-first responses** and a **hosted Code Intelligence Graph (CIG)** explorer with polished browser UX.

**Audience:** Implementers shipping Motadata AI Coding Assistant on WSL + Plan-Gate.

---

## P0 — Understand the bottleneck (one audit loop)

- Trace **one** disappointing Ask end-to-end: capture `evidence_bundle`, `reasoning_context`, `articulated_answer`, `metadata.ask_narration_source` (`governed_vllm` vs deterministic).
- Confirm whether **governed vLLM** ran (`MCODER_GOVERNED_ASK_NARRATOR=1` on Plan-Gate, `MOTADATA_EXPLAIN_VLLM_URL` reachable) or output fell back to **deterministic** composers only.

---

## P1 — Evidence breadth (**conditional** — only if P0 proves thin/wrong bundles)

Do **not** start P1 unless P0 shows the **`evidence_bundle` is actually thin or wrong** for representative prompts. If `reasoning_context` is rich but prose still feels bad, prioritize **P2/P3** first.

When triggered:

- Tune Context Layer retrieval for **explain / architecture / how** intents: `top_k`, fusion, and intent so bundles include **multiple files** and **method-level** snippets, not a single anchor class list.
- Add or tighten **intent-specific retrieval policy** (Layer-5 fusion / quality gate) where “explain” queries need broader neighborhood than “lookup symbol.”

---

## P2 — Governed narration (natural prose, grounded symbols)

- **Plan-Gate:** Iterate **bounded ask narrator** prompts (`runtime/ask_service/bounded_ask_narrator.py`): lead with direct answer, 2–4 short paragraphs, explicit “where to look next.”
- **Validation:** Balance governance (allowlists, generic-phrase filters) with **avoiding over-rejection** that forces thin fallback prose.
- **Ops:** Document required env on GPU/WSL: `MCODER_GOVERNED_ASK_NARRATOR`, `MOTADATA_EXPLAIN_VLLM_URL`, model id, timeouts.

---

## P3 — Deterministic narration polish (when vLLM is off or fails) — **primary path with P2**

- **`articulated_answer` / `answer_shaping`:** Continue separating **plan vs structural vs explain vs list**; **at most one** short confidence/limitation sentence in user-facing output.
- **`next_step`:** Phrase as actionable colleague hints, not internal scaffolding.
- **Banned in default user prose** (keep in JSON/debug only): `Flow evidence indicates`, `receives or initiates processing`, `Graph path`, `partial graph`, `evidence-bounded`, and similar diagnostic labelling.

---

## P4 — Evaluation (what “better” means)

- Add **subjective or LLM-judge rubrics** (directness, structure, non-redundancy, actionable next step)—not only `ok` / `owner_anchor` flags.
- Keep a small **golden prompt set** for regression on narration regressions.
- **Target bar:** fluent, direct answer; **no** banned graph/debug wording in human-visible lines; **one** confidence/limitation sentence max.

---

## P5 — Optional retrieval upgrade (only if audits show thin bundles)

- If traces show **wrong or sparse files**, consider **embedding-backed retrieval** (existing Qdrant/RAG direction in repo config, or another store)—as **retrieval only**, not as a replacement for CIG structure.

---

## P6 — **CIG hosting service + beautiful browser rendering** (new)

**Goal:** Run a **small HTTP service** (e.g. on WSL next to the workspace) that serves **read-only** views of **built CIG artifacts** (`code_intelligence_graph.v1.jsonl`, manifest, adjacency—see `runtime/layer5/graph/storage.py`, build via `runtime/scripts/build_code_intelligence_graph.py`).

### Functional requirements

- **Read artifacts** from a configurable directory (default: align with Plan-Gate / CLI expectations, e.g. `runtime/.cache/code_intelligence_graph` or env `MCODER_CIG_ARTIFACT_DIR`).
- **API (JSON):**
  - `GET /healthz` — service + artifact presence
  - `GET /api/v1/manifest` — stats, content hash, repo identity (from manifest)
  - `GET /api/v1/graph?focus=` — optional query: class name / file prefix / node id; return **bounded** nodes/edges (pagination / max nodes) to avoid loading huge graphs in the browser
  - `GET /api/v1/node/:id` — neighborhood slice (optional)
- **Security:** default bind **`127.0.0.1`**; document optional reverse proxy + auth for LAN access.

### UX / “beautiful rendering”

- **Single-page web UI** served by the same service (static `index.html` + JS bundle or lightweight framework):
  - **Graph view:** force-directed or hierarchical layout (`cytoscape.js`, `vis-network`, or similar); **dark/light** theme consistent with dev tools aesthetic; clear **legend** for edge types (`CALLS`, `EXTENDS`, `IMPORTS`, etc.).
  - **Inspector panel:** click node → show label, kind, attributes, linked file path.
  - **Search / focus:** jump to class or file; **fade unrelated** nodes or show k-hop neighborhood.
  - **Empty state:** if artifacts missing, show **how to build** CIG (link to script / one command).

### Integration notes

- **Does not replace Neo4j Browser** for the Java AST Neo4j stack; this backlog item is **CIG-specific**. Long-term, optional **loader from CIG JSONL → Neo4j** remains a separate consolidation story (`docs/design/CODE_INTELLIGENCE_GRAPH_V1.md`).
- **Placement in repo:** e.g. `runtime/cig_viewer_service/` or extend `runtime/layer5/api/skeleton.py` with graph routes + static assets—keep Plan-Gate and Context Layer unchanged; this is **read-only visualization**.

### Acceptance criteria

- Developer on WSL runs **one command**, opens **browser** to `http://127.0.0.1:<port>/`, sees manifest summary and interactive graph for a workspace where CIG was built.
- No write paths; no execution authority; **read-only** inspection.

---

## Suggested execution order (tightened)

1. **P0** — confirm `ask_narration_source` and fallback reason; capture one full Ask JSON.
2. **P2** — governed vLLM narrator contract (fluent, direct, evidence-bounded).
3. **P3** — deterministic fallback tone and banned-phrase cleanup.
4. **P4** — golden prompts + rubric (include acceptance bar above).
5. **P1** — **only if** P0 proves the evidence bundle is thin or wrong (not the default if `reasoning_context` is already present).
6. **P6 CIG viewer** — **parallel only**; does not block narration work.
7. **P5** — only if P1 trigger fires and embeddings are the next lever.

---

## References

- P0 one-shot audit: [P0_ASK_NARRATION_AUDIT.md](P0_ASK_NARRATION_AUDIT.md)
- CIG artifacts: `runtime/layer5/graph/storage.py`, `runtime/scripts/build_code_intelligence_graph.py`
- Ask graph payload: `runtime/ask_service/graph_traversal_payload.py`
- Articulated Ask: `runtime/ask_service/articulated_answer.py`, `runtime/ask_service/bounded_ask_narrator.py`
- Neo4j stack (separate): `docker/neo4j-graph/README.md`
- Design policy (single truth, optional projections): `docs/design/CODE_INTELLIGENCE_GRAPH_V1.md`
