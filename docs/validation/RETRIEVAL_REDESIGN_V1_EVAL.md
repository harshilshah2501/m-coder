# RETRIEVAL REDESIGN V1 — EVALUATION REPORT

**Doc status:** empirical (data-backed only — no invented metrics)

**Date:** `2026-04-14` (from run report timestamp)

**Workspace:** `/home/harshil/Projects/Motadata`

**Branch:** `feat/motadata-behavior-verification-guide`

**Evaluator:** `<fill>`

---

## How to use

1. Run **Baseline** (pre–Retrieval Redesign v1) and **V1** (post-change) against the **same** Motadata checkout when possible.
2. Fill tables from **real outputs** (logs, `motadata_behavior_verify.py` reports, fusion diagnostics). If baseline is missing, note *approximate / from memory* explicitly.
3. Do not narrate success without numbers or concrete path lists.

**Helpful repo paths**

- Behavior / utility verification: `runtime/scripts/motadata_behavior_verify.py`
- Scenario JSON (examples): `docs/validation/motadata_aiops_behavior_scenarios.v1.json`, `docs/validation/motadata_developer_utility_scenarios.v1.json`
- Production verification guide: `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`

---

# 1. Objective

Evaluate impact of **Retrieval Redesign v1** on:

- retrieval signal quality
- evidence grounding
- developer usefulness (Ask / Debug / Plan)

---

# 2. Setup

## 2.1 Environment

| Item | Value |
| ---- | ----- |
| Workspace root | `/home/harshil/Projects/Motadata` |
| Repo commit | `627b516b1df67c6f0e0d58ad0d02e18b82b881d5` (V1) / `c3ca2a2` (baseline worktree commit attempted) |
| Index state | `N/A (not captured)` |
| Model | `motadata-coder` (`/ml/training/pipeline/stage08/base_model`) |
| Context layer URL | `http://127.0.0.1:8091` (healthy, HTTP 200) |
| Plan-Gate URL | `http://127.0.0.1:8089` (healthy, HTTP 200) |

## 2.2 Runs

| Run | Description |
| --- | ----------- |
| **Baseline** | `repeat=2`, `stable=true`, `all_pass=true` from `baseline_run_verification.txt` and `motadata_behavior_validation.baseline_pre_v1.json` |
| **V1** | `repeat=2`, `stable=true`, `all_pass=true`; scenarios file `docs/validation/motadata_aiops_behavior_scenarios.v1.json` with `all_pass=true` |

**Baseline validity note:** baseline and v1 outputs are currently near-identical. A strict clean-room baseline (pre-v1 services started from pre-v1 worktree) was attempted but stalled at `export_evidence` with no completed report, so causal improvement claims remain constrained.

---

# 3. Scenario Set

## 3.1 Utility scenarios

| ID | Type | Query | Notes |
| -- | ---- | ----- | ----- |
| U1 | Ask | `How does alert correlation and enrichment work?` | Scenario id: `ask_broad_correlation`; pass; `evidence_quality=WEAK` |
| U2 | Debug | `Debug why incident enrichment might be skipped for some events` | Scenario id: `debug_explain_selection`; pass; `routing_mode=explain_debug` |
| U3 | Plan | `N/A (shadow event in verifier)` | Scenario id: `plan_pr_merge_shadow`; pass; decision `REFUSAL` |

(Add rows as needed.)

## 3.2 Anchored evaluation set (high signal)

| ID | Query | Expected owner / class / path |
| -- | ----- | ----------------------------- |
| A1 | `Where is alert correlation implemented? Reference AvailabilityCorrelationEngine or AlertCorrelationEngine.` | `AlertCorrelationEngine` / `AvailabilityCorrelationEngine` mention expected |
| A2 | probe OBJECT_DOWN flow | `N/A (not run in this artifact)` |
| A3 | incident creation logic | `N/A (not run in this artifact)` |

---

# 4. Retrieval metrics (before vs after)

## 4.1 Owner accuracy

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| owner@1 | `1.00 (1/1 anchored ask)` | `1.00 (1/1 anchored ask)` |
| owner@3 | `1.00 (1/1 anchored ask)` | `1.00 (1/1 anchored ask)` |

*(Owner proxy used here: whether anchored ask (`ask_symbol_anchored`) reports the expected owner class/path in plan summary.)*

## 4.2 Noise / distractors

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| Avg distractor count (top-k) | `N/A (not directly emitted as numeric)` | `N/A (not directly emitted as numeric)` |
| Generic infra ratio | `N/A (not directly emitted as numeric)` | `N/A (not directly emitted as numeric)` |

## 4.3 Anchoring quality

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| Anchor hit rate | `1.00 for shown context_bundle items` | `1.00 for shown context_bundle items` |
| Correct package match | `PARTIAL` | `PARTIAL` |

---

# 5. Evidence quality distribution

| Quality | Baseline | V1 |
| ------- | -------- | -- |
| STRONG | `1` | `1` |
| WEAK | `3` | `3` |
| INSUFFICIENT | `0` | `0` |
| NO_MATCH | `0` | `0` |

*(Counts above use ask responses visible in each run artifact: smoke run1 ask, smoke run2 ask, scenario `ask_broad_correlation`, scenario `ask_symbol_anchored`.)*

---

# 6. Ask behavior comparison

### Example: `ask_broad_correlation`

#### Baseline

- Top paths (sample): `AvailabilityCorrelationEngine.java`, `MetricPoller.java`, `MotadataAppManager.java`, `ConfigDBServiceImpl.java`, `Notification.java`, `APIServer.java`, `LAMAIntegration.java`, `PolicyCacheServiceImpl.java`
- Evidence quality: `WEAK` (`QUERY_TOO_GENERIC`)
- Answer summary: reports primary owner `AlertCorrelationEngine`, collaborators, and explicit distractor note for `AvailabilityCorrelationEngine`.

#### V1

- Top paths (sample from context bundle): `AvailabilityCorrelationEngine.java`, `MetricPoller.java`, `MotadataAppManager.java`, `ConfigDBServiceImpl.java`, `Notification.java`, `APIServer.java`, `LAMAIntegration.java`, `PolicyCacheServiceImpl.java`
- Evidence quality: `WEAK` (`QUERY_TOO_GENERIC`)
- Answer summary: reports primary owner `AlertCorrelationEngine`, collaborators, and explicit distractor note for `AvailabilityCorrelationEngine`.

#### Delta

- Improvement: no measurable change vs captured baseline.
- Regression: top-k still noisy/generic infra heavy for broad ask in both runs.
- Notes: this behavior is stable; uplift not demonstrated here.

### Example: `ask_symbol_anchored`

#### Baseline

- Top paths (scenario output): `AvailabilityCorrelationEngine.java`, `DiscoveryEngine.java`, `UIActionEventHandler.java`, `ObjectManager.java`, `APIServer.java`, `package-info.java`, `DependencyManager.java`, `DependencyQueryProcessor.java`
- Evidence quality: `STRONG`
- Answer summary: primary owner reported as `AlertCorrelationEngine`; support paths include topology/dependency context.

#### V1

- Top paths (scenario output): `AvailabilityCorrelationEngine.java`, `DiscoveryEngine.java`, `UIActionEventHandler.java`, `ObjectManager.java`, `APIServer.java`, `package-info.java`, `DependencyManager.java`, `DependencyQueryProcessor.java`
- Evidence quality: `STRONG`
- Answer summary: primary owner reported as `AlertCorrelationEngine`; support paths include topology/dependency context.

#### Delta

- Improvement: no measurable change vs captured baseline.
- Regression: top-k still includes generic files not tightly scoped to owner implementation in both runs.
- Notes: anchored path works, but this appears pre-existing in captured baseline.

---

# 7. Debug quality comparison

### Example: `debug_explain_selection`

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| References correct file | `YES` | `YES` |
| References control flow | `YES` | `YES` |
| Concrete vs generic | `MIXED` | `MIXED` |

---

# 8. Plan / code usefulness

| Metric | Baseline | V1 |
| ------ | -------- | -- |
| Grounded file selection | `PARTIAL` | `PARTIAL` |
| Safe scope definition | `YES` | `YES` (`governance_posture=PLAN_ONLY`, plan `decision=REFUSAL`, execute governed) |
| Hallucination risk (qualitative) | `MEDIUM` | `MEDIUM` on broad asks (`WEAK` + generic retrieval set) |

---

# 9. Utility scenario results

| Scenario | Baseline | V1 | Delta |
| -------- | -------- | -- | ----- |
| U1 (`ask_broad_correlation`) | `PASS` (`evidence_quality=WEAK`) | `PASS` (`evidence_quality=WEAK`) | `No measurable change` |
| U2 (`debug_explain_selection`) | `PASS` (`routing_mode=explain_debug`, has summary) | `PASS` (`routing_mode=explain_debug`, has summary) | `No measurable change` |
| U3 (`plan_pr_merge_shadow`) | `PASS` (`decision_response.v0.1`, decision present) | `PASS` (`decision_response.v0.1`, decision present) | `No measurable change` |

Additional scenario results in same run:

- `ask_symbol_anchored`: `PASS`, `evidence_quality=STRONG`
- `code_echo_probe`: `PASS`, `outcome=EXECUTED`
- `agent_no_route`: `PASS`, `/v0/agent=404`, assist layer present

---

# 10. Qualitative observations

### Improvements

- No clear improvements demonstrated against captured baseline artifacts.

### Regressions

- No direct regression observed in contracts (all pass), but retrieval top-k remains noisy in broad asks.

### Neutral

- System governance behavior (`PLAN_ONLY`, plan refusal, safe execute posture) remains unchanged.
- Anchored ask still reports owner and passes scenario expectations in both runs.

---

# 11. Failure analysis

| Scenario | Failure type | Root cause (retrieval / grounding / reasoning) |
| -------- | ------------ | ----------------------------------------------- |
| `ask_broad_correlation` | Weak evidence quality (`WEAK`) persists | retrieval + grounding (query generic; noisy top-k dominates) |
| `debug_explain_selection` | Answer partly generic in both runs | reasoning + grounding (selection text is directive, not concrete code snippet) |
| `baseline_pre_v1_true` attempt | Incomplete run (stalled) | environment/measurement risk (clean pre-v1 service run did not complete) |

---

# 12. Key insights

- Architecture/contract lane is stable in both captured runs (`all_pass=true`, `stable=true`, scenario suite pass).
- Utility lane pattern is unchanged across captured baseline and v1 (anchored ask `STRONG`, broad ask `WEAK`).
- A strict clean-room baseline remains incomplete due stalled pre-v1 service run; treat comparative claims as provisional.

---

# 13. Decision

| Question | Answer |
| -------- | ------ |
| Did retrieval improve? | UNCLEAR |
| Is developer usefulness improved? | UNCLEAR |
| Ready for closure (v1)? | NO |

---

# 14. Next actions

## If improvement confirmed

- Proceed to v1.1 (targeted fixes):
  - reduce generic infra in broad ask top-k
  - tighten owner path constraints and distractor caps
  - improve snippet targeting for debug to reduce generic prose

## If not

- Identify dominant failure layer:

  - retrieval
  - grounding
  - reasoning

---

# 15. Final verdict

Retrieval redesign v1 is:

- [ ] Successful
- [ ] Partially successful
- [x] Not effective

**Justification (evidence-only):**
- Captured baseline and v1 artifacts show no measurable delta on primary reported metrics (scenario pass, broad ask quality, anchored ask quality, top paths).
- Broad ask remains `WEAK` with noisy context bundle in both runs.
- A strict clean pre-v1 baseline attempt stalled at `export_evidence`, so definitive causality is not established.
- Therefore: implementation exists, but measured developer-outcome improvement is not yet demonstrated.

---
