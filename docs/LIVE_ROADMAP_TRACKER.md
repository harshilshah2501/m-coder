# LIVE ROADMAP TRACKER — Motadata AI Coding Assistant

**Doc status:** canonical-current. Live progress dashboard; status is artifact-driven.

## 0. Reconciliation snapshot (2026-04-18)

**Purpose:** Single place for **Completed** vs **remaining**. Sections below retain full history; use this table when prioritizing. **Ops checklist:** `docs/validation/POST_CLOSURE_MAINTENANCE.md`.

### Completed workstreams (canonical “done”)

| Item | Notes |
|------|--------|
| **MVP production closure** | Action 14 **PASS**; gates closed — §1.2–§1.3 |
| **B1 Retrieval generalization (closure bar)** | **CLOSED** — §B1 |
| **B2 L5.8 harness + closure gate** | **COMPLETE** — §B2 |
| **B3 Plugin truthfulness (MVP bar)** | Action 4 **CLOSED**; Phase-1 truth proof **LOCKED** — §B3 |
| **B4 Observability / trace reconstruction** | **CLOSED** — §B4 |
| **B5 Host readiness** | **CLOSED** — §B5 |
| **B6 L5.9 compatibility hardening** | Action 11 **CLOSED** — §B6 |
| **B7 Stage 3 burn-in / acceptance** | **CLOSED** — §B7 |
| **Debug Usefulness v1.1** | EXPLAIN_DEBUG grounding — §5 |
| **Authority Expansion Hardening v1** | Stage A noise suppression; API routing scenario — §5 |
| **Ask v1 evidence quality parity** | `108aabb` on `main`; `POST /v1/ask` uses grounding for `assess_evidence_quality` |
| **Behavior baseline promotion** | `MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5 + `MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md` |
| **Layer-1 / L2 / L4 milestone tables (declared rows)** | **LOCKED** or **COMPLETE** per §2.1; layer rollups per §2.1.1; details §4.1–§4.4 |
| **M3.0–M3.12** | **COMPLETE on main** — §4.3.1 (M3.12 narrow manifest + `doc_selector`; §6.16.1) |
| **M4.1–M4.6** | **COMPLETE on main** — §4.4 |
| **L5.0–L5.6, L5.8 harness, L5.9** | Per §4.5 table (harness closure + Action 11) |
| **Action 9 (WSL + audit pack MVP scope)** | **CLOSED** — §1 Action 9 table |

### **Remaining / follow-on (not done — evaluate before staffing)**

| Area | Status | Where |
|------|--------|--------|
| **L5.7** Dirty buffer / live overlay | **NOT_STARTED** | §4.5 row L5.7 |
| **M3.13–M3.16, M3.18** | Jira/PR pipelines, evaluation harness — **NOT_STARTED** | §4.3.1 |
| **§1.4 tracks** | L5-OBS ops follow-through; L5-RET / §B1 expansion; **CHARTER-TBD** debug depth | §1.4 |
| **IDE → Stage3LoopController E2E** | **Follow-on** (not burn-in closure) | §B7, §6.20, runbook §7 |
| **§B3 residual** | e.g. `plan_summary.notes` on all surfaces | §B3 bullets |
| **Assist influence** | **NOT ENABLED** (advisory-only by design) | §1.5 |
| **Caveat F1 / F2** | Resolver layout; A3 latency vs spine | Backlog § under Layer-5 |
| **“What is NOT included yet”** | Stage 2.5 influence, background sync, active-file UX | §1 “What is NOT included yet” |

---

## 1. Header

- **Project**: Motadata AI Coding Assistant — 4-Layer Governed Core + Layer-5 Product Extensions  
- **Last updated**: 2026-04-18  
- **Program state**: **Production-grade vertical slice achieved.** All production gates are closed with artifact-backed acceptance.
- **Current active layer**: **Program closure baseline (all core layers validated)**  
- **Update (2026-04):** Motadata **behavior verification + Ask v1 quality** work is merged to **`main`**. **M3.12** narrow doc-manifest slice is **on `main`** (see §6.16.1).  
- **Program objective (next):** **Controlled expansion from a closed baseline** — preserve governed execution honesty, observability, and reproducibility while adding non-MVP capabilities intentionally.  
- **Previous focus (done):** Authority Expansion Hardening v1 + baseline stabilization. **Current focus:** **post-closure maintenance** (`docs/validation/POST_CLOSURE_MAINTENANCE.md`) and **optional charters** (§1.4: debug depth **CHARTER-TBD**, §B1/L5-RET with §5 guardrails).
- **Overall status summary**:  
  - **Layer-1** — **LOCKED** (governance doctrine).  
  - **Layer-2** — **LOCKED** (ML compilation: Stage-6C cure, deterministic CONF, release verification PASS).  
  - **Layer-3** — **COMPLETE** (M3.0–M3.12 on `main`): core M3.0–M3.11 plus **M3.12** narrow manifest + **`doc_selector`** (§6.16.1). **M3.13–M3.18** follow-on. **Governed execute** (`POST /v0/execute`) is validated for truthful outcomes in the closed MVP slice.  
  - **Layer-4** — **COMPLETE** (M4.1–M4.6 + Track-C on `main`; merged 2026-03-15; see `docs/reports/M4X_MAIN_MERGE_COMPLETION.md`).
  - **Layer-5** — **CLOSED** (MVP slice). Waves A1–A8 and packaging slice delivered — deterministic index, lexical retrieval, evidence `layer5.evidence_bundle.v1` frozen; plugin evidence-first + Plan-Gate **`POST /v1/ask`**; installable `**packaging/motadata-context-layer`** wheel + `**runtime/context_layer_service**` HTTP API (**no m-coder checkout required on WSL**). **Product Authority + Code Understanding v1 — Phases 1–5 COMPLETE** (registry → index → ranking → Plan-Gate anchoring + eval → authority → action reasoning bridge). **L5.8 — harness + closure gate:** **COMPLETE** (see **B2**; **§4.5** milestone row). **B1/B3/B4/B5/B7:** **CLOSED**. **Action 14 final acceptance:** **PASS**. Production gates are closed; this tracker now records post-acceptance continuity.

### What is NOT included yet

- Stage 2.5 proactive intelligence is not influence-enabled in production (Assist remains advisory-only)
- Background sync
- Active-file UX improvements

### Action 9 — sub-status (surgical)

| Action | Status |
|--------|--------|
| 9 — WSL backend host (release validation) | ✅ CLOSED |
| 9 — Audit pack (trace + packaging) | ✅ Closed for MVP closure scope (operational follow-through only) |

**Operational follow-through (non-blocking; does not affect closure truth):**

- `mapping_request_ids.md` (trace spine — template `docs/guides/mapping_request_ids.md`; partial worked example: `docs/guides/HOST_A_PLAN_GATE_LOG_MAPPING.md`)
- Per-scenario folder packaging (`hostA_proof_pack/` layout in `docs/guides/HOST_A_PROOF_PACK_CLOSURE.md`)
- Backend + plugin **validation sheets** (same closure doc §5)

### 1.1 Known system realities (do not skip)

- **Dual Ask path:** JetBrains may call `**POST /v0/ask`** unless **evidence-first** is ON (`motadata.ask.evidence_first` / `MOTADATA_PLUGIN_ASK_EVIDENCE_FIRST`). Backend validation scripts for `**POST /v1/ask`** are **not** the same default path as the IDE — this is a **known system condition**, not operator error.
- **Evidence-first default:** **OFF** in plugin — alignment with `**layer5.evidence_bundle.v1`** + `/v1/ask` is **opt-in**.
- **Observability closure:** B4 trace reconstruction is **CLOSED** with artifact-backed request correlation across Context Layer, Plan-Gate, and execution-path evidence.
- **Retrieval:** anchored authority-gated retrieval baseline is now **WORKING / LOCKED** on current branch (`ask_anchor_owner_top1` strict gate pass; scenario suite pass). Broad ask retrieval is **improved** (reduced generic-infra dominance) but intentionally tracked as non-final tuning.
- **Distributed topology (single architecture):** backend (Context Layer, retrieval) near the workspace (**WSL or native Linux**); **Plan-Gate + vLLM on GPU** — not separate product “profiles.” **§B5** host readiness across both placements is **CLOSED** (2026-04-09) — **`docs/validation/B5_HOST_READINESS.md`** §0. Plugin **Plan-Gate base URL defaults to** `127.0.0.1:8089` (**`motadata.plan_gate.url`** / **`MOTADATA_PLAN_GATE_URL`** override); remaining URL externalization backlog is operational, not a B5 blocker.
- **IDE operator demo:** `docs/runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md` — Plan-Gate + plugin flows; **does not** exercise **`Stage3LoopController`** (see **§6.20**, **docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md**).

### 1.2 Current truth state (locked)

**MVP production closure state:** **CLOSED**. Action 14 final acceptance is **PASS** with artifact-backed evidence. Current acceptance authority: `docs/validation/artifacts/action14_final_acceptance/ACTION14_FINAL_ACCEPTANCE_REPORT.md`.

**Plugin Phase-1 truth proof:** **LOCKED** — frozen matrix and scenario artifacts under `docs/validation/artifacts/plugin_phase1_truth_proof/`; closure authority `docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md`; evidence log **§6.22**. Offline regression: `Phase1TruthProofHarnessTest.phase1ProofMatrixFrozenContract`. **Distinct from** residual **§B3** checklist items (e.g. `plan_summary.notes` visibility on all product surfaces).

| Surface                                                                     | State                                                                                                                                    |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Backend** (Context Layer + Plan-Gate + vLLM stack when started)           | **Functional** for HTTP contracts per validation sheet                                                                                   |
| **JetBrains plugin**                                                        | **Primary user surface** — **Action 4 CLOSED** (**§6.18**); **Phase-1 truth proof LOCKED** (**§6.22**, `PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md`). |
| **True end-to-end** (IDE → evidence → `/v1/ask` → honest UI + traceability) | **Production-grade vertical slice validated** (Action 14 PASS; governed and observable)                                                         |


### 1.3 Production gates closure record

All production gates are now **closed** for the MVP vertical slice:

- **Plugin v1 evidence-first path** validated for production intent.
- **Evidence visibility and insufficiency honesty** validated.
- `ask_path` visibility and path truthfulness validated.
- `plan_summary.notes` and truthful operator context validated in closure scope.
- `POST /v0/execute` outcome honesty validated (executed vs blocked vs refused).
- **Request tracing** validated as reconstructible across Context Layer and Plan-Gate, with execution-path correlation.
- **Action 14** final acceptance run: **PASS**.

### 1.4 Explicit follow-on tracks (post-closure; non-blocking)


| Track                    | ID                                     | Scope                                                                                                                                                                                                                     |
| ------------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Observability**        | **L5-OBS-1 (ops follow-through)**                           | Closure already achieved for MVP bar. Follow-through remains operational (log packaging, CI collection, runbook hygiene). |
| **Retrieval validation** | **L5-RET-VALIDATION (post-closure expansion)** | Closure already achieved for MVP bar. Follow-through supports broader expansion confidence without reopening B1/B2 closure. **Guardrail:** any exploratory / broad-ask tuning must preserve **`MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5** invariants (re-run `motadata_behavior_verify.py`; compare metrics; do not regress named baseline).                                                                                                      |
| **Debug depth / “thinking with code”** | **CHARTER-TBD (separate initiative)** | Not “more retrieval” or fusion churn. Explicit scope required: prompts, selection, vLLM constraints, or richer **`explain_debug`** output. Track apart from lexical/Stage A work unless tracker merges lanes. |
| **§B1 expanded suites / exploratory asks** | **§B1 / L5-RET (existing)** | Only with **metrics + guardrails** against **`docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5** — same scenario suite and policy file; document regressions with artifact diff + m-coder SHA. |


**Related audit artifacts:** `docs/audit/END_TO_END_SYSTEM_AUDIT_REPORT.md`, `docs/audit/SURGICAL_NEXT_STEPS_PLAN.md`.

### 1.5 Stage 2.5 — Assist Layer v1 (Advisory) closure

**Status:** **IMPLEMENTED + EVALUATED**

- Assist Layer v1 is implemented and integrated as an advisory-only layer.
- Runtime authority is preserved:
  - original query remains runtime Ask input.
  - augmented query is additive metadata only.
- Runtime behavior remains unchanged by Assist (no Plan-Gate behavior change, no execution authority, no query-flow authority).

**Actions 15–17 closure (evaluation / benchmark / confidence policy):**

- Dual-path evaluation harness is in place (original vs augmented) with deterministic comparator and severity scorer.
- Batch benchmark runner is in place with categorized dataset and artifact generation at:
  - `docs/validation/artifacts/assist_layer_v2_eval/`
- Dataset size and coverage:
  - 35 queries across `typo_normalization`, `abbreviation_expansion`, `clean_control`, `ambiguous_query`, `garbage_or_fragment`.

**Measured results (artifact-backed):**

- improved: **0**
- same: **17**
- degraded_minor: **16**
- degraded_major: **2**

**Interpretation:**

- Assist is often neutral.
- Minor retrieval drift is frequent.
- Major degradation exists but is uncommon.
- No consistent measurable improvement is demonstrated in the current batch.

**Confidence policy artifact:**

- `docs/validation/artifacts/assist_layer_v2_eval/assist_confidence_policy.v1.json`
- Current policy outcome:
  - no transforms qualify as SAFE.
  - transforms are in caution or block zones only.
- Policy is evidence-derived, advisory-only, and not runtime-enforced in this pass.

**Final system stance (locked for this stage):**

**Assist Layer v1 is advisory-only and not trusted to influence runtime query behavior.**

- `augmented_query` is not used for retrieval or reasoning runtime inputs.
- Assist outputs are used for inspection, observability, and future evaluation only.

**Closure classification:**

- Stage 2.5 v1: **IMPLEMENTED + EVALUATED**
- Assist influence: **NOT ENABLED (by design, based on evidence)**

**Forward dependency note:**

- Any future Assist influence depends on reducing degraded cases, establishing measurable safe zones, and passing stricter evaluation thresholds.

## CURRENT SYSTEM REALITY (POST VALIDATION)

### Backend
- Context Layer + Plan-Gate + vLLM path is **contract-correct and governed**
- `/v1/ask` evidence-first path validated
- execution path (`/v0/execute`) is honest and deterministic
- **Stage 3 controlled runtime loop** — **implemented** in-repo (`runtime/loop/`, schema contracts, validators, tests); **§B7** burn-in / acceptance **CLOSED** (offline pytest + native live smoke + WSL+tunnel `verify_ask_path` — **§B7**, `STAGE3_BURN_IN_REPORT.md` §9). **Product `Stage3LoopController` E2E** with live IDE traffic remains **follow-on** per runbook **§7** (**§6.20**).

### Retrieval
- Deterministic lexical + symbol retrieval foundation is materially strengthened
- **PR-6** true-positive debug retrieval baseline is **LOCKED** on real Motadata repo:
  - Top-1 accuracy: **10/10**
  - Top-3 anchor hit: **10/10**
  - Mean first relevant rank: **1.00**
  - Mean top-5 noise dominance: **0.00**
- Remaining retrieval risk is **generalization beyond the locked debug fixture set**, not raw noise-dominance rescue

### Plugin
- Plugin truthfulness closure is **CLOSED** for MVP scope (**Action 4**, **§6.18**)
- Phase-1 truth proof is **LOCKED** (**§6.22**)

### System Status
- Backend: FUNCTIONAL
- Retrieval: BASELINE LOCKED (PR-6); **generalization / expanded validation** **CLOSED** (**§B1**); **L5.8 harness** CLOSED (**B2**) — do not conflate harness closure with open-ended RET work
- Plugin: **CLOSED for MVP truth bar** — Action **4** **CLOSED** per **§6.18**
- Stage 3 loop: **IMPLEMENTED** (pytest-green); **§B7** **CLOSED**; **product path** follow-on = runbook §7 where needed (**§5**, **§6.20**)
- End-to-end: **PRODUCTION-GRADE VERTICAL SLICE ACHIEVED** (**Action 14 PASS**; B1/B3/B4/B5/B7 closed)

## PRODUCTION CLOSURE RECORD (BLOCKERS RESOLVED)

### B1 — Retrieval Generalization & Validation (NON-NEGOTIABLE)
**Status:** **B1 — CLOSED**
- Expanded golden suite + perturbations executed on canonical corpus.
- Deterministic harness + artifact generation in place (`docs/validation/artifacts/b1_retrieval_validation/`).
- Targeted fixes applied:
  - weak-evidence classification alignment
  - topology/cache-target retrieval correction
  - metric/threshold semantics correction (scoped gates)
  - latency gate calibration
- PR-6 invariants preserved.
- No architecture / retrieval model changes.

**Residual warnings (tracked follow-through signals, not B1 blockers):**
- `latency_p95_ms` — warning (tail latency concentrated in debug stacktrace family).
- `evidence_drift_rate` — warning (residual classification/retrieval interaction cases).

### B2 — Grounded Ask Validation — **L5.8 harness + closure gate** (COMPLETE)
**Status:** **COMPLETE** (this subsection is the **L5.8 baseline/harness closure**; it is **not** “ongoing L5.8” vs “NOT_STARTED” in **§4.5** — see table row for the single reconciled status model). **§6 evidence pointer:** **§6.19a**.  
**Linked Closure Action:** **Action #3 (closed)**  
**Follow-through (separate track, not a second L5.8 completion state):** expanded golden suites, generalization beyond the locked fixture set, and production SLO maturation continue under **§B1**, **L5-RET-VALIDATION**, and **§1.4 Track RET** — **not** a reopen of harness closure.  
**PR-6 baseline remains locked on canonical real-repo context. Current L5.8 hardening includes guard-context enforcement so synthetic or shifted-root corpora cannot produce false baseline regression signals.**  
**Progress checklist:**  
- [x] Deterministic L5.8 harness scaffolding landed in `runtime/layer5/audit` (`l58_dataset`, `l58_evaluator`, `l58_perturbations`, `l58_drift`, `l58_report`, `l58_grounded_harness`)  
- [x] Golden dataset + thresholds fixtures added (`l58_golden_queries.v1.json`, `l58_thresholds.v1.json`)  
- [x] Perturbation determinism snapshot test added (`test_l58_perturbation_snapshot.py`)  
- [x] PR-6 protected subset enforcement wired into harness evaluation path  
- [x] JSON + Markdown harness report outputs added  
- [x] CI smoke/full harness invocation wired in workflow  
- [x] Validate L5.8 harness against canonical PR-6 reference environment with zero protected-subset regressions  
- [x] Promote L5.8 to **COMPLETE** after closure-gate validation and PR-6 preservation checks  
**Final state note:** canonical full-run latency p95 is ~339 ms, no remaining hard failures, and residual latency warning threshold is non-blocking.
- Query → expected files mapping
- top-k correctness validation
- false positive / false negative tracking
- no-match honesty enforcement

### B3 — Plugin Truthfulness
- **Action 4 — Close plugin truthfulness gaps** — **Status: ✅ CLOSED** — canonical paragraph **§6.18** (tracker-ready wording).
- **Phase-1 truth proof (S1–S8, exact_match)** — **Status: ✅ LOCKED** — **§6.22**; frozen artifacts + offline contract test.
- Show ask_path
- Show plan_summary.notes
- Fix "(no files selected)" misleading cases
- Correct execute outcome UX

### B4 — Observability (L5-OBS-1)
- **Action #5 (2026-03-31):** **CLOSED** — **§6.19**, `docs/guides/ACTION_5_OBSERVABILITY_CORRELATION.md`. Plan-Gate and Ask/Execute services emit grep-stable correlation; proof-pack reconstruction without inference for the HTTP path.
- **B4 follow-through — trace reconstruction (2026-04-08):** **CLOSED** — artifact-backed proof that a single `REQUEST_ID` + `TRACE_ID` spine reconstructs the full lifecycle across **Context Layer** (`/v1/export_evidence`), **Ask** (`[ASK_V1]` ingest + Plan-Gate `POST /v1/ask`), **Plan-Gate execution** (`POST /v0/execute`), and **execution outcome** (response + `PLAN_GATE request` logs). Prior Ask/explain path proof plus this execute-path proof complete **§B4** closure bar.
- **Residual (operational, not §B4 closure scope):** vLLM process logs and CI runbook collection as needed; **Action 9** audit-pack packaging remains tracked separately.
- **Coverage (locked):** `request_id` / `trace_id` propagation (Context Layer, Plan-Gate, reasoner/explain where exercised); Plan-Gate request logging with endpoint path; traceability for Ask / Debug / Execute.

### B5 — Host Readiness (environment hardening)
**Status:** **B5 CLOSED** (2026-04-09) — **`docs/validation/B5_HOST_READINESS.md`** §0. **Proof:** native Linux `docs/validation/artifacts/b5_linux_backend_gpu/`; WSL `docs/validation/artifacts/b5_wsl_backend_gpu/` + `docs/validation/b5_wsl_backend_gpu/`. Same HTTP contracts; GPU-governed Plan-Gate + vLLM; `/v0/ask` **PLAN_ONLY** / `execution: false` / no silent failure on success path.
- **Hardening (unchanged):** `runtime/config/host_local.env.example` (ports + URLs + `WORKSPACE_ROOT`), `runtime/scripts/run_local_stack.sh` (Context Layer start/stop/health + persisted port), `runtime/config/README.md`, `demo_stack.env.example` documents `PLAN_GATE_PORT`; `runtime/config/host_local.env` gitignored; legacy `runtime/.config/.env.example` points to m-coder templates.
- **Realistic on fresh host:** HTTP slice (Context Layer + Plan-Gate + validation sheet) **yes**; **full vLLM + GPU** remains **per-host** (`VLLM_BASE_MODEL`, `pip install vllm`).
- **Canonical model:** one **distributed** topology — workspace-side backend on **WSL or native Linux**; **Plan-Gate + vLLM on GPU**. **Both placements validated** with artifact-backed transcripts (§0).

### B6 — Compatibility Path Hardening (L5.9)
**Status:** **CLOSED** (Action 11, 2026-03-31) — tracker row **L5.9**; evidence **§6.17**.

- Path routing made explicit (`ask_path`, structured Plan-Gate / plugin logs).
- Trace chain established (`trace_id` end-to-end; `PLAN_GATE request` + `ROUTING_DECISION` where applicable).
- Fallback no longer silent (controlled v1→v0; contract failures do not silently fall back; plugin logs routing decisions).
- Explain vs planner distinction observable (`routing_mode`, `EXPLAIN_DEBUG` vs plan-only).

**Closure bar (numbered):** *Fallback rules documented and controlled; no silent path ambiguity remains.*

### B7 — Stage 3 controlled runtime loop — burn-in / acceptance
**Status:** **CLOSED** (2026-04-09) — **Offline pytest:** `docs/validation/artifacts/stage3_pytest_output*.txt`, `sample_ledger_trace.json`. **Native live smoke:** `stage3_live_smoke_output.txt`, `stage3_trace_reconstruction.txt`. **WSL + SSH tunnel → GPU:** `docs/validation/artifacts/stage3_b7_wsl_tunnel_verify_ask_path.txt` — `verify_ask_path.sh` **PASS**. Authority: **`docs/validation/STAGE3_BURN_IN_REPORT.md` §9**. **Out of scope (unchanged):** IDE → **`Stage3LoopController`** E2E — follow-on (**STAGE3_BURN_IN_AND_E2E_DEMO.md** §7). Keep **GPU/WSL commit alignment** via **`wsl_plugin_mvp_stack.sh check`**. Implementation **COMPLETE** per **§6.20**.

## L5-RET — RETRIEVAL POLICY BASELINE + VALIDATION TRACK

Objective:
Keep retrieval deterministic and baseline-protected while validating generalization.

L5-RET is now a **baseline preservation and regression-protection layer**, not an active improvement track.

### R1 — Baseline Policy Maintenance (LOCKED)
- PR-6 established deterministic owner-first retrieval baseline (`retrieval_policy.v5`)
- Baseline is frozen as canonical for true-positive debug grounding
- Any ranking logic change requires PR-6 audit re-validation on real repo before merge

### R2 — L5-RET-VALIDATION (feeds §B1 / L5.8-class threshold maturation)
- Query → expected owner / anchor mapping
- Golden suites:
  - Ask-understanding
  - Debug-root-cause
  - Plan/change-impact
  - Code-targeting
  - No-match / ambiguity
  - Adversarial noise
- Perturbation suite:
  - abbreviated symbol
  - package omitted
  - CamelCase split
  - error text only
  - active-file bias
  - typo-light wording
  - subsystem alias wording
  - why/where/fix phrasing shifts

### R3 — Metrics Gates
- top-1 owner accuracy
- top-3 anchor hit
- mean first relevant rank
- noise dominance
- code ratio
- weak-evidence precision
- no-match honesty precision
- drift detection

### Done Criteria
- PR-6 baseline preserved
- **Expanded** validation thresholds published and passing for suites beyond the locked harness (**L5.8 harness closure** = **complete** — **B2**)
- Regression detection active for owner/noise drift

## PR-6 Baseline Invariants (NON-NEGOTIABLE)
- Deterministic retrieval only (no embeddings, no semantic ranking)
- Workspace-local retrieval (WSL), not GPU
- Production code dominance over logs/tests/vendor
- Noise dominance must remain ~0.00
- Owner-file accuracy must not regress
- Any retrieval change must pass regression suite before merge

## L5-OBS — OBSERVABILITY TRACK

Objective:
Make system fully traceable and debuggable

### O1 — Request Propagation
- request_id across all services

### O2 — Endpoint Logging
- log:
  - /v1/export_evidence
  - /v1/ask
  - /v0/execute
  - vLLM calls

### O3 — Path Visibility
- surface ask_path in logs/UI

### O4 — Trace Reconstruction
- map request → evidence → plan → execution

### Done Criteria
- full trace available for any request
- no blind debugging required

## PRODUCTION CLOSURE GATES

System is considered production-grade only if:

[x] Retrieval produces AIOps-dominant evidence in latest automated batch — see `docs/validation/AIOPS_MVP_FINAL_REPORT_TEMPLATE.md` (8 PASS / 0 PARTIAL, STRONG metadata across all scenarios). Historical caveat note remains in `docs/validation/MVP_PRODUCTION_CLOSURE_NOTE.md`; no threshold gaming.
[x] Ask/Debug/Plan/Code scenarios pass
[x] Plugin reflects backend truth
[x] Observability fully implemented for MVP closure bar
[x] Both backend host modes validated against the same GPU-governed stack
[x] Compatibility path resolved
[x] Documentation aligned and canonical
[x] Action 14 final acceptance run PASS

---

## Tracking Principle

- **Milestones are governed by artifacts, not intention.**
  - A milestone is only meaningful when its contract/spec, implementation surface, and validation evidence exist together.
- **Status changes must be artifact-driven.**
  - Moving a milestone beyond `IN_PROGRESS` requires concrete, inspectable artifacts and evidence; “started coding” is not sufficient.
- **Dependencies and unblockers must be explicit.**
  - Each milestone must name what it depends on and what the next unblocker is, so progress can be sequenced and debugged.
- **Tracking is execution-governed.**
  - This tracker reflects what is actually built and validated, not aspirational design; doctrine remains defined in Layer-1.

---

## 2. Status Legend

### 2.1 Status markers

**Color coding** (in tables below): **green** = done (**LOCKED** or **COMPLETE** per §2.1) · **orange** = active (IN_PROGRESS / VALIDATING) · **gray** = not started (NOT_STARTED) · **red** = blocked (BLOCKED). Layer-level rollups use §2.1.1. Renders in GitHub and most Markdown viewers.


| Status          | Meaning                                                              |
| --------------- | -------------------------------------------------------------------- |
| **NOT_STARTED** | Milestone defined, no substantive work begun                         |
| **IN_PROGRESS** | Active engineering work underway                                     |
| **BLOCKED**     | Work paused due to dependency or risk                                |
| **VALIDATING**  | Implementation complete; in testing / verification / hardening phase |
| **COMPLETE**    | Implementation done; exit criteria met, but not doctrinally locked   |
| **LOCKED**      | Completed and ratified; further changes require explicit governance  |

### 2.1.1 Layer rollup status (canonical)

Use **only** these patterns when stating **layer-level** status (§1 Header, §3 Executive snapshot, root `README.md`, `docs/PROGRAM_STATE_SNAPSHOT.md`). Do not use legacy synonyms for whole layers (e.g. “complete / locked” for Layer-2 — use **LOCKED**).

| Layer | Canonical rollup | Meaning |
| ----- | ---------------- | ------- |
| **Layer-1** | **LOCKED** | Governance / doctrine ratified; changes require GREG. |
| **Layer-2** | **LOCKED** | ML compilation (Stages 1–8) finished and frozen under release verification. |
| **Layer-3** | **COMPLETE** (M3.0–M3.12 on `main`) | Core runtime + M3.12 narrow doc ingestion; **M3.13+** remain in §4.3.1. |
| **Layer-4** | **COMPLETE** (M4.1–M4.6 + Track-C on `main`) | Observation milestones and Track-C closure delivered. |
| **Layer-5** | **CLOSED** (MVP slice) | MVP vertical slice accepted; follow-on work (e.g. L5.7, §B1) stays in §4.5 and §0. |

**§4.x milestone rows** still use **COMPLETE**, **LOCKED**, **NOT_STARTED**, etc. from the table above (including **LOCKED** per stage or milestone). **CLOSED** is reserved for **program tracks** (B1–B7), **Action 14**, and the **Layer-5 MVP slice** rollup.

### 2.2 Priority markers


| Priority     | Meaning                       |
| ------------ | ----------------------------- |
| **CRITICAL** | Must be addressed immediately |
| **HIGH**     | Near-term priority            |
| **MEDIUM**   | Important but not urgent      |
| **LOW**      | Nice-to-have or long-term     |


Status and priority should be used together, e.g. `IN_PROGRESS (CRITICAL)`.

---

## 3. Executive Progress Snapshot


| Layer  | Scope                                  | Status                    | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------ | -------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ~~**L1**~~ | ~~Governance (Constitution)~~              | ~~**LOCKED**~~                | ~~Constitutional manifest, phase doctrine, dominance rules locked.~~                                                                                                                                                                                                                                                                                                                                                                                                      |
| ~~**L2**~~ | ~~ML Compilation (Stages 1–8)~~            | ~~**LOCKED**~~     | ~~Stage-6C cure validated; deterministic CONF rendering adopted; release verification PASS.~~                                                                                                                                                                                                                                                                                                                                                                             |
| ~~**L3**~~ | ~~Runtime Enforcement / Execution~~        | ~~**COMPLETE** (M3.0–M3.12 on `main`)~~ | ~~**M3.13–M3.18** follow-on. **Stage 3 controlled runtime loop** (burn-in) exists (**§6.20**); canonical **M3.x** table unchanged — loop work is tracked operationally, not as a new M3 ID.~~                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ~~**L4**~~ | ~~Observation / Drift Detection~~          | ~~**COMPLETE** (M4.1–M4.6 + Track-C on `main`)~~    | ~~Validated against real runtime ledger (.spool/ledger.db). C1–C3 demo-ready (2026-03-17).~~                                                                                                                                                                                                                                                                                                                                        |
| **L5** | Workspace Intelligence / Ask Grounding | **CLOSED (MVP slice)**            | Context Layer + **`POST /v1/ask`** on **`main`**; behavior baseline **§5** (`108aabb`). **L5.8 harness:** **COMPLETE** (**B2**). **§B7** / **§B5** **CLOSED**. **B1/B3/B4/B5/B7:** closed. **Action 14:** PASS. **Remaining:** L5.7, §B1/L5-RET follow-through — **§0**. |


---

## 4. Layer-by-Layer Milestone Tracker

### 4.1 Layer-1 — Governance

**Purpose**: Define constitutional judgment semantics (REF, CONF, DES, MIX, CODE, REACH), dominance hierarchy, irreversible boundary doctrine, collapse taxonomy, and governance protocols. Layer-1 defines *what* judgment means; lower layers implement without reinterpretation.

**Current status**: **LOCKED**


| ID   | Milestone                                    | Status | Dependencies | Exit criteria                                                                |
| ---- | -------------------------------------------- | ------ | ------------ | ---------------------------------------------------------------------------- |
| ~~L1.1~~ | ~~Constitutional Manifest v1.0 locked~~          | ~~LOCKED~~ | ~~—~~            | ~~Manifest ratified by GREG; phase semantics and dominance hierarchy explicit.~~ |
| ~~L1.2~~ | ~~Boundary Doctrine locked~~                     | ~~LOCKED~~ | ~~L1.1~~         | ~~Irreversible boundary definitions and phrase equality rules finalized.~~       |
| ~~L1.3~~ | ~~Collapse Taxonomy locked~~                     | ~~LOCKED~~ | ~~L1.1~~         | ~~Collapse types (REF_SOFTENING, CONF_TO_DES, etc.) defined and immutable.~~     |
| ~~L1.4~~ | ~~Golden Exemplars corpus locked~~               | ~~LOCKED~~ | ~~L1.1–L1.3~~    | ~~Governance exemplars set finalized; D.N.A validation protocol enforced.~~      |
| ~~L1.5~~ | ~~Governance escalation (GREG) protocol locked~~ | ~~LOCKED~~ | ~~L1.1–L1.4~~    | ~~Process for constitutional change defined; versioning rules in force.~~        |


**Dependencies**: None for new runtime work (Layer-1 is already locked).  
**Layer exit criteria**: All governance artifacts locked with version IDs; changes require formal GREG escalation and ratification.

---

### 4.2 Layer-2 — ML Compilation

**Purpose**: Compile constitutional judgment into a mutation-stable, deterministic, training-grade dataset and SFT model **without altering semantics**. Covers Stage-1–Stage-8: base mapping → variants → mutation harness → freeze → SFT.

**Current status**: **LOCKED** (see §2.1.1)

#### 4.2.1 Stages and Status


| Stage | Name                        | Status | Dependencies | Exit criteria                                                                 |
| ----- | --------------------------- | ------ | ------------ | ----------------------------------------------------------------------------- |
| ~~S1~~    | ~~Structural mapping~~          | ~~LOCKED~~ | ~~L1.*~~         | ~~Governance exemplars mapped to product surfaces; no new semantics introduced.~~ |
| ~~S2~~    | ~~Artifact extraction~~         | ~~LOCKED~~ | ~~S1~~           | ~~Instructions, context, reasoning, boundaries, postures extracted losslessly.~~  |
| ~~S3~~    | ~~Base stabilization~~          | ~~LOCKED~~ | ~~S2~~           | ~~Bases pass D.N.A; boundaries and phases stable; REF dominance preserved.~~      |
| ~~S4~~    | ~~Variant generation~~          | ~~LOCKED~~ | ~~S3~~           | ~~4 variants per base; same boundary, phase, posture; single mutation axis.~~     |
| ~~S5~~    | ~~Variant stability gate~~      | ~~LOCKED~~ | ~~S4~~           | ~~All variants pass POST-DRAFT D.N.A; no optimism drift or boundary aliasing.~~   |
| ~~S6~~    | ~~Mutation harness (6A/6B/6C)~~ | ~~LOCKED~~ | ~~S5~~           | ~~Stage-6C PASS; collapse vectors fully classified; freeze unblocked.~~           |
| ~~S7~~    | ~~Dataset freeze~~              | ~~LOCKED~~ | ~~S6~~           | ~~Freeze manifest locked; corpus hash, variant counts, phase distribution set.~~  |
| ~~S8~~    | ~~SFT training~~                | ~~LOCKED~~ | ~~S7~~           | ~~SFT / adapter training complete; invariance audit PASS; release approved.~~     |


#### 4.2.2 Layer-2 Closure Evidence (Summary)

- **Stage-6C cure validated**:
  - Deterministic CONF runtime rendering adopted in Stage-6C mutation harness.
  - CONF→DES drift eliminated under adversarial loops.
- **CONF drift results**:
  - `S0 = 80`  
  - `conf_to_des = 0`  
  - `s2_s3 = 0`
- **Release verification**:
  - `LAYER2_RELEASE_VERIFICATION.json = PASS`
  - Dataset freeze and SFT artifacts promoted under governance-approved criteria.

**Dependencies**: Layer-1 doctrine and exemplars.  
**Layer exit criteria**: All stages S1–S8 **LOCKED**; invariance audits PASS; adapters frozen and handed off to Layer-3.

---

### 4.3 Layer-3 — Runtime Enforcement / Execution

**Purpose**: Enforce constitutional judgment at runtime. REF and CONF are governed runtime phases; DES and CODE remain model-expressive but are orchestrated by the runtime. Layer-3 owns control flow, state transitions, authority and boundary enforcement, and completion criteria. The model proposes; the runtime decides.

**Current status**: **M3.0–M3.12 COMPLETE on main.** M3.13–M3.18 are follow-on milestones.  
**Priority**: **CRITICAL**

**Canonical Layer-3 numbering:** This document uses a single canonical model M3.0–M3.18. No alternate naming (e.g. M3.E0, M3X.*) is used in live roadmap tables.

#### 4.3.1 Layer-3 Milestones (canonical M3.0–M3.18)


| ID    | Milestone                                  | Status                       | Dependencies       | Deliverable / exit criteria summary                                                                                                                                                                                                                                       |
| ----- | ------------------------------------------ | ---------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ~~M3.0~~  | ~~Deterministic Runtime Emulator~~             | ~~COMPLETE~~                     | ~~L2.*~~               | ~~Plan-gate emulator + shadow runner + invariant tests. see §6.2.~~                                                                                                                                                                                                           |
| ~~M3.1~~  | ~~Deterministic Agent State Transition Table~~ | ~~COMPLETE~~                     | ~~Plan-Gate contract~~ | ~~State enum, terminal states, stop reasons, transition matrix. see §6.3.~~                                                                                                                                                                                                   |
| ~~M3.2~~  | ~~Repository Context Engine~~                  | ~~COMPLETE~~                     | ~~L2.*~~               | ~~Context bundles, versioned and reproducible. see §4.3.2 (M3.2).~~                                                                                                                                                                                                           |
| ~~M3.3~~  | ~~Agent Loop Orchestrator~~                    | ~~COMPLETE~~                     | ~~M3.2, M3.1~~         | ~~Loop controller, transition executor, no model-controlled recursion. see §6.4, §6.12.~~                                                                                                                                                                                     |
| ~~M3.4~~  | ~~Execution Sandbox~~                          | ~~COMPLETE~~                     | ~~M3.2–M3.3~~          | ~~Isolated executor, REFUSED/BLOCKED/EXECUTED, ledger. see §6.8.~~                                                                                                                                                                                                            |
| ~~M3.5~~  | ~~Plan-Gate Integration~~                      | ~~COMPLETE~~                     | ~~M3.2–M3.4~~          | ~~All paths through Plan-Gate; four postures; decisions ledgered. see §6.9.~~                                                                                                                                                                                                 |
| ~~M3.6~~  | ~~Internal Plan-Gate Decomposition~~           | ~~COMPLETE~~                     | ~~M3.5~~               | ~~AuthorityValidator, IrreversibilityDetector, JudgeGate. see §6.10.~~                                                                                                                                                                                                        |
| ~~M3.7~~  | ~~IDE Plugin Integration~~                     | ~~COMPLETE~~                     | ~~M3.5~~               | ~~Plugin → Plan-Gate → ledger; /v0/execute; 30 tests. see §6.7.~~                                                                                                                                                                                                             |
| ~~M3.8~~  | ~~Ledger Emission / Replay~~                   | ~~COMPLETE~~                     | ~~M3.5~~               | ~~Ledger completeness, replay, join contract. see §6.12.~~                                                                                                                                                                                                                    |
| ~~M3.9~~  | ~~Shadow Mode Validation~~                     | ~~COMPLETE~~                     | ~~M3.0–M3.8~~          | ~~Shadow runner, no boundary crossed; plan and ledger per run. see §6.12.~~                                                                                                                                                                                                   |
| ~~M3.10~~ | ~~Sandbox driver abstraction~~                 | ~~COMPLETE~~                     | ~~M3.4~~               | ~~Abstraction layer for sandbox execution drivers. see §6.13.~~                                                                                                                                                                                                               |
| ~~M3.11~~ | ~~Container sandbox runtime~~                  | ~~COMPLETE~~                     | ~~M3.10~~              | ~~Container-based sandbox implementing driver abstraction. see §6.14.~~                                                                                                                                                                                                       |
| ~~M3.12~~ | ~~Documentation ingestion~~                    | ~~**COMPLETE** (on `main`)~~ | ~~M3.0–M3.9~~          | ~~Narrow repo-aware manifest (`**ManifestBuilder**`, `**IngestionConfig**`), **`doc_selector`** (`**select_from_manifest**`), Ask handler integration in `**runtime/ask_service/handlers.py**` — see **`docs/runtime/M3_12_NARROW_CONTEXT_ENGINE_SPEC.md`**, verification **`§6.16.1`**, prior integration report `docs/reports/M3_12_INTEGRATION_VERIFICATION_REPORT.md`.~~ |
| M3.13 | Jira ingestion                             | NOT_STARTED                  | M3.0–M3.9          | Pipeline to ingest Jira data.                                                                                                                                                                                                                                             |
| M3.14 | PR ingestion                               | NOT_STARTED                  | M3.0–M3.9          | Pipeline to ingest PR data.                                                                                                                                                                                                                                               |
| M3.15 | Jira cleaning pipeline                     | NOT_STARTED                  | M3.13              | Clean and normalize Jira data.                                                                                                                                                                                                                                            |
| M3.16 | PR signal extraction                       | NOT_STARTED                  | M3.14              | Extract signals from PR data.                                                                                                                                                                                                                                             |
| ~~M3.17~~ | ~~Task schema~~                                | ~~**COMPLETE** (L5 branch)~~     | ~~M3.0–M3.9~~          | ~~Initial task-model slice + C1 trace alignment merged on `**feature/l5-context-layer-v1-ask-packaging`** (see **§6.16**). **M3.18** harness / broader evaluation scope still open.~~                                                                                         |
| M3.18 | Task evaluation harness                    | NOT_STARTED                  | M3.17              | Harness to evaluate tasks against governance and runtime contracts.                                                                                                                                                                                                       |


> Note: These Layer-3 milestones are **execution milestones** and do not redefine doctrine. They implement the runtime-governed agent architecture described in the Layer-3 specs.

> **Operational note (2026-04):** The **Stage 3 controlled runtime loop** (schema-driven task/proposal/tool contracts, deterministic state machine, loop controller, decision engine, executor integration, ledger linkage, fail-closed behavior; automated tests) is an **implementation surface** under `runtime/loop/`, `runtime/state/`, `runtime/tools/`, `runtime/adapters/`, `runtime/obs/`, and `runtime/tests/`. It does **not** introduce a new **M3.x** row; **M3.3** remains the historical Agent Loop Orchestrator milestone as previously completed. Status: **§6.20**, **§5**, **§1**.

> Follow-on relationship note: **M3.13–M3.16** remain valid downstream ingestion/enrichment milestones (M3.12 doc-manifest slice is **COMPLETE on `main`**). They are not substitutes for workspace-local code grounding and are not the immediate blocker for grounded Ask validity.

#### 4.3.2 Artifact-Driven Milestone Details

##### M3.0 — Deterministic Runtime Emulator

**Required Artifacts**

- `runtime/plan_gate_stub/plan_gate.py`
- `runtime/emulator/authority.py`
- `runtime/emulator/boundary.py`
- `runtime/emulator/ledger.py`
- `runtime/shadow_runner/run_demo.py`
- `runtime/tests/test_emulator_invariants.py`

**Exit Criteria**

- REF path emits refusal and never `safe_execute`.
- CONF path emits `bounded_allow` and never `defer`.
- Safe approval does not default to CODE; unresolved/emulator-safe phase handling documented.
- Shadow mode never emits `boundary_verdict=crossed`.
- Deterministic `plan_hash` and `boundary_phrase_hash` behavior verified for representative cases.
- Sample IDE event fixtures (commit_prod_change, merge_without_approval, safe_commit) execute end-to-end through the emulator with consistent Plan, Decision, and Ledger outputs.

**Evidence**

- All 6 required artifacts implemented and verified.
- Shadow runner demo executed successfully with all 3 scenarios passing:
  - `merge_without_approval` → REF → refuse (PASS)
  - `commit_prod_change` → CONF → bounded_allow (PASS)
  - `safe_commit` → DES → safe_execute (PASS)
- Invariant tests (28 tests) all passing:
  - `authority_fail never produces safe_execute` (PASS)
  - `boundary_present never produces defer` (PASS)
  - `shadow mode never emits boundary_verdict=crossed` (PASS)
- Deterministic hashing verified (same event → same plan_hash).
- Ledger emission with schema_version `ledger_row.v0.1` verified.

##### M3.1 — Deterministic Agent State Transition Table

**Required Artifacts**

- `docs/runtime/RUNTIME_STATE_TRANSITIONS.md`
- `runtime/state/schemas/state_enums.v0.1.json`
- `runtime/state/schemas/transition_matrix.v0.1.json`

**Exit Criteria**

- State enum finalized (including governed runtime phases and execution states).
- Terminal states (e.g., `Completed`, `Aborted`, `Refused`) finalized.
- Stop reasons finalized and documented (e.g., budget_exhausted, explicit_refusal, boundary_block).
- Invalid transitions explicitly rejected in the transition matrix.
- Runtime-only ownership of the state machine documented (model cannot add states or transitions).

**Evidence**

- none yet

##### M3.2 — Repository Context Engine

**Required Artifacts**

- Repository context architecture note (Layer-3 doc describing responsibilities and interfaces).
- Symbol search abstraction (API and contract for code symbol lookups).
- Dependency graph abstraction (API and contract for dependency relationships between files/modules).
- Context ranking policy (rules for how context snippets are ranked and selected).

**Exit Criteria**

- Deterministic retrieval path defined (given repo revision and request, same context bundle produced).
- Repository context bundle shape documented (fields, limits, provenance).
- At least one end-to-end retrieval example captured and documented.

**Evidence**

- **Artifacts**:
  - `docs/runtime/REPOSITORY_CONTEXT_ENGINE.md` — repository context engine responsibilities, contracts, determinism rules, and out-of-scope guarantees.
  - `runtime/context/contracts.py` — `ContextRequest`, `SelectedContextRef`, `ContextItem`, `ContextBundle` contracts.
  - `runtime/context/selectors.py` — deterministic direct/sibling/import/symbol selectors (selection-only, no content).
  - `runtime/context/engine.py` — `ContextEngine.build_context_bundle()` with selection vs materialization split, caps, and fail-closed behavior.
  - `runtime/tests/test_context_engine.py` — determinism, caps, missing-file, symbol-hint, and provenance tests.
- **Determinism & caps**:
  - Same `ContextRequest` + same repo contents at a given revision → same `ContextBundle.items` ordering and `selection_reason` values (ignoring `created_at_utc`).
  - `max_files` and `max_bytes` caps enforced with `limits.truncated` set when caps are hit.
- **Fail-closed behavior**:
  - Explicitly requested missing files cause `MissingExplicitFilesError` (no silent partial bundles).
  - Selected-but-missing files during materialization raise `ContextEngineError`.
- **Tests**:
  - pytest (`python3 -m pytest runtime/tests/test_context_engine.py -v`): 6 passed

##### M3.3 — Agent Loop Orchestrator

**Required Artifacts**

- Loop controller spec (document describing the agent loop sequence and responsibilities).
- Transition executor design (how state transitions invoke Model Worker, Sandbox, and Plan-Gate).
- Retry / iteration budget rules (limits on loop depth and retries).
- Stop condition rules (conditions under which the loop terminates or escalates).

**Exit Criteria**

- Happy-path loop defined (from initial plan to completed decision).
- Invalid loop patterns rejected (e.g., uncontrolled recursion, circular transitions).
- Deterministic replay path defined using Task State Store + ledger.

**Evidence**

- see §6.12

##### M3.4 — Execution Sandbox

**Required Artifacts**

- Sandbox contract doc (document describing isolation guarantees and interfaces).
- Runner interface (API for executing commands/tests/tools inside the sandbox).
- Artifact capture spec (what logs, outputs, and artifacts are persisted).
- Isolation / cleanup policy (how environments are cleaned/reset between runs).

**Exit Criteria**

- Isolated execution flow defined end-to-end.
- Test outputs and artifacts capturable in a reproducible way.
- Cleanup semantics documented for success and failure cases.

**Evidence**

- none yet

##### M3.5 — Plan-Gate Integration

**Required Artifacts**

- `runtime/plangate/plangate_decision.py` — PlanGateDecision (posture: refuse | defer | bounded_allow | safe_execute; authority_ok, boundary_detected, irreversible, reason).
- `runtime/plangate/plangate_service.py` — PlanGateService.evaluate(request) → PlanGateDecision (deterministic, rule-based; no LLM).
- LoopController integration: Plan-Gate evaluated before validated_to_sandbox; only safe_execute may reach sandbox.
- Ledger event types: plangate_refused, plangate_deferred, plangate_bounded_allow, plangate_safe_execute (request_id, plan_hash, decision_posture, reason).
- Demo extension: SAFE_EXECUTE → execution, REFUSE → refusal, DEFER → deferred, BOUNDED_ALLOW → bounded_allow; decision + outcome printed.
- `runtime/tests/test_plangate_integration.py` — refusal/defer/bounded_allow prevent sandbox; safe_execute allows; bounded_allow distinct from defer; decision persists.
- `docs/runtime/milestones/M3.3_PLAN_GATE_INTEGRATION.md` — milestone doc.

**Exit Criteria**

- Every sandbox execution requires Plan-Gate approval; no path may bypass Plan-Gate.
- All four postures (refuse, defer, bounded_allow, safe_execute) are first-class: refuse/defer/bounded_allow prevent sandbox; only safe_execute allows transition to sandbox; bounded_allow distinct from defer (stop_reason, plangate_bounded_allow).
- Plan-Gate decisions are ledgered (plangate_refused, plangate_deferred, plangate_bounded_allow, plangate_safe_execute); linkage via request_id.
- CLI demo shows five cases (SAFE_EXECUTE, REFUSE, REFUSED no gate, DEFER, BOUNDED_ALLOW); tests verify refusal, defer, and bounded_allow paths.

**Evidence**

- see §6.9

##### M3.6 — Internal Plan-Gate Decomposition

**Required Artifacts**

- AuthorityValidator, IrreversibilityDetector, JudgeGate; PlanGateService unchanged.

**Exit Criteria**

- Plan-Gate internally decomposed; external contract unchanged.

**Evidence**

- see §6.10

##### M3.7 — IDE Plugin Integration

**Required Artifacts**

- Plugin bridge doc (how IDE plugin interacts with runtime services).
- Intercepted action map (which IDE actions are governed and how they map to Plan-Gate calls).
- Local runtime invocation path (how the plugin locates and calls the runtime gate).

**Exit Criteria**

- Plugin request path defined (from IDE action to runtime Plan-Gate invocation).
- Blocked action UX defined (how refusals and conditional blocks are surfaced).
- Runtime response display path defined (how decisions and guidance are rendered in IDE).

**Evidence**

- none yet

##### M3.8 — Ledger Emission / Replay

**Required Artifacts**

- Transition-to-ledger mapping (how state transitions and decisions map to ledger_row.v0.1 fields).
- Append-only write policy (rules and mechanisms ensuring ledger immutability).
- Replay/join contract note (how to join plan, decision, and ledger rows for audits).

**Exit Criteria**

- Join key documented (e.g., `request_id`, `plan_hash`, `event_id`).
- Append-only semantics documented (no in-place mutation, only new rows).
- Deterministic sample ledger flow defined from a traced runtime session.

**Evidence**

- see §6.12

##### M3.9 — Shadow Mode Validation

**Required Artifacts**

- Shadow protocol note (how shadow mode runs in parallel with live behavior).
- Baseline scenario list (set of representative workflows used for shadow evaluation).
- Shadow replay harness plan (how to replay shadow runs for debugging and audits).

**Exit Criteria**

- No-crossed-boundary rule documented for shadow (shadow may plan but must not cross irreversible boundaries).
- REF shadow cases listed and validated (illegitimacy and missing authority behave as expected in shadow).
- Baseline capture path defined (how shadow data is stored and exposed to Layer-4).

**Evidence**

- see §6.12

**Dependencies**:  

- Upstream: Layer-1 and Layer-2 must remain locked; no changes to doctrine or compilation while runtime is being implemented.  
- Lateral: IDE plugin and CI systems for integration; infrastructure for sandboxing and ledger storage.

**Relationship between emulator and broader runtime architecture**:

- **M3.0** is the first executable governance-enforcement slice: deterministic runtime emulator for Plan-Gate + ledger, authority validation, boundary detection, decision contracts, ledger emission, shadow runner.
- **M3.1–M3.9** define the broader runtime-governed agent architecture (state machine, context engine, orchestrator, sandbox, Plan-Gate, IDE integration, ledger, shadow) that builds on top of the emulator.
- The emulator is not replaced; it remains the governance-aligned kernel for Layer-3.

**Layer exit criteria**:

- **M3.0–M3.12** are **COMPLETE** on main; tag `layer3-runtime-governed-v1`. **M3.13–M3.18** are follow-on milestones.
- No fail-open paths: when enforcement infrastructure is unavailable, default posture is REF/REFUSAL.
- Observation layer (L4) has sufficient ledger data to begin drift tracking.

---

### 4.4 Layer-4 — Observation / Drift Detection

**Purpose**: Observe and validate that runtime behavior continues to match doctrine. Layer-4 detects drift, boundary relocation, and collapse vectors in production, providing structured evidence to governance (GREG). It does not author doctrine or enforce directly.

**Current status**: **M4.1–M4.6 COMPLETE on main** (merged 2026-03-15). **Track-C (C1–C3) COMPLETE** (2026-03-17): runtime observation query layer validated and demo-ready.  
**Priority note:** Layer-3 runtime MVP is **complete on main**; Track-C closure is **done** — ongoing work is maintenance and Layer-5 integration touchpoints, not “unblocking L4.”

**Track-C (Runtime Observation Query Layer)**  

- **C1** Execution Trace Builder: deterministic trace reconstruction by request_id / canonical_hash (latest request group).  
- **C2** Execution Explanation Builder: deterministic explanation from trace.  
- **C3** Runtime Query Surface: CLI for summary, request trace/explanation, canonical_hash trace/explanation.  
- Validated against real runtime ledger (`.spool/ledger.db`; request_id `demo-runtime`; canonical_hash `4b6a08e37bfed4a502029c1b8b1b9500122ff86cc45b15339ac1ff29d6218837`).  
- Closure: `docs/runtime/TRACK_C_FINAL_CLOSURE.md`.

#### 4.4.1 Milestones

*M4.1–M4.6 merged to main 2026-03-15. See `docs/reports/M4X_MAIN_MERGE_COMPLETION.md`. Track-C final closure 2026-03-17.*


| ID   | Milestone                   | Status              | Dependencies | Deliverable                                                              | Exit criteria                                                                               |
| ---- | --------------------------- | ------------------- | ------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| ~~M4.1~~ | ~~Ledger Ingestion~~            | ~~**COMPLETE** (main)~~ | ~~M3.8~~         | ~~Service/pipeline ingesting runtime ledger rows into observation storage.~~ | ~~All ledger_row.v0.1 events of interest are reliably ingested and queryable.~~                 |
| ~~M4.2~~ | ~~Drift Baseline~~              | ~~**COMPLETE** (main)~~ | ~~M4.1~~         | ~~Baseline distributions of phases, boundaries, and collapse vectors.~~      | ~~Baselines established for key metrics; thresholds approved by governance stakeholders.~~      |
| ~~M4.3~~ | ~~Collapse Vector Tracking~~    | ~~**COMPLETE** (main)~~ | ~~M4.1–M4.2~~    | ~~Online classification of collapse vectors in runtime behavior.~~           | ~~All detected collapses are classified; unclassified collapses trigger alerts.~~               |
| ~~M4.4~~ | ~~Ledger Reconciliation~~       | ~~**COMPLETE** (main)~~ | ~~M4.1~~         | ~~Tools to reconcile pre-SFT, post-SFT, and runtime ledgers.~~               | ~~Ability to trace changes in behavior across releases and runtime environments.~~              |
| ~~M4.5~~ | ~~GREG Governance Escalation~~  | ~~**COMPLETE** (main)~~ | ~~M4.1–M4.4~~    | ~~Automated pathways for generating evidence packages and triggering GREG.~~ | ~~Drift above threshold results in deterministic escalation with complete evidence bundles.~~   |
| ~~M4.6~~ | ~~Runtime Performance Metrics~~ | ~~**COMPLETE** (main)~~ | ~~M4.1–M4.4~~    | ~~Metrics and dashboards for runtime performance and invariance.~~           | ~~Key runtime and invariance metrics available to stakeholders; alerts wired into operations.~~ |


**Dependencies**: Layer-3 ledger emission and runtime invariants; Layer-1 doctrine for drift definitions; Layer-2 for pre-SFT invariance baselines.  
**Layer exit criteria**: Drift detection and escalation loop closed: anomalies go from detection → evidence → GREG escalation in a repeatable, auditable way.

---

### LAYER 5 — CONTEXT LAYER & ASK SYSTEM

**Previous status (superseded 2026-04):** INTEGRATION COMPLETE, QUALITY GATES PENDING. **Current:** MVP **behavior verification + Ask v1 quality** closed on `main` with promoted baseline (**`MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5**). **Remaining Layer-5 work:** L5.7 (not started), §B1/L5-RET follow-through, optional charters — see **§0**.

#### Completed
- L5.1 → L5.6: Indexing, retrieval, evidence schema, Ask path integration
- **L5.8 — harness + metrics baseline (closure gate):** **COMPLETE** — see **B2** checklist (artifacts under `runtime/layer5/audit/` l58_* harness); **§4.5** milestone row aligned.
- **L5.9:** Compatibility path hardening — **Action 11 CLOSED** (2026-03-31); see **§6.17** and runbook `docs/guides/ACTION_11_LINUX_TEST_RUNBOOK.md`.

#### In Progress / Not Started
- L5.7: Dirty buffer overlay
- **L5.8 follow-through (not a duplicate “NOT_STARTED” milestone):** expanded validation / generalization / SLO maturation — **§B1**, **L5-RET-VALIDATION**, **§1.4 Track RET** (same program as Stage 2 reliability; harness closure remains **closed**).

#### New Required Tracks
- L5-RET: Retrieval Baseline Preservation + Validation Generalization
- L5-OBS: Observability & Tracing — **Action #5 CLOSED** (**§6.19**); non-HTTP ops follow-through
- L5-UX: Plugin Truthfulness Alignment — **Action 4 CLOSED** (**§6.18**); residual checklist items remain in **§B3**

**Purpose**: Establish a workspace intelligence layer in WSL that performs workspace-local retrieval and deterministic evidence assembly before Plan-Gate evaluation. Layer-5 defines the structured evidence-bundle contract into Plan-Gate, reduces dependence on remote repo-path assumptions (`repo_root`, `ASK_DEFAULT_REPO_ROOT`) to compatibility-only behavior, and does not redesign Layer-1 governance semantics or Layer-3 execution authority.

**Priority**: **CRITICAL**


| ID   | Milestone                                  | Status      | Dependencies    | Deliverable / exit criteria summary                                                                                                                                                                                                               |
| ---- | ------------------------------------------ | ----------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ~~L5.0~~ | ~~Grounded Ask Spike (Wave-1 / A1)~~           | ~~COMPLETE~~    | ~~—~~               | ~~Provisional workspace-local retrieval spike; grounded evidence output proven (`archive/workspace_intelligence/spikes/`). Not final L5.2/L5.3 architecture.~~                                                                                                |
| ~~L5.1~~ | ~~Workspace Resolver baseline (Wave-1 / A2)~~  | ~~COMPLETE~~    | ~~M3.7~~            | ~~Resolver + local API skeleton (`runtime/layer5/`). Canonical workspace identity + path normalization contract.~~                                                                                                                                    |
| ~~L5.2~~ | ~~Deterministic Index MVP (Wave-2 / A4)~~      | ~~COMPLETE~~    | ~~L5.1, M3.2~~      | ~~**A4:** deterministic file-level index (`runtime/layer5/index/`), `canonical_json` lifecycle, full rebuild; excludes graph/symbol/AST.~~                                                                                                            |
| ~~L5.3~~ | ~~Retrieval Foundation (Wave-2 / A5)~~         | ~~COMPLETE~~    | ~~L5.2~~            | ~~**A5:** lexical deterministic retrieval (`runtime/layer5/retrieval/`), `(-score, relative_path)` ranking, breakdown; not graph/symbol lanes.~~                                                                                                      |
| ~~L5.4~~ | ~~Snippet + Evidence Builder (Wave-2 / A6)~~   | ~~COMPLETE~~    | ~~L5.3~~            | ~~**A6:** bounded snippets + bundle assembly (`runtime/layer5/evidence/`). Evidence contract freeze — see **§4.5.1a** below.~~                                                                                                                        |
| ~~L5.5~~ | ~~Plugin Evidence Bridge (A7)~~                | ~~COMPLETE~~    | ~~L5.1–L5.4, M3.7~~ | ~~Evidence-first: **WSL HTTP** `POST /v1/export_evidence` (wheel) or CLI / dev script → `ask_request.v1.0` → `POST /v1/ask`; controlled v0 fallback only when Context Layer **unreachable**; UI treats `evidence_bundle` as primary. See **§6.15**.~~ |
| ~~L5.6~~ | ~~Plan-Gate Evidence Ingestion (A8)~~          | ~~COMPLETE~~    | ~~L5.4–L5.5, M3.5~~ | ~~Plan-Gate `POST /v1/ask` validates/consumes `layer5.evidence_bundle.v1`; reasoning from bundle only (no repo ContextEngine on v1 path). See **§6.15**.~~                                                                                            |
| L5.7 | Dirty Buffer / Live File Overlay           | NOT_STARTED | L5.5            | Retrieval and snippet extraction can include unsaved editor buffers via deterministic overlay rules without mutating on-disk index truth.                                                                                                         |
| ~~L5.8~~ | ~~Grounded Ask Validation + Metrics~~          | ~~**COMPLETE** (harness + closure gate)~~ | ~~L5.6, L4~~        | ~~**Delivered:** deterministic L5.8 harness scaffolding, golden fixtures, perturbation snapshots, PR-6 protected subset enforcement, CI wiring, closure promotion — **B2**; **§6.19a**. **Ongoing (tracked as §B1 / L5-RET, not “L5.8 NOT_STARTED”):** expanded suites, drift detection, latency SLO publication for production-scale bars. **Note:** L5.7 (Dirty Buffer) is not a blocking dependency for the closed harness scope; dirty-buffer support remains a correctness extension.~~ |
| ~~L5.9~~ | ~~Compatibility Path Deprecation / Hardening~~ | ~~**COMPLETE** (Action 11, 2026-03-31)~~ | ~~L5.6–L5.8~~       | ~~**Action 11 closure:** explicit path routing + `trace_id` / `routing_mode`; structured `ROUTING_DECISION` (plugin) + Plan-Gate request logging; controlled v1→v0 fallback (no silent ambiguity); explain vs planner observable. Runbook: `docs/guides/ACTION_11_LINUX_TEST_RUNBOOK.md`; capture script: `scripts/action11_one_shot_capture.sh`. Evidence folder (example): `Action-11-artifacts-20260331-103853`. Broader “deprecation program” / telemetry gates may continue as separate follow-ons.~~                                                                |


#### 4.5.1a L5.4 — Evidence contract (freeze)

- **Schema:** `layer5.evidence_bundle.v1` (`runtime/layer5/evidence/evidence_bundle.v1.schema.json`, `evidence_bundle.v1.md`).
- **Status:** **FROZEN** (Wave-2.5 freeze-fix).
- **Golden fixture + hash:** `runtime/layer5/evidence/golden/` (`evidence_bundle.v1.masked.json`, `evidence_bundle.v1.fingerprint.sha256`); CI tests assert fingerprint stability.
- **Enforcement:** strict JSON Schema (`additionalProperties: false`), frozen `selection_reason` enum, normative byte-offset semantics, `IdentityMismatchError` policy + `require_identity_match` flag (`runtime/layer5/evidence/identity_policy.py`).

**Wave-1 closure (A1/A2/A3):** Grounded Ask proven via L5.0 spike; resolver/API skeleton established (L5.1; test env follow-up **Caveat-F1**); baseline Ask validation harness in `runtime/ask_validation/` (Wave-1 gate; latency path vs spine **Caveat-F2**). **L5.8** harness + closure gate is **COMPLETE** (**B2**); **ongoing** metrics/SLO expansion is **§B1 / L5-RET** follow-through — see **§4.5** milestone row (no longer “NOT_STARTED” for the harness).

#### 4.5.1 Ask validity criteria (grounded Ask contract)

- For repo-grounded Ask queries, at least one relevant file must be selected, **or** an explicit no-match outcome must be returned with deterministic justification.
- Evidence bundle must include: file paths, snippet spans/selectors, and per-selection reason fields.
- Empty `context_bundle.files` is invalid for grounded Ask unless accompanied by explicit no-match or scope-invalid justification.
- Plan-Gate and downstream reasoning surfaces must consume the provided bundle as evidence input, not infer hidden repository state.

#### 4.5.2 vLLM dependency boundary

- Retrieval, indexing, workspace resolution, and evidence bundling are deterministic infrastructure concerns and do not require vLLM availability.
- vLLM remains applicable for deeper reasoning/explanation synthesis over supplied evidence bundles.

#### 4.5.3 Layer-5 MVP contract-tightening checklist

- **Wave-2 shipped (A4–A6):** file-level index + lexical retrieval + evidence v1 frozen; items below that assumed broader scope (symbol/graph/watchers) remain **forward** tightening for later waves unless rescoped.
- L5.2 must lock index granularity decisions explicitly (file-level baseline, symbol-level coverage, AST-assisted parsing scope, and incremental watcher/update behavior).
- L5.3 must define retrieval lanes and ranking behavior explicitly (lexical/path lane, symbol lane, graph-expansion lane, recency/open-file bias, deterministic merge/rank output).
- **L5.8 (closed harness):** baseline harness and thresholds delivered; **ongoing:** publish and enforce **expanded** latency/SLA targets for retrieval and end-to-end Ask under **§B1** as suites grow.
- L5.4/L5.6 must lock evidence bundle contract versioning and determinism fields (schema version, bundle hash, revision/provenance linkage, replay/debug reproducibility).
- L5.9 must operationalize migration from compatibility path via feature flags, fallback semantics, and telemetry-based comparison gates.

**Dependencies**:  

- Upstream: existing Layer-3 runtime and plugin bridge remain stable.  
- New: Workspace Intelligence Layer contract and evidence bundle schema.
- Compatibility note: GPU-side direct repo access behavior (`repo_root`, `ASK_DEFAULT_REPO_ROOT`) is compatibility-only during migration, not the primary architecture.

**Layer exit criteria**:  

- Workspace-local retrieval produces deterministic grounded evidence bundles.  
- Ask path consumes evidence bundles and returns internally consistent files/selectors/plan surfaces.

---

## Backlog / Deferred (Layer-5)

**Caveat-F1 — Resolver test environment robustness**  
Problem: resolver tests assume `/workspace/...` in places; fails on typical local roots. Timing: late Wave-2 or early Wave-3 unless A4/A5 blocked sooner. Goal: pass on Cursor/CI `/workspace/...` and normal local checkouts. Trigger: `/workspace` assumptions block Wave-2. Success: stable green resolver tests in both layouts.

**Caveat-F2 — A3 latency path upgrade**  
Problem: A3 harness latency is truthful but not yet tied to final Wave-2 index/retrieval/evidence spine. Timing: after A4/A5/A6 deliver enough of that spine. Goal: re-instrument A3 on real index + retrieval + snippet/evidence paths. Trigger: harness latency misleading vs production path. Success: A3 reflects actual Layer-5 execution path latency.

---

## 5. Current Sprint / Current Focus

- **Previous Q1 sprint (complete):** locked baseline reproducibility, authority expansion hardening, Debug Usefulness v1.1, Ask v1 evidence quality parity, promoted **§5** baseline, and closure narrative — all landed; scenario suite green on WSL where verified.
- **Current objective (post-closure):** **Operational lock** on **`motadata_behavior_verify.py`** + **§5** baseline discipline — see **`docs/validation/POST_CLOSURE_MAINTENANCE.md`** and **§0** above.
- **Completed sprint work (reference):**
  - **Baseline lock:** anchored authority-gated baseline achieved (`ask_anchor_owner_top1` strict pass + scenario suite stable), broad ask improved (`ask_broad_correlation` generic-infra ratio reduced).
  - **Debug usefulness v1.1:** selected-file-grounded `EXPLAIN_DEBUG` guardrails + insufficiency checks landed and passing.
  - **Operational reproducibility:** authority index builder supports smart auto full/incremental refresh with dynamic progress and is integrated into WSL run flow.
  - **Authority Expansion Hardening v1:** Stage A suppresses noise-class files (including `db-files/*` and `test-plugin-metrics/*`) for code-oriented tasks; WSL candidate diff confirms `ask_api_request_routing_owner` no longer includes `db-files/report-templates/js/highcharts.js` in context bundle and distractor count dropped (`1 -> 0`).
  - **Ask v1 evidence quality parity (2026-04-17):** Plan-Gate **`POST /v1/ask`** supplies grounding + authority into **`assess_evidence_quality`** (m-coder `108aabb`); WSL verification green with **`ask_servicenow_sync_owner`** at **`evidence_quality: STRONG`** and full scenario suite **`all_pass=true`**.
  - **Promoted behavior baseline:** formal record under **`docs/validation/MOTADATA_BASELINE_ARTIFACT_POLICY.md` §5** — artifact `runtime/.run/motadata_behavior_validation.CANDIDATE.SERVICENOW_QUALITY_V3.motadata.json`, commit `108aabb098017b8c551629c745d71f63acf7`.
  - **Closure narrative:** **`docs/validation/MOTADATA_BEHAVIOR_VERIFICATION_CLOSURE.md`** + team pointers on `main`.
- **Next execution order (maintenance):**
  1. Keep retrieval baseline regression-proof via scenario runs; cite **§5** artifact + SHA for regression reports.
  2. Compare future candidates against the **§5** promotion (and optionally against `AUTHORITY_HARDENING_V1` when both artifacts are available locally).
  3. Optional tuning only with explicit scope — preserve **§5** invariants (**§1.4** guardrails).
- **Current blockers:**
  - No blocker on baseline reproducibility or strict anchored retrieval gates.
  - Residual product tuning (broader exploratory asks) is **non-blocking** vs the promoted **§5** bar.
- **Immediate next action:**
  - **Ongoing:** **`docs/validation/POST_CLOSURE_MAINTENANCE.md`**. **Chartered follow-ons:** **§1.4** (debug depth **CHARTER-TBD**, §B1/L5-RET) — not ad-hoc fusion work.

### 5.1 Current Focus — Controlled Runtime Loop (Hybrid Model)

Implementation exists; **current work** is **burn-in / validation / integration**, not autonomous coding expansion.  
The bounded, schema-driven reasoning loop remains **runtime-owned** (see **§5.2** contracts).

### 5.2 Hybrid Loop Architecture (Stage 3 — implementation)

**Core principles**

- Runtime-controlled loop (state machine owns transitions and termination).
- Model emits **structured proposals only** (no direct orchestration authority).
- Bounded retries and deterministic stop policies.
- No uncontrolled recursion.
- Full observability / ledgering per transition.

**Core contracts**

- `TaskEnvelope.v1`: runtime-owned task context + hard constraints.
- `ModelProposal.v1`: model-proposed next step in validated schema.
- `ToolExecutionRequest.v1`: bounded runtime-issued tool request.
- `ToolExecutionResult.v1`: normalized tool result for the loop.
- `LoopDecision.v1`: runtime decision (continue/revise/stop/refuse).
- `FinalResponse.v1`: grounded user-facing outcome.

**Loop states**

- `CONTEXT_READY`
- `PLAN_GATED`
- `MODEL_PROPOSED`
- `PROPOSAL_VALIDATED`
- `TOOL_EXECUTING`
- `TOOL_RESULT_READY`
- `MODEL_REVISED`
- terminal: `COMPLETED` / `REFUSED` / `BLOCKED` / `FAILED` / `INSUFFICIENT`

**Loop policy**

| Task    | Attempts | Tool use  | Output           |
| ------- | -------- | --------- | ---------------- |
| ASK     | 1        | optional  | grounded answer  |
| DEBUG   | 2–3      | read-only | hypothesis       |
| PLAN    | 1–2      | read-only | steps            |
| CODE    | 2–3      | bounded   | diff             |
| EXECUTE | 1–2      | sandboxed | truthful outcome |

### 5.3 Do Not Do (discipline guardrails)

- Do not add Neo4j in this phase.
- Do not add graph DB in this phase.
- Do not introduce uncontrolled agent loops.
- Do not allow LLM-driven orchestration to replace runtime control.
- Do not enable premature coding autonomy.

**Architecture alignment remains mandatory**: WSL workspace is source-of-truth, Context Layer stays near workspace, GPU hosts Plan-Gate + vLLM, and plugin remains a thin client.

---

## 6. Completed Evidence Log

This section records **evidence of completed milestones**. Entries should be **append-only** and reference concrete artifacts (files, logs, reports).

### 6.1 Layer-2 Closure

- **Milestone**: Layer-2 ML Compilation **LOCKED** (§2.1.1).  
- **Evidence**:
  - Stage-6C agent-loop mutation harness PASS with deterministic CONF runtime rendering.  
  - `conf_drift_result`:
    - `S0 = 80`
    - `conf_to_des = 0`
    - `s2_s3 = 0`
  - Deterministic CONF runtime rendering adopted as part of governance-aligned runtime enforcement.
  - `LAYER2_RELEASE_VERIFICATION.json = PASS` (location documented in Layer-2 artifacts).

### 6.2 M3.0 — Deterministic Runtime Emulator

- **Milestone**: M3.0 Deterministic Runtime Emulator — COMPLETE (2026-03-09)
- **Artifacts** (6/6):
  - `runtime/plan_gate_stub/plan_gate.py` — PlanGate class with `evaluate_plan()` method
  - `runtime/emulator/authority.py` — AuthorityChecker with deterministic rule-based validation
  - `runtime/emulator/boundary.py` — BoundaryDetector with irreversible boundary detection
  - `runtime/emulator/ledger.py` — LedgerEmitter producing `ledger_row.v0.1` records
  - `runtime/shadow_runner/run_demo.py` — Shadow runner with 3 demo scenarios
  - `runtime/tests/test_emulator_invariants.py` — 28 invariant tests
- **Evidence**:
  - Shadow runner demo (`python3 -m runtime.shadow_runner.run_demo`): ALL PASS
    - `merge_without_approval` → Phase: REF, Decision: REFUSAL, Posture: refuse
    - `commit_prod_change` → Phase: CONF, Decision: BOUNDED_ALLOW, Posture: bounded_allow
    - `safe_commit` → Phase: DES, Decision: SAFE_EXECUTE, Posture: safe_execute
  - Invariant validation: ALL PASS
    - `authority_fail never produces safe_execute`
    - `boundary_present never produces defer`
    - `shadow mode never emits boundary_verdict=crossed`
  - pytest (`python3 -m pytest runtime/tests/test_emulator_invariants.py`): 28 passed
  - Deterministic hashing verified: same event produces identical `plan_hash` and `boundary_phrase_hash`
  - Ledger rows emitted with `schema_version: ledger_row.v0.1`

### 6.3 M3.1 — Deterministic Agent State Transition Table

- **Milestone**: M3.1 Deterministic Agent State Transition Table — COMPLETE (2026-03-10)
- **Artifacts** (3/3):
  - `docs/runtime/RUNTIME_STATE_TRANSITIONS.md` — deterministic runtime state transition contract (runtime-owned control, terminal states, stop reasons, plan-gate checkpoints, decision-boundary ledger semantics)
  - `runtime/state/schemas/state_enums.v0.1.json` — state + stop_reason enums (13 states including `PLAN_EVALUATED`)
  - `runtime/state/schemas/transition_matrix.v0.1.json` — allowed transitions only, terminal non-escaping states, `transition_id`, plan-gate checkpoints, decision-boundary ledger semantics (anti-double-ledger guidance)
- **Evidence**:
  - Terminal states documented as non-escaping; invalid transitions defined as reject-by-default
  - Ledger semantics are **decision-boundary based** with explicit anti-double-ledger rule for simple REF refusal flows
  - DES explicitly constrained to **model-proposal semantics only**; execution remains runtime-owned

### 6.4 M3.3 — Agent Loop Orchestrator (Scaffold)

- **Milestone**: M3.3 Agent Loop Orchestrator — COMPLETE (2026-03-13); **final integration via §6.12.**
- **Artifacts (scaffold)**:
  - `runtime/state/store.py` — Task state store (in-memory + optional JSON persistence)
  - `runtime/state/transitions.py` — transition validator enforcing `transition_matrix.v0.1.json`
  - `runtime/orchestrator/loop_controller.py` — deterministic transition executor (load → validate → apply → persist → journal), wired to `ContextEngine` at `governance_to_context` (CONTEXT_FETCHED)
  - `runtime/tests/test_transition_executor.py` — transition executor tests (valid transitions succeed; invalid transitions refused; terminal non-escaping enforced; iteration/repetition/no-op guards; context wiring at CONTEXT_FETCHED)
- **Evidence**:
  - Store load refreshes in-memory view when reading from disk (prevents subtle divergence in long-lived processes)
  - Loop safety guards enforced:
    - retry-path iteration cap (currently applies to `review_to_proposal` only)
    - excessive consecutive repetition of the same `transition_id` is rejected
    - no-op transitions are rejected unless explicitly defined in the matrix
    - guard blocks return explicit `stop_reason` (e.g., `iteration_limit`) without forcing terminal state yet (future evolution: explicit terminal transition like `REVIEW_DECIDED -> BLOCKED`)
  - Context wiring at `CONTEXT_FETCHED`:
    - `LoopController` now constructs a `ContextRequest` from `TaskState.metadata` and calls `ContextEngine.build_context_bundle()` on the `governance_to_context` path
    - Minimal context metadata persisted in `TaskState.metadata['context_bundle']` (bundle_id, revision, paths, truncated)
    - Engine errors (`MissingExplicitFilesError` / `ContextEngineError`) are fail-closed: transition is refused with `stop_reason=\"validation_failed\"` and state remains `GOVERNANCE_CLASSIFIED`
  - pytest (`python3 -m pytest runtime/tests/test_transition_executor.py -v`): 23 passed
  - **Final integration evidence**: see §6.12 (Layer-3 governed runtime merge; 346 runtime tests; tag `layer3-runtime-governed-v1`).

### 6.7 M3.7 — IDE Plugin Integration (RuntimeBridge + Governed Actions)

- **Action 7 (Execute trust) — COMPLETE (live HTTP product path):** Execute trust validation is complete for **`POST /v0/execute`** via Plan-Gate (including **`EXECUTED_FAILED` vs `BLOCKED`** and **`plan_gate_*` server-rejected by default** on live HTTP). **Caveat:** Execute trust is complete on the live HTTP product path. Remaining direct-handler behavior and broader auth/binding topics are follow-through items, not unfinished Action 7 product logic.
- **Milestone**: M3.7 IDE Plugin Integration — COMPLETE (2026-03-12); **MVP scope: commit interception, ask flow, /v0/execute with decision ledgering and production governance.**
- **Artifacts** (11+):
  - **Plugin RuntimeBridge abstraction**:
    - `jetbrains-plugin/.../bridge/RuntimeBridge.kt` — Single integration point for all runtime calls.
    - `jetbrains-plugin/.../bridge/RuntimeOutcome.kt` — 7 distinct outcomes. No collapsing.
    - `jetbrains-plugin/.../bridge/RuntimeRequest.kt` — Unified request envelope.
    - `jetbrains-plugin/.../bridge/RuntimeResponse.kt` — Response contract with outcome, ui, reason, wasExecuted, ledgerRowId.
  - **Governed actions**:
    - `jetbrains-plugin/.../vcs/MotadataCheckinHandler.kt` — Shadow/enforcing; fail-closed.
    - `jetbrains-plugin/.../ask/AskMotadataAiAction.kt` — PLAN ONLY semantics.
    - `jetbrains-plugin/.../actions/SubmitToRuntimeAction.kt` — Explicit execution action.
  - **Runtime execute endpoint**:
    - `runtime/execute_service/handlers.py` — `/v0/execute`: Plan-Gate → ledger decision → sandbox (if safe_execute) → ledger outcome. Governance from PlanGateService only; `plan_gate_*` fields only when `MOTADATA_EXECUTE_ALLOW_PLAN_GATE_OVERRIDES` test mode is set (live HTTP rejects them by default); command parsed with shlex.split(); decision_ledger_row_id and ledger_row_id in response.
    - `runtime/ide/schemas/execute_request.v0.1.schema.json` — Optional ledger_path, plan_gate_* (test/demo).
    - `runtime/ide/schemas/execute_response.v0.1.schema.json` — decision_ledger_row_id, ledger_row_id.
  - **Tests**: `runtime/tests/test_execute_service.py` — 30 tests (validation, explicit flags, decision ledgering, shlex parsing).
  - **Documentation**: `docs/runtime/milestones/M3.4_IDE_PLUGIN_INTEGRATION.md`, `docs/runtime/JETBRAINS_PLUGIN_RUNTIME_BRIDGE.md`.
- **Evidence**:
  - **Plan-Gate decision ledgering in /v0/execute:** When ledger_path (request or MOTADATA_EXECUTE_LEDGER_PATH) is set, Plan-Gate decision is persisted (plangate_refused, plangate_deferred, plangate_bounded_allow, plangate_safe_execute) before sandbox or return. Response includes decision_ledger_row_id; ledger_row_id when executed. Decision and execution evidence are separate.
  - **Production governance:** No command-string keyword heuristics. Posture from PlanGateService.evaluate(request) only; `plan_gate_*` overrides only when explicit test env is enabled (rejected by default on live HTTP).
  - **Command parsing:** shlex.split() for quoted args; invalid/empty command rejected; shell=False downstream.
  - **RuntimeBridge:** Single integration point; 7 distinct outcomes; fail-closed; 3 governed actions (commit, ask, submit to runtime).
  - **Tests:** pytest `runtime/tests/test_execute_service.py` — 30 passed (decision ledgering, explicit flags, shlex, no keyword path).
- **Scope (MVP):** Commit interception, ask flow, explicit runtime execution, fail-closed bridge. Not in MVP: push interception, full IDE coverage, plugin E2E in running IDE.

### 6.8 M3.4 — Execution Sandbox (CODE Phase)

- **Milestone**: M3.4 Execution Sandbox — COMPLETE (2026-03-12); **closed for MVP; demo closure and local evidence complete.**
- **Artifacts** (6/6):
  - `runtime/sandbox/sandbox_runner.py` — SandboxRunner with subprocess execution, timeout enforcement, artifact capture
  - `runtime/sandbox/sandbox_policy.py` — SandboxPolicy with command allowlist, time limits, env filtering
  - `runtime/sandbox/sandbox_result.py` — SandboxResult + **GovernedExecutionResult** (unified REFUSED/BLOCKED/EXECUTED contract)
  - `runtime/sandbox/sandbox_errors.py` — SandboxPolicyViolation, SandboxTimeout, SandboxExecutionError
  - `runtime/sandbox/sandbox_executor.py` — Returns GovernedExecutionResult; BLOCKED/EXECUTED with optional ledger_store
  - `runtime/sandbox/sandbox_ledger.py` — SandboxLedgerEmitter (in-memory)
  - `runtime/sandbox/sandbox_ledger_store.py` — **SandboxLedgerStore** (SQLite WAL, append-only) for all three outcomes
  - `runtime/sandbox/demo_governed_execution.py` — **Canonical CLI/test-harness demo** (EXECUTED, BLOCKED, REFUSED)
  - `runtime/tests/test_sandbox_runner.py`, `runtime/tests/test_sandbox_demo_e2e.py`, `runtime/tests/test_sandbox_ledger_store.py`
  - `docs/demo/M3.2_PROOF_PACK.md` — Proof pack for MVP walkthrough
- **Evidence**:
  - **Three canonical outcomes:** REFUSED (runtime denies before sandbox; refusal ledger row persisted), BLOCKED (policy blocks; blocked row persisted), EXECUTED (command runs; execution row persisted).
  - Refusal events produce ledger rows (LoopController + ledger_store when validated_to_sandbox refused).
  - Unified contract: GovernedExecutionResult with outcome_type, request_id, plan_hash, sandbox_id, ledger_row_id, refusal_reason, blocked_reason, commands_executed/blocked, artifacts, duration_ms, exit_code, stdout_summary, stderr_summary.
  - Local ledger: SQLite append-only; get_by_request_id, get_by_ledger_row_id; persistence failure raises LedgerStoreError (fail-closed).
  - Demo: `python3 -m runtime.sandbox.demo_governed_execution` runs all three cases; pytest `runtime/tests/test_sandbox_demo_e2e.py` (7 tests) + `runtime/tests/test_sandbox_ledger_store.py` (8 tests).
  - LoopController wiring: validated_to_sandbox uses result.success and result.ledger_row_id (GovernedExecutionResult); optional ledger_store for refusal rows.
  - pytest (`python3 -m pytest runtime/tests/test_sandbox_runner.py runtime/tests/test_sandbox_demo_e2e.py runtime/tests/test_sandbox_ledger_store.py runtime/tests/test_transition_executor.py -v`): 77 passed
- **M3.4 vs M3.8:** M3.4 covers sandbox execution evidence and **local deterministic persistence** sufficient for MVP demo. M3.8 covers broader ledger completeness, replay/join contract, and observation-bridge (Layer-4).
- **Architecture**:
  - DES → propose; CONF → authorize; CODE → execute (sandboxed) ← M3.4
  - Execution must never happen outside the sandbox; no bypass path.

### 6.9 M3.5 — Plan-Gate Integration

- **Milestone**: M3.5 Plan-Gate Integration — COMPLETE (2026-03-12); **all execution paths flow through Plan-Gate before sandbox; posture-complete (refuse, defer, bounded_allow, safe_execute).**
- **Artifacts** (6/6):
  - `runtime/plangate/plangate_decision.py` — PlanGateDecision (posture: refuse | defer | bounded_allow | safe_execute; authority_ok, boundary_detected, irreversible, reason); to_dict/from_dict.
  - `runtime/plangate/plangate_service.py` — PlanGateService.evaluate(request) → PlanGateDecision; deterministic rule-based (REFUSED_COMMANDS, plan_gate_defer, plan_gate_refuse, plan_gate_bounded_allow); no LLM.
  - `runtime/orchestrator/loop_controller.py` — Plan-Gate evaluated before validated_to_sandbox; refuse → REFUSED + ledger; defer → valid=False, stop_reason=deferred + plangate_deferred; bounded_allow → valid=False, stop_reason=bounded_allow + plangate_bounded_allow (distinct branch); safe_execute → sandbox; Plan-Gate not configured → refuse.
  - `runtime/sandbox/sandbox_ledger_store.py` — EVENT_PLANGATE_REFUSED, EVENT_PLANGATE_DEFERRED, EVENT_PLANGATE_BOUNDED_ALLOW, EVENT_PLANGATE_SAFE_EXECUTE; same store persists plangate_* and sandbox_*; linkage via request_id.
  - `runtime/sandbox/demo_governed_execution.py` — PlanGateService() in controller; five cases: SAFE_EXECUTE → EXECUTED, REFUSE (curl), REFUSED (no gate), DEFER → deferred, BOUNDED_ALLOW → bounded_allow; decision + outcome printed.
  - `runtime/tests/test_plangate_integration.py` — PlanGateDecision/PlanGateService (incl. force_bounded_allow, bounded_allow distinct from defer); LoopController: refusal/defer/bounded_allow prevent sandbox, safe_execute allows; decision persists; plangate_bounded_allow ledger row.
  - `docs/runtime/milestones/M3.3_PLAN_GATE_INTEGRATION.md` — milestone document; bounded_allow MVP meaning; future follow-up note (no bounded sandbox profile yet).
- **Evidence**:
  - **Execution chain:** request → Plan-Gate → runtime decision → LoopController transition → sandbox (if allowed) → ledger evidence. No execution path may bypass Plan-Gate.
  - **Postures (all four exercised):** refuse → REFUSED + plangate_refused + sandbox_refused; defer → valid=False, stop_reason=deferred + plangate_deferred; bounded_allow → valid=False, stop_reason=bounded_allow + plangate_bounded_allow (no sandbox); safe_execute → _run_sandbox_and_persist + plangate_safe_execute + sandbox_executed. Only safe_execute reaches sandbox in MVP.
  - **Governance:** DES → reasoning only; CONF → bounded safe action; CODE → execution via sandbox only. bounded_allow is first-class, non-sandbox, distinct from defer; richer bounded execution (e.g. read-only sandbox profile) is future work.
  - **Demo:** `python3 -m runtime.sandbox.demo_governed_execution` prints five outcomes including BOUNDED_ALLOW with ledger_row_id; 7 ledger rows (plangate_safe_execute, sandbox_executed, plangate_refused, sandbox_refused, sandbox_refused, plangate_deferred, plangate_bounded_allow).
  - **Tests:** pytest `runtime/tests/test_plangate_integration.py` (14 tests), `runtime/tests/test_sandbox_demo_e2e.py` (12 tests): bounded_allow proved end-to-end; distinct from defer (stop_reason, event_type).

### 6.10 M3.6 — Internal Plan-Gate Decomposition

- **Milestone**: M3.6 Internal Plan-Gate Decomposition — COMPLETE (2026-03-12); **Plan-Gate internally decomposed into explicit first-class subcomponents; external contract unchanged.**
- **Artifacts** (7/7):
  - `runtime/plangate/contracts.py` — AuthorityResult, IrreversibilityResult, JudgeInput dataclasses.
  - `runtime/plangate/authority_validator.py` — AuthorityValidator component; validates requester authority.
  - `runtime/plangate/irreversibility_detector.py` — IrreversibilityDetector component; classifies boundaries and irreversibility.
  - `runtime/plangate/judge_gate.py` — JudgeGate posture-decider; combines authority + irreversibility + hints → PlanGateDecision.
  - `runtime/tests/test_plangate_authority_validator.py` — AuthorityValidator unit tests (16 tests).
  - `runtime/tests/test_plangate_irreversibility_detector.py` — IrreversibilityDetector unit tests (18 tests).
  - `runtime/tests/test_plangate_judge_gate.py` — JudgeGate unit tests (15 tests).
- **Evidence**:
  - **Internal architecture:**
    ```
    PlanGateService
     ├─ AuthorityValidator  → AuthorityResult
     ├─ IrreversibilityDetector → IrreversibilityResult
     └─ JudgeGate → PlanGateDecision
    ```
  - **Flow:** request → AuthorityValidator → IrreversibilityDetector → JudgeGate → PlanGateDecision.
  - **External contract unchanged:** `PlanGateService.evaluate(request) → PlanGateDecision`.
  - **Fields now explicit:**
    - `authority_ok` backed by `AuthorityResult` from `AuthorityValidator`.
    - `boundary_detected` / `irreversible` backed by `IrreversibilityResult` from `IrreversibilityDetector`.
  - **Tests:** 49 new subcomponent tests (all pass); 14 integration tests (all pass); 12 E2E demo tests (all pass); demo unchanged.
  - **Nature:** Architectural hardening / decomposition, not a doctrine change. Not yet full enterprise RBAC or production-grade boundary policy.

### 6.12 Layer-3 Integration (M3.3, M3.8, M3.9)

- **Milestone**: M3.3 Agent Loop Orchestrator, M3.8 Ledger Emission/Replay, M3.9 Shadow Mode Validation — COMPLETE (2026-03-13). This section documents the final integration of these milestones on main (tag `layer3-runtime-governed-v1`).
- **Merge**:
  - Branch merged: `integration/layer3-next-verification` (merged into `main` with `--no-ff`)
  - Merge commit: `23395b60bb72d70d01fbb6750c1ffb70760c3dcd`
- **Validation evidence**:
  - **Runtime tests**: `python3 -m pytest runtime/tests` — **346 passed**
  - **Ledger demo**: `python3 -m runtime.ledger.demo_trace` — passed (all invariants satisfied)
  - **Shadow demo**: `python3 -m runtime.shadow_runner.run_demo` — passed (all scenarios, invariants held)
- **Tag**: `layer3-runtime-governed-v1` (created and pushed to origin)
- **Artifacts (summary)**: M3.3 — stop_conditions, budget_policy, transition_executor, replay, orchestrator_test_suite; M3.8 — runtime/ledger/* (contracts, emitter, store, replay, demo_trace), test_ledger_completeness; M3.9 — runtime/shadow/* (runner, harness, ingestion_batch, baseline_scenarios), shadow_runner_test, shadow_harness_test, test_emulator_invariants updates.

### 6.13 M3.10 — Sandbox Driver Abstraction

- **Milestone**: M3.10 Sandbox Driver Abstraction — COMPLETE (merged to main).
- **Artifacts**:
  - `runtime/sandbox/sandbox_driver.py` — SandboxDriver protocol, BaseSandboxDriver(ABC), LocalProcessSandboxDriver; driver_name for observability.
  - `runtime/sandbox/sandbox_executor.py` — Optional `driver` parameter; delegates to `_driver.run` / `_driver.validate_only`; default LocalProcessSandboxDriver.
  - `runtime/tests/test_sandbox_driver.py` — Driver and executor-through-driver tests.
  - `docs/runtime/milestones/M3.10_SANDBOX_DRIVER_ABSTRACTION.md`, `docs/runtime/branch_execution_notes/` (M3.10 note).
- **Evidence**:
  - Pluggable driver seam: executor owns governance and ledger; driver only runs/validates.
  - Default `SandboxExecutor()` uses LocalProcessSandboxDriver; backward compatible.
  - driver_name exposed for observability (e.g. sandbox_driver=local_process).

### 6.14 M3.11 — Container Sandbox Runtime

- **Milestone**: M3.11 Container Sandbox Runtime — COMPLETE (merged to main).
- **Container driver file**: `runtime/sandbox/container_sandbox_driver.py` — ContainerSandboxDriver(BaseSandboxDriver), driver_name = "container"; run/validate_only via podman/docker; workspace mount, exec form, timeout, --rm.
- **Tests passed**: pytest `runtime/tests/test_sandbox_runner.py` (37), `runtime/tests/test_sandbox_driver.py` (12), `runtime/tests/test_transition_executor.py` (26), `runtime/tests/test_sandbox_demo_e2e.py` (12), `runtime/tests/test_container_sandbox_driver.py` (17 passed, 1 skipped when no runtime). **Total: 105 passed, 1 skipped.**
- **Demo result**: `python3 -m runtime.sandbox.demo_governed_execution` — 7 ledger rows; refused / blocked / executed semantics preserved; DES → CODE execution and governance unchanged.
- **Fail-closed note**: Missing container runtime (podman/docker), invalid runtime path, or container run failure → SandboxExecutionError; executor returns EXECUTED (failed). No silent fallback to host or local process.
- **Opt-in backend selection**: Container backend only active when explicitly configured (e.g. `SandboxExecutor(driver=ContainerSandboxDriver())` or `create_sandbox_driver("container")`). Default remains LocalProcessSandboxDriver.
- **Commit / merge summary**:
  - **Branch name**: feature/m3.10-m3.11-execution-isolation
  - **Merge commit SHA**: 302fae2681fbfd07c732445674c988b957f170c6 (short: 302fae2)
  - **Tests run**: 105 passed, 1 skipped (test_container_sandbox_driver live test when no podman/docker).
  - **Demo result**: 7 ledger rows; refused / blocked / executed semantics preserved.

### 6.15 L5.5 / L5.6 — Wave-3 integration (A7 Plugin + A8 Plan-Gate `/v1/ask`)

- **Milestones**: **L5.5 (A7)** Plugin Evidence Bridge — COMPLETE (2026-03-21); **L5.6 (A8)** Plan-Gate Evidence Ingestion — COMPLETE (2026-03-21).
- **Artifacts (summary)**:
  - **Runtime / Plan-Gate:** `runtime/plan_gate_service/app.py` — `POST /v1/ask`; `runtime/ask_service/v1_ingest.py`; `runtime/ide/schemas/ask_request.v1.0.schema.json`; `runtime/ask_service/evidence_bridge.py` — `context_bundle_from_evidence_dict`; `runtime/tests/test_ask_v1_ingest.py`.
  - **WSL export (primary):** `packaging/motadata-context-layer/` wheel; `runtime/context_layer_service/` — `GET /healthz`, `POST /v1/export_evidence`; dev fallback `runtime/scripts/layer5_export_evidence.py`.
  - **Plugin:** `jetbrains-plugin/.../bridge/RuntimeBridge.kt`, `Layer5EvidenceExporter.kt`, `EvidenceExportOutcome.kt`, `AskV1Contract.kt`; default Context Layer URL `http://127.0.0.1:8091`; Plan-Gate default `http://127.0.0.1:8089` (see runbook for remote GPU).
- **Contract outcomes**:
  - Evidence-first uses real `**ask_request.v1.0`** and `**POST /v1/ask**` (not v0 `evidence_first` bolt-on for the primary path).
  - Listed v1 contract failures (`evidence_schema_invalid`, `identity_mismatch`, `empty_evidence_bundle`, `ask_envelope_invalid`) **do not** silently fall back to legacy.
  - Controlled fallback only: export/script failure, v1 **404/405**, or legacy mode (flag off).
- **Evidence (automated)**:
  - `python3 -m pytest runtime/tests/test_ask_v1_ingest.py` — PASS (v1 ingest + HTTP Plan-Gate slice).
- **Evidence (automated e2e smoke — Linux host, 2026-03-21)**:
  - Start Plan-Gate (`python3 -m runtime.plan_gate_service.app`, unset `MOTADATA_EXPLAIN_VLLM_URL`); `GET /healthz` OK.
  - `printf '<query>' | python3 runtime/scripts/layer5_export_evidence.py <repo_root>` → JSON evidence bundle.
  - `POST /v1/ask` with `ask_request.v1.0` + bundle (+ `expected_workspace_identity_hash` when hash non-empty) → `plan_only_response.v0.1`, `governance_posture=PLAN_ONLY`, `execution=false`, `evidence_first_meta.ask_path=v1_evidence`, non-empty `plan_summary.steps` (sample: 4 steps, 8 evidence entries).
- **Evidence (pending — operational e2e)**:
  - First full **Windows IDE + WSL Context Layer wheel + GPU Plan-Gate** run recorded by humans/CI when available; amend this subsection with transcript or run ID (checklist: `**docs/MOTADATA_DEMO_SCENARIOS.md`** §4).

### 6.16 Branch consolidation + M3.12 on L5 line (2026-03-21)

- **Unified branch:** `feature/l5-context-layer-v1-ask-packaging` now **merge-parent** for:
  - `feature/m3.12-narrow-context-engine` — `runtime/ask_service/handlers.py` gains **ManifestBuilder** + `**select_from_manifest`** (repo-aware file hints) while preserving **evidence_first**, `**ASK_DEFAULT_REPO_ROOT`**, **EXPLAIN_DEBUG**, and default **ContextEngine** selectors; `runtime/tests/test_ask_service.py` extended with M3.12 determinism tests.
  - `integration/m3.12-context-demo` — demo runbook / verification artifacts as merged.
  - `feature/m3.17-task-schema` — task-model slice + `**docs/runtime/C1_EXECUTION_TRACE_BUILDER_RESULT.md`** unified (M3.17 pre-merge sign-off appended).
- **Operator docs (in-repo):** `docs/MOTADATA_AI_CODING_ASSISTANT_ARCHITECTURE.md` (architecture); `docs/MOTADATA_DEMO_SETUP_RUNBOOK.md` (setup); `docs/MOTADATA_DEMO_SCENARIOS.md` (demo + success criteria).
- **Local cleanup:** After push, safe to `**git branch -d`** the merged topic branches listed in **§5 Immediate next action** (local only unless coordinated for `origin`).

#### 6.16.1 M3.12 on `main` — verification record (2026-04-18)

- **Truth:** Narrow M3.12 slice is **merged on `main`**: `runtime/context/manifest_builder.py`, `runtime/context/doc_selector.py`, `runtime/context/manifest_models.py`, integration in `runtime/ask_service/handlers.py` (`ManifestBuilder`, `select_from_manifest`). Spec: `docs/runtime/M3_12_NARROW_CONTEXT_ENGINE_SPEC.md`.
- **Automated (re-run on current `main` when auditing):**  
  `python3 -m pytest runtime/tests/test_m312_manifest.py runtime/tests/test_m312_doc_selector.py runtime/tests/test_m312_demo_scenarios.py runtime/tests/test_ask_service.py -q`  
  **Result at verification:** **29 passed** (Linux).

### 6.17 Action 11 — Compatibility Path Hardening (L5.9) — CLOSED (2026-03-31)

- **Milestone**: **L5.9** compatibility path hardening delivered as **Action 11** — explicit routing, trace chain, non-silent fallback, explain/planner observability.
- **Closure bar:** *Fallback rules documented and controlled; no silent path ambiguity remains.*
- **Evidence pack (operator-local, example run):** folder `Action-11-artifacts-20260331-103853` under the operator home (contains `pytest-action11.txt`, `plan-gate.stderr.log`, `context-layer.stderr.log`, `response_v1.json` / `response_v0_fb.json` / `response_explain.json`, `artifact4_metadata.txt`, `artifact4_plugin_ROUTING_DECISION.txt`, `RUN_SUMMARY.txt`).
- **Regression / automation:** `python3 -m pytest` targets in `docs/guides/ACTION_11_LINUX_TEST_RUNBOOK.md` (Track A); one-shot capture: `scripts/action11_one_shot_capture.sh`.
- **Branch (development line):** `feature/action-11-path-hardening-trace-routing` (schemas, Plan-Gate, plugin `AskRoutingDecisionLog`, tests).

> Future entries should follow this style: **Milestone**, then bullet list of concrete evidence files / metrics / reports.

### 6.18 Action 4 — Close plugin truthfulness gaps (2026-03-31)

**Status: ✅ CLOSED**

UI behavior is fully driven by backend `routing_mode`; plugin surfaces `trace_id`, `plugin_ask_routing`, and structured routing decisions. Fallback paths are explicitly visible (summary + WARNING notification) and no longer presented as normal success. Full-dialog routing is auditable and compact; notification summary is concise on success and explicit on fallback. Legacy AskClient is isolated and documented. Compilation and targeted tests pass; Gradle test failure is environment-related (IntelliJ plugin setup), not implementation-related.

- **Implementation pointers (Kotlin, `jetbrains-plugin/`):** `bridge/RuntimeBridge.kt`, `bridge/AskRoutingDecision.kt`, `ask/AskResultDialogMessage.kt`, `ask/AskMotadataAiAction.kt`, `ask/AskClient.kt`; tests include `AskUiRoutingTruthTest`, `AskResultDialogMessageTest`.

### 6.19 Action #5 — Plan-Gate observability (L5-OBS-1 HTTP) — CLOSED (2026-03-31)

- **Status: ✅ CLOSED**
- **Scope:** Observability and auditability only — no routing or execution semantics change.
- **Deliverables:**
  - **Plan-Gate** (`runtime/plan_gate_service/app.py`): every `POST` emits one `PLAN_GATE request` line with `path`, `request_type`, `request_id`, `trace_id` (literal `(none)` if absent), `routing_mode` (from ask responses when applicable, else `n/a`), `outcome` (layer + execute `outcome` when applicable), `status`, `duration_ms`.
  - **Ask v0** (`runtime/ask_service/handlers.py`): `[ASK] trace_id=… request_id=… task_type=…` (always).
  - **Ask v1** (`runtime/ask_service/v1_ingest.py`): `[ASK_V1] …` (always).
  - **Explain** (`runtime/ask_service/reasoner.py`): `EXPLAIN_DEBUG … routing_mode=explain_debug …` (always includes `trace_id` slot).
  - **Execute** (`runtime/execute_service/handlers.py`): `[EXECUTE] trace_id=… request_id=… phase=begin`; Plan-Gate line carries execute `outcome`.
- **Evidence:** `runtime/plan_gate_service/tests/test_plan_gate_request_logging.py`, `runtime/tests/test_action5_observability.py`; guide `docs/guides/ACTION_5_OBSERVABILITY_CORRELATION.md`.
- **Action #9** remains **FUNCTIONALLY CLOSED** with **audit pack pending** — observability supports reconstruction; the audit pack is separate work.

### 6.19a L5.8 — Grounded Ask validation harness (closure gate) — COMPLETE

- **Milestone:** **L5.8** baseline/harness closure (distinct from open-ended **§B1** generalization work).
- **Evidence:** **§B2** checklist (artifact paths, CI wiring, closure promotion); primary implementation locus `runtime/layer5/audit/` (l58 harness modules named in **B2**). This subsection satisfies **§8** “evidence in §6” for the **§4.5** **L5.8** row status.

### 6.20 Stage 3 — Controlled Runtime Loop (implementation) — BURN-IN / VALIDATION (2026-04)

- **Workstream:** **Stage 3 controlled runtime loop** — runtime-owned, schema-driven, bounded, observable hybrid loop (**not** ML pipeline “Stage 3”; see **§7** nomenclature).
- **Milestone / tracking:** Operational implementation + tests (**no new M3.x ID**); **§4.3** operational note; **§B7** burn-in / acceptance **CLOSED** (see **§B7** header).
- **Artifacts (factual scope):**
  - **Schemas:** JSON Schema contracts for task ingress, model proposals, tool request/result, loop decisions, final response, loop context frame (`runtime/state/schemas/` `*.v1.json`).
  - **Validators:** strict validation + evidence-integrity checks (`runtime/state/validators.py`).
  - **State machine:** deterministic transitions (`runtime/loop/state_machine.py`).
  - **Loop controller:** orchestration, budget, Plan-Gate hooks, fail-closed paths (`runtime/loop/loop_controller.py`).
  - **Decision engine:** policy mapping to terminal classes (`runtime/loop/decision_engine.py`).
  - **Model adapter:** `LoopContextFrame` → `ModelProposal` boundary (`runtime/adapters/model_adapter.py`).
  - **Tool executor:** sandbox integration + normalized outcomes (`runtime/tools/executor.py`).
  - **Ledger / observability:** append-only events, trace reconstruction with iteration linkage (`runtime/obs/ledger.py`).
  - **Fail-closed handling:** validation exceptions, in-loop Plan-Gate recheck failures, terminal alignment.
  - **Tests:** `runtime/tests/test_stage3_loop.py` — **22** passing cases (automated regression for blocked/refused/failed semantics and execution truth).
- **Committed burn-in record (offline pytest + artifacts):** `docs/validation/STAGE3_BURN_IN_REPORT.md`; `docs/validation/artifacts/stage3_pytest_output.txt` (native), `stage3_pytest_output_wsl.txt`, `stage3_pytest_subset_wsl.txt`, `sample_ledger_trace.json`. Native log re-captured **2026-04-08** at **`d4a2807`**. **Live governed HTTP:** `stage3_live_smoke_output.txt`, `stage3_trace_reconstruction.txt`, **`stage3_b7_wsl_tunnel_verify_ask_path.txt`**, report **§9** — **§B7** = **CLOSED** (2026-04-09). Full runbook: **docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md**.
- **Evidence summary:** bounded, runtime-owned semantics; truthful **blocked** / **refused** / **failed** / **insufficient** outcomes; fail-closed gate and validation behavior covered by automated tests; product **burn-in** = operator paths in `docs/guides/STAGE3_BURN_IN_AND_E2E_DEMO.md`.

### 6.21 AIOps MVP automated rerun evidence refresh (2026-04-06; tracker update 2026-04-07)

- **Milestone context:** refresh of grounded Ask usefulness signal using Stage-4 artifact batch.
- **Artifacts:** `docs/validation/AIOPS_MVP_FINAL_REPORT_TEMPLATE.md`; `/home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/summary/run_summary.json`; `/home/harshil/Harshil-PoCs/Stage-4-Artifacts/aiops_mvp/summary/run_summary.md`.
- **Evidence:** automated counts are PASS=8, PARTIAL=0, FAIL=0, ERROR=0; per-scenario `evidence_quality=STRONG` for A1/A2/D1/D2/P1/P2/C1/C2; A2 includes `QUERY_TOO_GENERIC` while remaining PASS.
- **Interpretation guardrail:** this entry updates the latest automated signal; production-grade closure still requires remaining gates in **§1.3** and **§B3** (**§B7** burn-in **closed**; **§B5** host readiness **closed** 2026-04-09).

### 6.22 Plugin Phase-1 truth proof — LOCKED (Stage 2 closure chronology item 1)

- **Milestone:** JetBrains plugin **Phase-1** operator-visible truth aligned to backend JSON for **S1–S8**; **`exact_match`: true** for every scenario in the frozen matrix.
- **Closure authority:** `docs/validation/PLUGIN_PHASE1_TRUTH_PROOF_CLOSURE.md`.
- **Artifacts:** `docs/validation/artifacts/plugin_phase1_truth_proof/` (`proof_matrix.json`, `proof_matrix.md`, `scenario_S1` … `scenario_S8`, `host_contract_check.json`).
- **Implementation / regression:** `jetbrains-plugin/src/test/kotlin/ai/motadata/plugin/ask/Phase1TruthProofHarnessTest.kt` — **`phase1ProofMatrixFrozenContract`** (default Gradle test); **`generatePhase1ProofPack`** tagged **`live`** (regenerate only with Context Layer + Plan-Gate up).
- **Guardrail:** Do not conflate this lock with **§B3** residual checklist or with **HTTP AIOps MVP** usefulness bars — orthogonal evidence surfaces.

---

## 7. Stage-based execution model (recalibrated, 2026)

> **Nomenclature:** **Program Stages 1–2** and **future expansion** below are **program / product execution** milestones (MVP demo → production-ready → later expansion). They do **not** replace ML pipeline stage labels (Stage-1 … Stage-8), M3 milestone IDs, or layer numbers. **Stage 3 controlled runtime loop** (**§1**, **§5**, **§6.20**) names the **implemented** Layer-3 loop surface — **distinct** from **§7.5** future “intelligence expansion” wording. Keep **§1 Header**, **§5**, and **§6** as the canonical status surfaces; use this section for phased outcomes and exit bars.

### 7.1 Program state snapshot (aligned with §1)

| Pillar | State |
|--------|--------|
| Architecture spine (4-layer governed) | Locked |
| Retrieval baseline (PR-6) | Locked |
| Action 11 — compatibility / path hardening (L5.9) | Closed — **§6.17** |
| Action 4 — plugin truthfulness | Closed — **§6.18** |
| Plugin Phase-1 truth proof (S1–S8) | Locked — **§6.22** |
| Action 5 — observability closure (L5-OBS-1) | Closed — **§6.19** |
| Stage 3 — controlled runtime loop (implementation) | Implemented — **§B7 burn-in / acceptance CLOSED** — **§6.20** |
| Action 14 — final acceptance | **PASS** — `docs/validation/artifacts/action14_final_acceptance/ACTION14_FINAL_ACCEPTANCE_REPORT.md` |

### 7.2 Product Authority + Code Understanding Layer (v1) — status

- **Design spec:** `docs/design/PRODUCT_AUTHORITY_CODE_UNDERSTANDING_LAYER_v1.md`
- **Implementation line (example):** `feature/phase-4-product-authority` (authority stack + evidence + Plan-Gate + eval + reasoning bridge)

| Phase | Focus | Status |
|-------|--------|--------|
| 1 | Authority foundation (registry, freshness, validation) | **COMPLETE** |
| 2 | Code index + entry points + adapter | **COMPLETE** |
| 3 | Authority-aware ranking | **COMPLETE** |
| 4 | Plan-Gate integration + answer anchoring + eval wiring | **COMPLETE** |
| 5 | Authority → action reasoning bridge (bounded fix/debug reasoning) | **COMPLETE** |

### 7.3 Stage 1 — MVP Demo (Coding + Reasoning)

**What this stage means now**

- **Product ownership truth** — registry-backed owner identification, not generic file lists.
- **Owner-first Ask / Debug / Plan** — grounded in evidence + authority where present.
- **Authority-aware answer synthesis** — validated vs stale vs weak paths; distractors not promoted as peers.
- **Bounded coding reasoning slice** — Ask → Plan → bounded reasoning (no full codegen; sandbox-compatible posture).
- **One credible end-to-end product-aware coding/reasoning demo** — proves the slice, not full production scale.

**Not part of Stage 1 scope (already closed — do not treat as open work)**

- Plugin truthfulness (**Action 4**, **§6.18**)
- Observability plumbing (**Action 5**, **§6.19**)
- Compatibility / path hardening (**Action 11**, **§6.17**)

**Exit criteria (Stage 1)**

- System **consistently identifies true owners** where authority applies.
- Answers are **owner-first** and **structurally grounded** (non-generic where authority exists).
- **Distractors** are **not** presented as peer owners.
- **Weak / stale authority** is handled **honestly** (hedge or no overclaim per policy).
- **At least one real coding scenario** works end-to-end (bounded reasoning acceptable).

### 7.4 Stage 2 — Fully Functional & Ready System

**Framing:** **Stage 2 closure is complete.** Reliability, repeatability, deployment trust, and final acceptance are now proven (Action 14 PASS). This section remains as historical stage framing.

**Scope**

- **S2.1 — L5.8-class validation depth (primary gate):** **L5.8 harness closure** is **COMPLETE** (**B2**); Stage 2 work continues with **expanded** goldens, perturbations, ambiguity / adversarial phrasing; metrics: owner@1 / owner@3, distractor error rate, weak-evidence precision, no-match honesty, false-strong rate (**aligns with B1 / §1.4 Track RET**).
- **S2.2 — Authority robustness:** drift handling, registry correctness, multi-owner / compound queries.
- **S2.3 — Broader coding capability validation:** repeatable **multi-file** reasoning, change-impact understanding, safe proposals, grounded diffs, execution honesty.
- **S2.4 — Observability at scale (post-closure):** trace reconstruction, production-grade logging reliability, artifact-based debugging — **extension** of closed L5-OBS-1 baselines, not reinvention.
- **S2.5 — Host readiness:** **COMPLETED**. WSL and native Linux backend host modes validated against the same GPU-governed Plan-Gate + vLLM stack (**§B5**).
- **S2.6 — Final acceptance (Action 14):** **COMPLETED (PASS)**. Unified suite (Ask, Debug, Plan, Code, No-match) passed with production sign-off.

**Exit criteria (Stage 2)**

- Validation **deterministic** and **repeatable**; no hallucinated ownership; weak/no-match honest; coding behavior grounded and safe; **deployment-ready** bar satisfied.

### 7.5 Future program expansion — Controlled Intelligence (post–Stage 2 trust; **not** the Stage 3 runtime loop)

> **Disambiguation:** This subsection is **future product capability expansion** (richer context, ingestion, benchmarking). The **Stage 3 controlled runtime loop** is the **implemented** governed loop (**§6.20**). Do not conflate the two “Stage” wordings.

**Goal:** Add bounded fluency **without** compromising grounding, truthfulness, or runtime control.

**Themes**

- **Deeper context layer** — e.g. dirty-buffer overlay, richer symbol/call coverage.
- **Broader authority coverage** — subsystem maps, versioned snapshots, more concepts.
- **Jira / PR / doc ingestion expansion** — **M3.13–M3.18** follow-ons (M3.12 **COMPLETE on `main`** — §6.16.1), task evaluation harness.
- **Stronger coding workflows (bounded)** — multi-file patch flows and iterative fix-validation loops under runtime-owned loop policy.
- **Model benchmarking** — e.g. Qwen3 / Qwen3-Coder vs grounded reasoning baselines.
- **Enterprise / operator maturity** — packaging, audit/export, operator workflows.

### 7.6 Priority order (program)

1. Product ownership truth  
2. Validation truth  
3. Operational trust  
4. Coding reliability  
5. Expansion and scale  

---

## 8. How to Update This Tracker

This file is the **single live progress dashboard** for the Motadata AI Coding Assistant roadmap. Future updates (including by automated tools such as Cursor) must follow these rules:

1. **Only update statuses when evidence exists**
  - Do not mark a milestone as `COMPLETE` or `LOCKED` without a corresponding evidence entry in **Section 6**.
  - Prefer moving milestones through `IN_PROGRESS → VALIDATING → COMPLETE → LOCKED` explicitly.
2. **Do not advance milestones without required artifacts and evidence**
  - A milestone may **not** be marked `VALIDATING`, `COMPLETE`, or `LOCKED` unless:
    - Its **required artifacts exist** (as listed in the milestone detail sections), and
    - Its **Evidence** section contains at least one concrete validation entry (file, metric, or report).
  - “Started coding” or partial implementation without artifacts and validation does **not** qualify.
3. **Append to the evidence log instead of rewriting history**
  - When a milestone completes, add a new subsection under **Section 6** with:
    - Milestone ID and name.
    - Bullet list of concrete evidence artifacts (files, metrics, reports).
  - Do **not** remove or rewrite prior evidence entries.
4. **Update current focus when the active milestone changes**
  - Keep **Section 5 (Current Sprint / Current Focus)** aligned with the actual active work.
  - Update:
    - `Current objective`
    - `Active tasks`
    - `Next execution order`
    - `Current blockers`
    - `Immediate next action`
5. **Do not alter constitutional doctrine**
  - Do **not** change phase semantics (REF, CONF, DES, MIX, CODE, REACH).
  - Do **not** change dominance hierarchy or irreversible boundary definitions.
  - Do **not** rename or reinterpret pipeline stages (Stage-1 through Stage-8).
  - If a documentation change appears to affect doctrine, it must be made in governance documents via a separate GREG process, **not** here.
6. **Preserve milestone IDs and naming**
  - Do not change milestone IDs (e.g., `M3.0`, `M4.1`) once created.
  - If a milestone is superseded, mark it as such in the **Notes** or **Exit criteria**, but keep the row for historical context.
7. **Keep tables and structure intact**
  - Maintain the section ordering (**§1–§8**) and table structures defined in this file.
  - When updating **§7 (stage-based execution)**, align Product Authority phase / stage wording with **§1 Header**, **§5**, and evidence in **§6**; do not conflate **§7** program stages with ML pipeline Stage-1…Stage-8; do not conflate **§7.5** future expansion with the **Stage 3 controlled runtime loop** (**§6.20**) (see the nomenclature note at the start of **§7**).
  - When adding new milestones (if ever necessary), place them in the appropriate layer section with a clear ID and description.
8. **Be concise but operational**
  - Avoid marketing language.
  - Focus on concrete status, dependencies, exit criteria, and evidence.

Following this protocol ensures that this tracker remains a durable, engineering-grade artifact that Cursor and humans can rely on for roadmap execution reviews.

---

