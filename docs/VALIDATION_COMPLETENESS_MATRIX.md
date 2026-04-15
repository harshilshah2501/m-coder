# VALIDATION_COMPLETENESS_MATRIX — what is genuinely proven

**Purpose:** Separate **exists in code**, **tested**, **CLI/HTTP exercised**, **artifact-backed**, and **tracker closure**. Avoid **test illusion** (many tests ≠ product slice proven).

**Authority:** `docs/LIVE_ROADMAP_TRACKER.md` for closure; this matrix adds **gap typing**.

---

## Gap type legend

| Gap type | Meaning |
|----------|---------|
| **CLOSED** | Tracker + (artifact or explicit sign-off) |
| **PARTIALLY_VALIDATED** | Some of: unit test, CLI, artifact; not all layers |
| **NO_TEST** | Little/no automated test found (may still be CLI-proven) |
| **NO_ARTIFACT** | No saved proof under `docs/validation/artifacts/` |
| **INFERRED_ONLY** | Understood from code paths only |
| **FOLLOW_ON_ONLY** | Explicitly follow-on in tracker (not MVP blocker) |

---

## Matrix

| Surface / contract / workflow | Exists in code | Has test | Has CLI/HTTP validation | Has artifact evidence | Closure status (tracker) | Gap type | Notes |
|------------------------------|---------------|----------|-------------------------|------------------------|---------------------------|----------|-------|
| **Evidence bundle `layer5.evidence_bundle.v1`** | Yes — `runtime/layer5/`, schemas | Yes — export tests | Yes — verifier checks `schema_hint` | Yes — verifier JSON | B2/L5 related | **CLOSED** | |
| **`POST /v1/ask`** | Yes — `plan_gate_service/app.py` | Yes — `test_ask_v1_ingest.py` | Yes — `motadata_behavior_verify.py` | Yes — `motadata_behavior_validation.json` | Closed | **CLOSED** | Primary CLI path |
| **`POST /v0/ask`** | Yes | Yes — `test_ask_service.py` | **Partial** — verifier focuses v1 for “query” | Via live runs | Closed (dual-path known) | **PARTIALLY_VALIDATED** | Default IDE; explicit v0 row in scenarios optional |
| **`POST /v0/execute`** | Yes | Yes — execute tests | Yes — verifier | Verifier JSON | Closed | **CLOSED** | |
| **`POST /v0/plan`** | Yes | Yes (plan handler / HTTP) | Yes — verifier | Spool optional | Closed | **CLOSED** | Stub policy semantics |
| **Explain/Debug (`EXPLAIN_DEBUG`)** | Yes | Yes — reasoner tests | Yes — verifier | Verifier JSON | Closed | **CLOSED** | Needs vLLM for “quality” |
| **Request tracing / correlation** | Yes — structured logs | Yes — `test_action5_observability.py` | Yes — grep logs + verifier IDs | Proof pack docs | B4 closed | **CLOSED** | vLLM process logs = ops follow-on |
| **PR-6 retrieval baseline** | Yes | Yes — L58 + retrieval tests | Indirect via harness | PR-6 reports | Tracker: locked | **CLOSED** | |
| **L5.8 harness** | Yes — `runtime/layer5/audit/` | Yes — `test_l58_*.py` | pytest | `l58_grounded_report.*` | B2 closed | **CLOSED** | |
| **B1 expanded goldens** | Yes | Yes | pytest / CI | `docs/validation/artifacts/b1_retrieval_validation/` | B1 closed | **CLOSED** | |
| **Stage 3 loop burn-in** | Yes — `runtime/loop/` | Yes — `test_stage3_loop.py` | **No** dedicated CLI (pytest only) | `stage3_pytest_output*.txt` | B7 closed | **PARTIALLY_VALIDATED** if “CLI” required — **CLOSED** for pytest+artifact definition | No HTTP |
| **Host readiness (B5)** | Yes — scripts/env | Partial — implicit | Yes — stack + verifier | `b5_*` artifacts | B5 closed | **CLOSED** | |
| **No-match honesty** | Yes — metadata + L5.8 | Yes — `test_l58_nomatch_honesty_slice.py` | Partial — verifier shows quality fields | L5.8 outputs | Partial closure | **PARTIALLY_VALIDATED** | Edge cases remain |
| **Weak-evidence truthfulness** | Yes | Yes — harness + ingest tests | Yes — verifier `evidence_quality` | Reports | Tracker | **CLOSED** / **PARTIALLY_VALIDATED** | Residual warnings non-blocking |
| **Plugin truthfulness** | Yes — Kotlin | Yes — plugin tests | **DEFERRED** this pass | Plugin Phase-1 matrix | B3 closed (MVP) | **PARTIALLY_VALIDATED** (CLI lens) | **DEFERRED_INTEGRATION** for primary proof |
| **Stage3LoopController + live IDE** | Yes | No E2E IDE test in repo | No | Runbook only | Follow-on | **FOLLOW_ON_ONLY** | Per tracker |
| **`archive/legacy_runtime_rag/` product path** | Yes | Some | Not in `motadata_behavior_verify.py` | Sparse vs slice | OUT | **INFERRED_ONLY** / gap | Parallel stack |

---

## Summary scores (qualitative)

| Question | Answer |
|----------|--------|
| Is the **HTTP vertical slice** well tested + CLI proven? | **Yes** — strong |
| Is every **subdirectory** equally proven? | **No** — `archive/legacy_runtime_rag/`, root `observation/` differ |
| Does **pytest count** equal **product confidence**? | **No** — map tests to surfaces (orchestrator vs HTTP) |

---

## Explicit non-claims

- **Closed MVP** does not imply every Python file in `runtime/` ran in one integration test.
- **B7 closed** means Stage 3 **burn-in definition** met — not “Stage3 wired to JetBrains.”
