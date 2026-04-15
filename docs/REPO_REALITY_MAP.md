# REPO_REALITY_MAP — major paths

**Status tags:** `CANONICAL` (navigation) · mixed **Canonicality** per row  
**Last updated:** 2026-04-14  

**Architecture:** The repo is organized around a **four-layer constitutional core** (L1–L4) plus **Layer-5 workspace intelligence** (Context Layer, evidence bundles, Assist — see `docs/ARCHITECTURE_4_LAYER.md`). Rows below **L5** mark Layer-5 product paths.

Use this table to orient in a large repo. **Product slice** column reflects `docs/PRODUCT_SLICE.md` (CLI-first validation pass).

| Path | Layer | Role | Canonicality | Product Slice | Current Relevance | Validation Surface | Notes |
|------|-------|------|--------------|---------------|-------------------|-------------------|-------|
| `governance/` | L1 | Constitution, exemplars, GREG | **CANONICAL** | IN (doctrine) | High — doctrine source | Pytest/docs spot checks | No ML/runtime code |
| `ml/` | L2 | Compilation, SFT, freeze artifacts | **CANONICAL** | OUT (slice proof) | High for ML line | ML release verification artifacts | Slice uses outputs, not training loop |
| `runtime/plan_gate_service/` | L3 | HTTP Plan-Gate daemon | **CANONICAL** | IN | **Critical** | `curl`, `motadata_behavior_verify.py`, health | v0/v1 Ask, plan, execute |
| `runtime/ask_service/` | L3 | Ask routing, Explain/Debug | **CANONICAL** | IN | **Critical** | HTTP + verifier | Plan-only invariants |
| `runtime/execute_service/` | L3 | Execute handlers | **CANONICAL** | IN | **Critical** | `/v0/execute` tests / verifier | Honest outcomes |
| `runtime/context_layer_service/` + `runtime/layer5/` | L5 product | Evidence export, retrieval | **CANONICAL** | IN | **Critical** | `export_evidence`, behavior verifier | `layer5.evidence_bundle.v1` |
| `packaging/motadata-context-layer/` | Packaging | Installable context layer | **CANONICAL** | IN | High | wheel + HTTP | No full checkout on WSL |
| `runtime/loop/` | L3 | Stage 3 controlled loop | **CANONICAL** | IN (impl) | High — burn-in closed | `pytest runtime/tests/test_stage3_loop.py` | IDE E2E = follow-on |
| `archive/legacy_runtime_rag/` | L3 | RAG API, indexing | **COMPATIBILITY** / parallel | **OUT** (`OUT_OF_PRODUCT_SLICE` in `PRODUCT_SLICE.md`) | Medium — tech debt | Targeted tests | Not primary governed path; not JetBrains bridge (audit) |
| `runtime/plangate/` | L3 | In-process gate | **CANONICAL** | IN | High for sandbox chain | Unit/integration | **≠** `plan_gate_service/` |
| `runtime/plan_gate_stub/` | L3 | CLI stub / protocol test | **COMPATIBILITY** | Secondary | Low — protocol | Stub CLI | Not production daemon |
| `runtime/ci_gate/` | L3 | CI backstop | **CANONICAL** | IN | Medium | CI | Calls Plan-Gate |
| `jetbrains-plugin/` | IDE | JetBrains client | **CANONICAL** (code) | IN (shipping) | **DEFERRED_INTEGRATION** for proof | UI manual / optional | B3 truthfulness **CLOSED** in tracker; **slice** still CLI-first — see `PRODUCT_SLICE.md` §0 |
| `observation/` | L4 | Drift tooling (CLI packages) | **CANONICAL** | IN (L4 tooling) | **High** — M4.x baseline | CLI | **L4 milestones M4.1–M4.6 complete on `main`** per tracker; not “partial” closure |
| `runtime/observation/` | L3/L4 | Traces, metrics | **CANONICAL** | IN | **High** | Logs/tests | See `docs/README.md` disambiguation |
| `runtime/obs/` | L3 | Stage 3 mini-ledger | **CANONICAL** | IN (Stage 3) | Medium | pytest artifacts | Minimal ledger |
| `docs/LIVE_ROADMAP_TRACKER.md` | Meta | Program truth | **CANONICAL** | IN | **Critical** | Human review | Single status dashboard |
| `docs/MASTER_SYSTEM_SPEC.md` | Meta | Spec index | **CANONICAL** | IN | High | N/A | Entry to layer specs |
| `docs/production_closure_handbook_corrected_canonical_version.md` | Meta | Narrative | **COMPATIBILITY** / **PARTIALLY_STALE** | Supporting | Low for gates | Historical | Superseded on **open/closed** by tracker |
| `docs/audit/` | Meta | Audits, inventories | **ARCHIVE** + **CANONICAL** (facts at time) | Supporting | High for forensic | N/A | END_TO_END audit still factual for paths |
| `docs/validation/` | Meta | Proof artifacts | **CANONICAL** (evidence) | IN | **Critical** | Artifacts + reports | B1/B5/B7 folders |
| `archive/` | Archive | Old spikes, notes | **ARCHIVE** | OUT | Low | Rare | `archive/README.md` index |
| `motadata_behavior_validation*.json` | Artifact | Verifier output | **CANONICAL** (run record) | IN | High | `motadata_behavior_verify.py` | Often gitignored pattern; check `.run/` |

**M3.12+ branch truth:** Per `docs/LIVE_ROADMAP_TRACKER.md` §1, **M3.0–M3.11** are **complete on `main`**. **M3.12** (and follow-on) may live on integration branches (e.g. L5 packaging line) until promoted — **do not** treat unmerged line items as the same baseline as `main` without checking the tracker and git.

**UNKNOWN / NEEDS_CONFIRMATION:** exact on-`main` presence of every M3.12+ line item — use git + tracker §1 for branch truth.
