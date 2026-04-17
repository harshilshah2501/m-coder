# SYSTEM_TRUTH — m-coder / Motadata AI Coding Assistant

**Status tags:** `CANONICAL` · `IN_PRODUCT_SLICE` (governed HTTP + workspace backend + GPU stack)  
**Last reconciled:** 2026-04-17 (against `docs/LIVE_ROADMAP_TRACKER.md`, `docs/PROGRAM_STATE_SNAPSHOT.md`, `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`, `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`)

This file is the **single navigation anchor** for “what the repo actually is right now.” Detailed doctrine remains in linked specs; **live closure and milestone truth** are owned by the tracker.

---

## 1. Authority order (non-competing)

| Priority | Source | Role |
|----------|--------|------|
| 1 | `docs/LIVE_ROADMAP_TRACKER.md` | Live program status, gate closures (B1–B7, Action 14), evidence pointers |
| 2 | `docs/MASTER_SYSTEM_SPEC.md` | 4-layer spec index, doctrine immutability clause, links to layer specs |
| 3 | `docs/mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md` | Formal production closure sign-off (with tracker) |
| 4 | `docs/ARCHITECTURE_4_LAYER.md` | Directory ↔ layer mapping, allowed/forbidden per layer |
| 5 | `docs/PRODUCT_SLICE_CHARTER.md` | Product-grade vertical slice contracts and host topology (JetBrains listed as client there; **active validation stance for this pass is CLI/HTTP-first** — see `docs/PRODUCT_SLICE.md`) |

**Supporting (not competing) narrative:** `docs/production_closure_handbook_corrected_canonical_version.md` — **PARTIALLY_STALE:** its “gates OPEN / blocking closure” tables predate tracker-recorded closure; treat tracker + Action 14 artifacts as **CANONICAL** for closure state.

**Root `README.md` Layer-3/Layer-4 status lines:** **NEEDS_CONFIRMATION / PARTIALLY_STALE** vs tracker (tracker: Layer-3 core milestones complete; Layer-4 M4.x complete on main). Prefer tracker for program status.

---

## 2. Canonical architecture truth (structural)

| Layer | Repo root | Role (summary) |
|-------|-------------|----------------|
| L1 Governance | `governance/` | Constitution, phases REF…REACH, GREG, exemplars |
| L2 Compilation | `ml/` | Pipeline, freeze, SFT; no runtime redefinition of doctrine |
| L3 Runtime | `runtime/` | Plan-Gate HTTP, Ask, execute, context/evidence, sandbox path, loop controllers |
| L4 Observation | `observation/` (+ `runtime/observation/`, `runtime/obs/` nuances) | Drift, traces; see `docs/README.md` observation disambiguation |

**Axis rule (non-negotiable from specs):** constitutional **phases** (REF, CONF, …) are orthogonal to **pipeline stages** (Stage-1…8). Stage-6 (mutation) ≠ Phase-6 (REACH).

**Runtime execution truth (from `docs/ARCHITECTURE_4_LAYER.md` + runtime README):**

- Governed user-triggered execution flows **Plan-Gate → sandbox/execute path → ledger**, not ad-hoc subprocess “execution” inside `archive/legacy_runtime_rag/` tooling.
- **Naming:** `runtime/plangate/` (in-process gate) vs `runtime/plan_gate_service/` (HTTP daemon) are **different** concepts — operational confusion is a known doc hazard.

---

## 3. Active execution path (production slice)

**Topology (single distributed model, not two products):**

- **Workspace-side backend:** Context Layer + retrieval near repo — **WSL or native Linux**.
- **Governed compute:** Plan-Gate + vLLM on **GPU host** (may be reached via localhost or tunnel per env).

**HTTP surfaces (Plan-Gate service):** `POST /v0/plan`, `POST /v0/ask`, `POST /v1/ask`, `POST /v0/execute`, `GET /healthz`, `GET /version` — implementation: `runtime/plan_gate_service/` (see `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md`).

**Context / evidence:** `POST /v1/export_evidence` on Context Layer; bundle schema **`layer5.evidence_bundle.v1`** (frozen contract).

**Ask paths:**

- **Compatibility / default IDE path:** `POST /v0/ask` when evidence-first is off.
- **Primary evidence-first path (CLI and opt-in IDE):** export → `POST /v1/ask` (see `runtime/scripts/verify_ask_path.sh`, `motadata_behavior_verify.py`).

**Stage 3 controlled loop:** Implemented under `runtime/loop/`; burn-in closure recorded in tracker (**B7**) and `docs/validation/STAGE3_BURN_IN_REPORT.md`. **IDE → `Stage3LoopController` live E2E** called out in tracker as **follow-on**, not identical to burn-in closure.

---

## 4. CLI-first validation stance (this documentation pass)

**Active closure / regression surfaces for ongoing work:**

| Surface | Status |
|---------|--------|
| **CLI + HTTP** (`motadata_behavior_verify.py`, `verify_ask_path.sh`, stack scripts) | **CANONICAL** for repeatable proof |
| **JetBrains plugin / IDE UI** | **DEFERRED_INTEGRATION** as *active* validation gate for this doc control-plane pass; contracts in plugin/bridge docs remain **COMPATIBILITY** references, not weekly proof criteria |

Operational runbooks that are IDE-centric remain **ARCHIVE / COMPATIBILITY** for operators who still use the UI; they do not override CLI-first proof for “current validation.”

---

## 5. Major invariants (extracted from locked tracker + specs)

| Invariant | Source of truth |
|-----------|-------------------|
| **Motadata behavior verification baseline (main):** `all_pass` scenario suite + promoted artifact SHA — **do not argue from stale “broad ask = WEAK”** narratives; Plan-Gate **`POST /v1/ask`** uses full grounding for `assess_evidence_quality` | `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`, `docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5 |
| Evidence bundle schema versioned and validated | `layer5.evidence_bundle.v1`, Layer-5 freeze language in tracker |
| Ask remains **plan-only** posture unless contract explicitly allows execution flags | Ask handlers / audit |
| **No silent fallback** on real service failures (controlled v1→v0 documented; contract errors do not silently “succeed”) | Audit + PRODUCT_SLICE_CHARTER |
| PR-6 retrieval baseline **LOCKED**; changes require re-validation on real repo | Tracker B1 / PR-6 language |
| Assist Layer (Stage 2.5) **advisory-only**; does not drive retrieval/runtime query inputs | Tracker §1.5 |
| Model outputs **untrusted** until runtime validation | `docs/PROGRAM_STATE_SNAPSHOT.md` |

---

## 6. Versioned contracts that still matter

| Contract | Location (typical) |
|----------|---------------------|
| `ask_request` v0.1 / v1.0 | `runtime/ide/schemas/` |
| `plan_request` / `decision_response` v0.1 | `runtime/ide/schemas/`, `runtime/schemas/` |
| `layer5.evidence_bundle.v1` | Packaged schema + runtime validation |
| Plan/ledger v0.1 | `docs/RUNTIME_PLAN_AND_LEDGER_V0_1.md`, `runtime/schemas/` |

IDE/plugin flow rules remain in `docs/JETBRAINS_PLUGIN_FLOW_V0_1.md` (**DEFERRED_INTEGRATION** for validation priority, **COMPATIBILITY** for API behavior).

---

## 7. Explicitly forbidden (from locked program + architecture docs)

- Redefining constitutional phase semantics or dominance outside GREG process (`MASTER_SYSTEM_SPEC` immutability clause).
- **Uncontrolled agent loops**; LLM-owned control flow for governed execution.
- Treating `archive/legacy_runtime_rag/` orchestration tooling as the governed execution path.
- **Embeddings / Neo4j / LangGraph / LLM reranking** as debt work — listed **DEFERRED** in `docs/PROGRAM_STATE_SNAPSHOT.md` (not “next sprint” unless tracker reopens).

---

## 8. Explicitly deferred (later integration / not CLI-first pass)

| Item | Tag |
|------|-----|
| JetBrains UI/plugin as primary **weekly** validation surface | `DEFERRED_INTEGRATION` |
| `Stage3LoopController` **live IDE** E2E | Follow-on per tracker / `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md` §7 |
| Semantic embedding retrieval **as a gate** | Charter Track C; lexical MVP baseline locked |
| Full product SaaS, multi-tenant RBAC | Out of charter slice |

---

## 9. Contradictions resolved (for readers)

| Topic | Conflicting sources | **Canonical winner** |
|-------|----------------------|----------------------|
| MVP gates open vs closed | `production_closure_handbook_*` vs tracker | **Tracker + Action 14 report** — gates **CLOSED** for declared MVP slice |
| Layer-3 “in progress” vs milestones complete | Root `README.md` vs tracker | **Tracker** — core Layer-3 milestone line items **COMPLETE** per tracker §1 |
| B1 “ongoing” vs “closed” | Various validation docs | **Tracker:** B1 **CLOSED** with expanded suite; residual metrics may show **warnings** without reopening baseline |
| **`evidence_quality` for broad / integration asks (WEAK vs STRONG)** | Older stdout / pre-**`108aabb`** runs vs current **main** | **§5 + closure doc:** after Ask v1 quality parity, verifier-visible **`ask_broad_correlation`** / **`ask_servicenow_sync_owner`** can report **STRONG**; cite artifact + commit in `MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5 |

---

## 10. Related canonical navigation

- `docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md` — Motadata CLI verification closure (baseline pointers; team handoff)
- `docs/validation/POST_CLOSURE_MAINTENANCE.md` — ongoing operational lock + optional charters (not open closure todos)
- `docs/PRODUCT_SLICE.md` — in/out of scope for *this* pass  
- `docs/REPO_REALITY_MAP.md` — directory map  
- `docs/CLI_VALIDATION_MATRIX.md` — proof commands  
- `docs/WORKFLOW_TRUTH_TABLE.md` — end-to-end workflows  
