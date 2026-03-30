# Production-Grade Closure Handbook — Motadata AI Coding Assistant (m-coder)

Handy print reference for final closure workstreams, gates, sequence, and done-means-done criteria.

---

## Scope

- First **production-grade vertical slice** (not demo)
- Enforces **deterministic, grounded, and observable system behavior**

---

## Working Principle (Non-negotiable)

- Code retrieval happens **near the workspace (WSL / local repo)**
- Reasoning and governance happen on **GPU (Plan-Gate + vLLM)**
- Communication is **artifact-based (evidence bundles, metadata)**
- Plugin is a **thin client** (no hidden logic)
- **No silent fallback behavior** anywhere in the system

---

## Bottom Line

The system is NOT production-grade until:

- PR-6 locked retrieval baseline is preserved while generalization is validated
- Evidence grounding is **trustworthy and repeatable** beyond fixed closure fixtures
- Plugin reflects **backend truth without distortion**
- Observability is **complete and reconstructible**

Feature completeness is irrelevant without **grounded correctness**.

---

# 1. Current Truth State (Corrected)

### What is already solid

- Layer-1 Governance → Locked

- Layer-2 Compilation → Stable

- Layer-3 Runtime Core → Structurally sound

- Layer-4 Observation → Functional

- `/v1/ask` → Contract-correct and deterministic

- Workspace-local evidence export → Implemented

- Execute path → Honest under backend invocation

- Architecture is correct and MUST NOT be altered:
  
  - Retrieval → Workspace (WSL)
  - Reasoning + Governance → GPU (Plan-Gate + vLLM)
  - Plugin → Thin UI client only

---

### What is still blocking closure

### 1. Retrieval (Baseline Closed, Generalization Open)

- PR-6 true-positive debug retrieval closure phase is **COMPLETE / LOCKED**
- Deterministic retrieval baseline for debug grounding is now canonical
- Locked baseline metrics:
  - Top-1: **10/10**
  - Top-3: **10/10**
  - Mean first relevant rank: **1.00**
  - Noise dominance: **0.00**
- Remaining blocker is **generalization beyond the fixed validated set**, not baseline rescue

---

### 2. Grounding Quality

- Backend pipeline is correct
- PR-6 baseline debug grounding is correct on the locked set
- Production closure still requires L5.8 thresholds across broader Ask/Debug/Plan/Code + no-match sets

---

### 3. Plugin Truthfulness

- UI sometimes contradicts backend
- Misleading phrasing exists

---

### 4. Observability

- Request tracing incomplete
- Plan-Gate visibility insufficient

---

### 5. Host Validation

- Profiles defined
- Not production-validated across both profiles

---

## Closure Gates (Canonical)

| Gate           | Meaning                                                            | Status | Closure Condition                                   |     |
| -------------- | ------------------------------------------------------------------ | ------ | --------------------------------------------------- | --- |
| Grounding      | PR-6 baseline achieved; generalization remains mandatory           | OPEN   | L5.8 validation thresholds + drift/no-match gates   |     |
| Truthfulness   | Weak or insufficient evidence must not produce confident reasoning | OPEN   | Hard guard + reason codes enforced                  |     |
| Plugin Honesty | UI must reflect backend truth and path class                       | OPEN   | Evidence, ask\_path, notes, execute outcome visible |     |
| Observability  | Request must be traceable across Context Layer, Plan-Gate, vLLM    | OPEN   | Request ID + endpoint logging                       |     |
| Host Readiness | Windows + WSL + GPU and native Linux profiles validated            | OPEN   | Deployment/validation runbook passes both           |     |

---

# 2. Final Closure Workstreams (Corrected)

## WS-1: Retrieval Dominance Policy (Foundational Baseline)

**Closure status:** Foundational baseline landed and validated by PR-6

**Objective:** Preserve deterministic retrieval baseline (PR-6 locked) as the foundation with regression protection.

**Includes:**

- File classification (core / supporting / noise)
- Subsystem awareness (alerting, correlation, topology, etc.)
- Path priors and module bias
- Symbol-aware scoring
- Top-k diversity constraints

**Constraints:**

- Deterministic only
- No embeddings
- No learned rerankers
- No ML / SFT

**Exit condition:**

- Baseline preserved with no regression against PR-6 closure suite

## PR-6 Baseline Invariants (NON-NEGOTIABLE)

- Deterministic retrieval only (no embeddings, no semantic ranking)
- Workspace-local retrieval (WSL), not GPU
- Production code dominance over logs/tests/vendor
- Noise dominance must remain ~0.00
- Owner-file accuracy must not regress
- Any retrieval change must pass regression suite before merge

---

## WS-2: Weak-Evidence and No-Match Truthfulness

**Closure status:** Mandatory before closure

**Objective:** Guarantee system never overstates confidence beyond evidence.

**Includes:**

- Evidence quality classification:
  - STRONG
  - WEAK
  - INSUFFICIENT
  - NO\_MATCH
- Hard guard enforcement for INSUFFICIENT / NO\_MATCH
- Controlled reasoning for WEAK with explicit caveats
- Stable reason-code emission

**Exit condition:**

- No synthetic confidence under weak grounding
- All responses aligned with evidence quality

---

## WS-3: Grounded Ask Validation & Metrics (L5.8)

**Closure status:** Mandatory before closure

**Objective:** Immediate active continuation after PR-6 — make grounding generalization measurable and enforceable via production metrics.

**Includes:**

- Query suites:
  - Repo understanding
  - Debug
  - Plan/change
  - No-match
  - Adversarial ambiguity
- Metrics:
  - Core-code ratio
  - Noise ratio
  - Weak correctness
  - No-match correctness
  - False strong rate
  - False negatives

**Principle:**

- Metrics are **gates**, not diagnostics

**Exit condition:**

- All threshold metrics pass deterministically

---

## WS-4: Plugin Truthfulness Alignment

**Closure status:** Mandatory before closure

**Objective:** Ensure UI reflects backend truth exactly.

**Includes:**

- Evidence bundle rendering
- `ask_path` visibility
- `plan_summary.notes` exposure
- Truthful execution outcomes

**Fixes:**

- Remove misleading phrases (e.g., "no files selected" when evidence exists)

**Constraint:**

- Plugin remains thin
- No retrieval or reasoning logic inside plugin

**Exit condition:**

- UI is a faithful projection of backend state

---

## WS-5: Observability & Tracing (L5-OBS-1)

**Closure status:** Mandatory before closure

**Objective:** Make every request reconstructible end-to-end.

**Includes:**

- `request_id` propagation across:
  - Context Layer
  - Plan-Gate
  - vLLM
- Plan-Gate request/access logging
- Path and decision visibility
- Optional GPU/log-level verification for audit-grade traceability

**Exit condition:**

- No debugging via guesswork
- Full trace per request

---

## WS-6: Host-Profile Readiness

**Closure status:** Mandatory before closure

**Objective:** Ensure system behaves identically across supported environments.

**Includes:**

- Windows + WSL + GPU validation
- Native Linux + JetBrains + GPU validation
- Config externalization
- Removal of implicit localhost assumptions

**Exit condition:**

- Both profiles pass validation runbook

---

## WS-7: Compatibility Path Hardening (L5.9)

**Closure status:** Mandatory before closure

**Objective:** Control legacy fallback paths explicitly.

**Includes:**

- `repo_root` / `ASK_DEFAULT_REPO_ROOT` handling
- Canonical path definition
- Controlled fallback behavior
- Telemetry/comparison vs workspace-local evidence path

**Exit condition:**

- No ambiguity between compatibility and canonical path

---

## WS-8: Mainline, Docs & Release Hygiene

**Closure status:** Mandatory before closure

**Objective:** Remove all ambiguity from system state and documentation.

**Includes:**

- Branch/mainline convergence
- Canonical documentation set:
  - Charter
  - Roadmap tracker
  - Deployment/validation runbook
  - Acceptance scenarios
  - Retrieval policy
  - Validation sheets
- Alignment between product docs and actual system behavior

**Exit condition:**

- Single source of truth across code, docs, and runtime

---

##  3. Numbered Action Items to Final Closure

These action items are executed strictly in alignment with the Phase sequence defined in Section 6. No item should be progressed out of phase.

Actions **1–7** are materially satisfied by the locked PR-6 retrieval baseline, L5.8 closure validation, completed plugin product-truthfulness logic, completed main HTTP-path observability (Context Layer, Plan-Gate, explain/debug logging), completed Explain/Debug trust validation (server and plugin contract), and completed Execute-path trust validation on the **live HTTP product path** (`POST /v0/execute`). **Action 8 (Validate no-match honesty)** remains **satisfied** under the **L5.8 / Action 3** closure already recorded below (strict no-match honesty); it is **not** reactivated as unfinished work. The current active action is **9 (Close host profile A)**.

| **#**     | **Action item**                        | **What it includes**                                                              | **Done means done**                               |
| --------- | -------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------- |
| **~~1~~** | ~~Land retrieval policy PR-1~~         | ~~File/subsystem classifier, scoring priors, deterministic tests~~                | ~~PR merged; tests green; top-k visibly cleaner~~ |
| **~~2~~** | ~~Land retrieval policy PR-2~~         | ~~Intent classifier, weak-evidence quality gate, hard reasoning guard~~           | ~~Weak/insufficient/no-match behavior enforced~~  |
| **~~3~~** | ~~Complete L5.8 validation harness~~   | ~~Golden + adversarial query packs, before/after metrics~~                        | ~~Quality metrics reproducible and published~~    |
| **~~4~~** | ~~Close plugin truthfulness gaps~~       | ~~Evidence rendering, ask\_path, notes, execute honesty~~                           | ~~Plugin no longer contradicts backend truth~~      |
| **~~5~~** | ~~Close Plan-Gate observability gap~~  | ~~Request logging, correlation IDs, trace reconstruction~~                      | ~~Any request traceable end to end~~              |
| **~~6~~** | ~~Validate Explain/Debug path rigorously~~ | ~~Prove vLLM use when required; prove no hidden repo access~~                         | ~~Debug path contract and logs are trustworthy~~      |
| **~~7~~** | ~~Validate Execute path rigorously~~       | ~~Refused/blocked/executed (incl. executed-failed vs blocked) always distinct and truthful; `plan_gate_*` server-rejected by default on live HTTP~~ | ~~No fake success; no ambiguity; trust boundary enforced~~ |
| **~~8~~** | ~~Validate no-match honesty~~              | ~~Out-of-scope and absent-symbol queries return explicit insufficiency~~              | ~~Satisfied under L5.8 / Action 3 closure; see note below~~ |
| **9**     | Close host profile A                   | Windows + WSL + GPU full release validation pass                                  | **Functional closure:** checklist + runbook (**FUNCTIONALLY CLOSED**); **audit pack** (trace file + packaging + validation sheets) pending, non-blocking |
| **10**    | Close host profile B                   | Native Linux full release validation pass                                         | Checklist passes; config documented               |
| **11**    | Close compatibility path hardening     | Fallback rules documented and controlled                                          | No silent path ambiguity remains                  |
| **12**    | Mainline convergence                   | Feature branch/integration line/main are operationally unambiguous                | Release branch truth is clear                     |
| **13**    | Canonical doc finalization             | Roadmap, charter, runbook, validation sheets, retrieval policy linked and current | No active contradiction across docs               |
| **14**    | Final acceptance run                   | Ask, Debug, Plan, Code, No-match, Failure-mode suite                              | All pass on reference environment                 |
| **15**    | Production-slice release sign-off      | Hard gates reviewed against evidence                                              | Ready to claim first production-grade slice       |

**Note:** PR-6 baseline remains locked on canonical real-repo context. L5.8 includes guard-context hardening so synthetic or shifted-root corpora cannot produce false baseline regression signals during baseline comparison.

L5.8 Action 3 closure: PR-6 baseline preserved; guard-context hardening completed; retrieval generalization materially recovered; code-targeting rank-depth resolved; strict no-match honesty fixed; latency p95 reduced below hard gate (<= 400 ms); no remaining hard drift failures. Warning-level latency monitoring remains non-blocking CI observation.

**Action 4:** Action 4 product-truthfulness logic is complete. Remaining JetBrains plugin `:test` reliability is environment/tooling debt and does not reopen the truthfulness feature closure itself.

**Action 5:** Action 5 product-observability logic is complete for the main HTTP product path. Remaining runbook/CI/non-HTTP parity work is operational follow-through and does not reopen the observability closure itself.

**Action 6:** Action 6 Explain/Debug trust validation is complete for product logic (server and plugin contract). Remaining IntelliJ plugin test-runtime execution is environment/tooling debt and does not reopen the Explain/Debug trust closure.

**Action 7:** Action 7 execute trust validation is complete for the live HTTP product path (including executed-failed vs blocked honesty and server-enforced rejection of `plan_gate_*` client hints by default). Remaining direct-handler validation discipline and broader auth/binding concerns are out-of-scope follow-through and do not reopen the execute trust closure.

**Action 8:** Action 8 (no-match honesty) remains satisfied under the L5.8 / Action 3 closure already recorded above; it is not reactivated as the current frontier.

**Action 9:** **FUNCTIONALLY CLOSED (Audit pack pending).** Host Profile A has passed the **functional** bar (Ask, Explain/Debug, Execute boundary, No-match, Failure) per `docs/guides/ACTION_7_TRUST_AUDIT.md`; no new product blocker has been proven in this slice. **Remaining** work is **audit discipline** only: formal `mapping_request_ids.md`, per-scenario `hostA_proof_pack/` packaging, and the two validation sheets — see `docs/guides/HOST_A_PROOF_PACK_CLOSURE.md`. This follow-through is **non-blocking** for product iteration; it is **required** for enterprise audit-grade submission.

# 4. Critical Correction (NEW — Architecture Reality)

## Two-Connection Model (Must be Preserved)

### Connection A — Source of Truth

WSL → AIOps Repo

- Retrieval
- Symbol extraction
- Evidence generation

### Connection B — Reasoning

WSL → GPU

- Evidence bundles
- Metadata

🚨 GPU MUST NOT read repo directly

---

# 5. PR-6 (Mandatory Closure Phase)

## Status

**COMPLETE / LOCKED**

## What PR-6 proved

- Deterministic true-positive debug grounding works on real Motadata repo symbols/files
- Retrieval ranking can be owner-first and noise-controlled without embeddings, AST parsing, or GPU retrieval
- PR-6 is the mandatory baseline contract for debug grounding

## Locked closure metrics

- Top-1: **10/10**
- Top-3: **10/10**
- Mean first relevant rank: **1.00**
- Noise dominance: **0.00**

## Canonical conclusion

PR-6 is now the baseline retrieval contract for debug grounding. Downstream work must preserve, not weaken, this baseline and must re-validate when ranking logic changes.

---

# 6. Recommended Execution Sequence (Production-Grade Closure Flow)

This sequence is refined based on real validation learnings. PR-6 baseline closure is complete; the active frontier is controlled generalization + truthfulness + observability.

---

## Phase A — Deterministic Grounding Control (Foundation)

**Action items:** 1 → 2 (foundational, landed)

**Objective:** Make retrieval deterministic, auditable, and measurable.

**Includes:**

- Retrieval policy (PR-1)
- Intent + quality gate (PR-2)

**Exit criteria:**

- Deterministic ranking reproducible
- Quality gate stable (STRONG / WEAK / INSUFFICIENT / NO\_MATCH)

---

## Phase B — True-Positive Debug Grounding (PR-6)

**Action items:** foundational closure phase (complete)

**Objective:** Establish deterministic true-positive debug grounding baseline on real Motadata repo.

**Result (locked):**

- Top-1: 10/10
- Top-3: 10/10
- Mean first relevant rank: 1.00
- Noise dominance: 0.00

**Exit status:** COMPLETE / LOCKED (baseline contract preserved going forward)

---

## Phase C — Generalization + Truthfulness Validation

**Action items:** 3, 6, 7, 8

**Objective:** Validate post-PR-6 generalization and enforce truthful behavior under weak/no-match evidence.

**Includes:**

- L5.8 grounded validation harness + metrics gates (WS-3)
- Weak/no-match truthfulness under generalized query packs (WS-2 + WS-3)
- Debug path validation
- Execute path validation
- No-match honesty

**Important distinction:**

- Baseline debug grounding is locked by PR-6; this phase expands confidence to broader query and perturbation spaces.

**Exit criteria:**

- No hallucinated reasoning
- Clear distinction: executed vs refused vs blocked
- Weak evidence always caveated

---

## Phase D — Product Surface + Observability

**Action items:** 4, 5

**Objective:** Make UI truth and request traces production-trustworthy.

**Includes:**

- Plugin truthfulness alignment
- request\_id propagation
- Plan-Gate logging
- vLLM invocation trace visibility

**Exit criteria:**

- Plugin view is consistent with backend evidence/truth outputs
- Single request traceable across:
  - Context Layer
  - Plan-Gate
  - vLLM
- No debugging via guesswork

---

## Phase E — Compatibility + Host Closure

**Action items:** 9–11

**Objective:** Close host validation and compatibility hardening before final acceptance.

**Includes:**

- Windows + WSL + GPU validation
- Native Linux validation
- Compatibility path control

**Exit criteria:**

- Both host profiles pass identical validation
- No hidden localhost/tunnel assumptions

---

## Phase F — Program Closure

**Action items:** 12–15

**Objective:** Finalize production slice and remove all ambiguity.

**Includes:**

- Mainline convergence
- Canonical doc alignment
- Final acceptance suite
- Production sign-off

**Exit criteria:**

- All gates backed by evidence artifacts
- No contradiction across docs, code, or behavior

---

## Key Execution Principle (Critical)

Do not relax PR-6 baseline protections while executing L5.8/L5-OBS-1/plugin truthfulness gates.

This prevents regression while generalizing from a validated baseline.

---

# Final Principle

A system that retrieves the wrong file perfectly is still broken.

---

This version reflects actual system behavior and enforces true production closure discipline.
