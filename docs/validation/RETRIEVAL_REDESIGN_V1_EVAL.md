# RETRIEVAL REDESIGN V1 — EVALUATION REPORT

**Doc status:** empirical (data-backed only — no invented metrics)

**Date:** `2026-04-15` (baseline/v1 artifacts); **v1.1 empirical:** `2026-04-15` (WSL run, `motadata_behavior_validation.json` / stdout capture)

**Workspace:** `/home/harshil/Projects/Motadata`

**Branch:** `feat/motadata-behavior-verification-guide`

**Evaluator:** `<fill>`

---

## 2026-04-16 closure note (current branch truth)

This section records the latest validated state and supersedes older "v1.1 no uplift" language for the current branch line.

- **Anchored authority-gated retrieval: working baseline achieved**
  - strict anchored lane passes (`ask_anchor_owner_top1`)
  - `owner_in_top1=true`, `owner_in_top3=true`
  - `require_authority_status=validated` passes
- **Broad ask retrieval: improved, not final**
  - `ask_broad_correlation` now shows reduced generic leakage (`generic_infra_ratio_top_k` improved from prior `0.75` to `0.5` on latest verified run)
  - still `WEAK` by policy for broad/generic asks (expected at current thresholding)
- **Scenario suite stability**
  - full scenario suite `all_pass=true`
  - artifact: `runtime/.run/motadata_behavior_validation.json`
- **Next active lane**
  - Debug usefulness refinement is the primary open engineering lane
  - authority wording refinement remains secondary

---

## Retrieval Redesign v1.1 (corrective pass)

This doc’s **baseline vs v1** tables remain the canonical empirical verdict for **v1**: not effective on the captured eval set (identical ask path sets; no measured uplift).

**v1.1** implemented:


| Area                       | Change                                                                                                                                                                                                         |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Hard post-fusion selection | Tighter default caps (`max_generic_infra_paths=2`, `max_distractor_paths=1`), minimum retained paths after caps (`min_paths_after_caps=3`), deterministic restore when the bundle would otherwise be too thin. |
| Registry-unavailable path  | `hard_filter_only` in `runtime/layer5/retrieval/fusion.py` so hard caps apply even when authority fusion is skipped (`runtime/ask_service/evidence_bridge.py`).                                                |
| Verifier metrics           | Canonical keys in JSON and stdout: `distractor_count_at_k`, `generic_infra_count_at_k`, `generic_infra_ratio`, `owner_in_top1`, `owner_in_top3`, `anchor_hit_rate_at_k` (legacy `*_top_k` aliases retained).   |


### v1.1 empirical run (Motadata, WSL)

Captured from `python3 runtime/scripts/motadata_behavior_verify.py --workspace-root "/home/harshil/Projects/Motadata" --repeat 2 --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json --print dev` (saved report: `motadata_behavior_validation.json`).

| Check | Result |
| ----- | ------ |
| Smoke | `repeat=2`, `stable=true`, `all_pass=true` |
| Scenario suite | `all_pass=true` |
| **`ask_broad_correlation` retrieval_metrics** | `distractor_count_at_k=0`, `generic_infra_count_at_k=6`, `generic_infra_ratio=0.75`, `owner_in_top1=false`, `owner_in_top3=false`, `anchor_hit_rate_at_k=1.0` |
| **`ask_symbol_anchored` retrieval_metrics** | `distractor_count_at_k=0`, `generic_infra_count_at_k=1`, `generic_infra_ratio=0.125`, `owner_in_top1=false`, `owner_in_top3=false`, `anchor_hit_rate_at_k=1.0` |
| Broad ask context bundle (8 paths) | Same ordered set as baseline/v1: `AvailabilityCorrelationEngine` → `MetricPoller` → `MotadataAppManager` → `ConfigDBServiceImpl` → `Notification` → `APIServer` → `LAMAIntegration` → `PolicyCacheServiceImpl` |
| Anchored ask context bundle (8 paths) | Same ordered set as baseline/v1: `AvailabilityCorrelationEngine` → `DiscoveryEngine` → `UIActionEventHandler` → `ObjectManager` → `APIServer` → `package-info` → `DependencyManager` → `DependencyQueryProcessor` |

**Verdict vs v1 on this eval set:** numeric ratios and path lists match the prior v1 capture; **no measured retrieval delta** for v1.1. Instrumentation is clearer (canonical metric keys); behavior outcome unchanged.

### Stage A v2 — A/B (`--export-stage-a`, WSL, 2026-04-15)

**Purpose:** Prove that turning Stage A **off** vs **on** changes retrieval inputs (not only client env — use HTTP `enable_stage_a_v2` via `motadata_behavior_verify.py --export-stage-a off|on`; context layer must include that handler, e.g. commit `70d0d6d`).

**Artifacts:** `runtime/.run/motadata_behavior_validation.stage_a_off.json` vs `stage_a_on.json`; diff: `python3 runtime/scripts/diff_motadata_behavior_validation.py …`.

**Observed (off → on):**

- **`stage_a`:** empty snapshot vs filled `lane_counts` + 20 `pool_paths` (telemetry path works).
- **`ask_broad_correlation` context bundle:** same 8 paths except **last slot** — `PolicyCacheServiceImpl` → `MicrosoftTeamsNotification`.
- **`ask_symbol_anchored` context bundle:** same 8 paths except **one slot** — `APIServer` → `availability.png`.
- **`ask_symbol_anchored` retrieval_metrics:** `generic_infra_ratio` **0.125 → 0.0**; `anchor_hit_rate_at_k` **1.0 → 0.875**.

**Takeaway:** A/B is valid (bundle and metrics move); movement is **small** (mostly one-path swaps in top-8), not a full broad-ask rescue — consistent with Stage A scope.

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


| Item                                   | Value                                                                                           |
| -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Workspace root                         | `/home/harshil/Projects/Motadata`                                                               |
| Repo commit (main eval / v1 artifacts) | `ad76853` (example; match your tree at run time)                                                |
| Baseline snapshot (pre–v1 comparison)  | `c3ca2a2` (historical baseline worktree; paths captured in `motadata_behavior_validation.json`) |
| Index state                            | `N/A (not captured)`                                                                            |
| Model                                  | `motadata-coder` (`/ml/training/pipeline/stage08/base_model`)                                   |
| Context layer URL                      | `http://127.0.0.1:8091` (healthy, HTTP 200)                                                     |
| Plan-Gate URL                          | `http://127.0.0.1:8089` (healthy, HTTP 200)                                                     |


## 2.2 Runs


| Run          | Description                                                                                                                                                                                                                               |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Baseline** | `repeat=2`, `stable=true`, `all_pass=true` from `baseline_run_verification.txt` and `motadata_behavior_validation.json`                                                                                                                   |
| **V1**       | `repeat=2`, `stable=true`, `all_pass=true` from `behaviour_run_verification_v1_true.txt` and `motadata_behavior_validation.v1_true.json`; scenarios file `docs/validation/motadata_aiops_behavior_scenarios.v1.json` with `all_pass=true` |
| **V1.1**     | `repeat=2`, `stable=true`, `all_pass=true`; same scenarios; report `motadata_behavior_validation.json` (WSL, 2026-04-15); canonical `retrieval_metrics` in scenario `actual_summary` |


**Baseline validity note:** baseline and v1 outputs are directly comparable in this report and are near-identical on observed behavior outputs.

---

# 3. Scenario Set

## 3.1 Utility scenarios


| ID  | Type  | Query                                                            | Notes                                                                      |
| --- | ----- | ---------------------------------------------------------------- | -------------------------------------------------------------------------- |
| U1  | Ask   | `How does alert correlation and enrichment work?`                | Scenario id: `ask_broad_correlation`; pass; `evidence_quality=WEAK`        |
| U2  | Debug | `Debug why incident enrichment might be skipped for some events` | Scenario id: `debug_explain_selection`; pass; `routing_mode=explain_debug` |
| U3  | Plan  | `N/A (shadow event in verifier)`                                 | Scenario id: `plan_pr_merge_shadow`; pass; decision `REFUSAL`              |


(Add rows as needed.)

## 3.2 Anchored evaluation set (high signal)


| ID  | Query                                                                                                        | Expected owner / class / path                                               |
| --- | ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| A1  | `Where is alert correlation implemented? Reference AvailabilityCorrelationEngine or AlertCorrelationEngine.` | `AlertCorrelationEngine` / `AvailabilityCorrelationEngine` mention expected |
| A2  | probe OBJECT_DOWN flow                                                                                       | `N/A (not run in this artifact)`                                            |
| A3  | incident creation logic                                                                                      | `N/A (not run in this artifact)`                                            |


---

# 4. Retrieval metrics (before vs after)

## 4.1 Owner accuracy


| Metric  | Baseline                  | V1                        | V1.1 |
| ------- | ------------------------- | ------------------------- | ---- |
| owner@1 | `1.00 (1/1 anchored ask)` | `1.00 (1/1 anchored ask)` | `Verifier: owner_in_top1=false` (same as v1 numerics) |
| owner@3 | `1.00 (1/1 anchored ask)` | `1.00 (1/1 anchored ask)` | `Verifier: owner_in_top3=false` (same as v1 numerics) |


*(Owner proxy used here: whether anchored ask (`ask_symbol_anchored`) reports the expected owner class/path in plan summary.)*

## 4.2 Noise / distractors


| Metric                       | Baseline                        | V1                                                                   | V1.1 |
| ---------------------------- | ------------------------------- | -------------------------------------------------------------------- | ---- |
| Avg distractor count (top-k) | `N/A in baseline JSON artifact` | `0` (`distractor_count_top_k` / `distractor_count_at_k`)              | `0` (`distractor_count_at_k`, smoke + `ask_broad_correlation`) |
| Generic infra ratio          | `N/A in baseline JSON artifact` | `≈0.75` broad ask; `≈0.125` anchored (`generic_infra_ratio_top_k`) | Same: **`0.75`** broad, **`0.125`** anchored (`generic_infra_ratio`) |


**Note:** v1.1 reports use canonical keys `distractor_count_at_k` and `generic_infra_ratio` (see v1.1 section). Older saved JSON may still show `*_top_k` alias fields.

## 4.3 Anchoring quality


| Metric                | Baseline                              | V1                                    | V1.1 |
| --------------------- | ------------------------------------- | ------------------------------------- | ---- |
| Anchor hit rate       | `1.00 for shown context_bundle items` | `1.00 for shown context_bundle items` | `anchor_hit_rate_at_k=1.0` (smoke + scenarios) |
| Correct package match | `PARTIAL`                             | `PARTIAL`                             | `PARTIAL` (unchanged) |


---

# 5. Evidence quality distribution


| Quality      | Baseline | V1  | V1.1 |
| ------------ | -------- | --- | ---- |
| STRONG       | `1`      | `1` | `1`  |
| WEAK         | `3`      | `3` | `3`  |
| INSUFFICIENT | `0`      | `0` | `0`  |
| NO_MATCH     | `0`      | `0` | `0`  |


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

#### V1.1

- Same eight paths and order as baseline/V1; `evidence_quality=WEAK` (`QUERY_TOO_GENERIC`); `generic_infra_ratio=0.75`, `distractor_count_at_k=0`.
- **Delta vs V1:** none (identical paths and headline metrics).

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

#### V1.1

- Same eight paths and order as baseline/V1; `evidence_quality=STRONG`; `generic_infra_ratio=0.125`, `distractor_count_at_k=0`.
- **Delta vs V1:** none (identical paths and headline metrics).

---

# 7. Debug quality comparison

### Example: `debug_explain_selection`


| Metric                  | Baseline | V1      | V1.1    |
| ----------------------- | -------- | ------- | ------- |
| References correct file | `YES`    | `YES`   | `YES`   |
| References control flow | `YES`    | `YES`   | `YES`   |
| Concrete vs generic     | `MIXED`  | `MIXED` | `MIXED` |


---

# 8. Plan / code usefulness


| Metric                           | Baseline  | V1                                                                                | V1.1 |
| -------------------------------- | --------- | --------------------------------------------------------------------------------- | ---- |
| Grounded file selection          | `PARTIAL` | `PARTIAL`                                                                         | `PARTIAL` |
| Safe scope definition            | `YES`     | `YES` (`governance_posture=PLAN_ONLY`, plan `decision=REFUSAL`, execute governed) | `YES` (same) |
| Hallucination risk (qualitative) | `MEDIUM`  | `MEDIUM` on broad asks (`WEAK` + generic retrieval set)                           | `MEDIUM` (unchanged) |


---

# 9. Utility scenario results


| Scenario                       | Baseline                                            | V1                                                  | V1.1                                                 | Delta vs V1 |
| ------------------------------ | --------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------- | ----------- |
| U1 (`ask_broad_correlation`)   | `PASS` (`evidence_quality=WEAK`)                    | `PASS` (`evidence_quality=WEAK`)                    | `PASS` (`evidence_quality=WEAK`; metrics as §v1.1)    | No change   |
| U2 (`debug_explain_selection`) | `PASS` (`routing_mode=explain_debug`, has summary)  | `PASS` (`routing_mode=explain_debug`, has summary)  | `PASS` (same)                                       | No change   |
| U3 (`plan_pr_merge_shadow`)    | `PASS` (`decision_response.v0.1`, decision present) | `PASS` (`decision_response.v0.1`, decision present) | `PASS` (same)                                       | No change   |


Additional scenario results in same run:

- `ask_symbol_anchored`: `PASS`, `evidence_quality=STRONG`
- `code_echo_probe`: `PASS`, `outcome=EXECUTED`
- `agent_no_route`: `PASS`, `/v0/agent=404`, assist layer present

---

# 10. Qualitative observations

### Improvements

- **v1.1:** clearer numeric retrieval metrics in reports (`distractor_count_at_k`, `generic_infra_ratio`, etc.).
- No clear **retrieval or usefulness** improvements vs baseline/v1 on this scenario set.

### Regressions

- No direct regression observed in contracts (all pass), but retrieval top-k remains noisy in broad asks.

### Neutral

- System governance behavior (`PLAN_ONLY`, plan refusal, safe execute posture) remains unchanged.
- Anchored ask still reports owner and passes scenario expectations in baseline, v1, and v1.1 runs.
- **v1.1** path sets and ratios match v1 on the same Motadata snapshot (no new signal of uplift).

---

# 11. Failure analysis


| Scenario                  | Failure type                                                   | Root cause (retrieval / grounding / reasoning)                                 |
| ------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `ask_broad_correlation`   | Weak evidence quality (`WEAK`) persists                        | retrieval + grounding (query generic; noisy top-k dominates)                   |
| `debug_explain_selection` | Answer partly generic in both runs                             | reasoning + grounding (selection text is directive, not concrete code snippet) |
| Baseline collection       | Earlier environment friction (GPU, worktrees, commit mismatch) | resolved for later runs; baseline JSON in repo is valid for comparison         |


---

# 12. Key insights

- Architecture/contract lane is stable in both captured runs (`all_pass=true`, `stable=true`, scenario suite pass).
- Utility lane pattern is unchanged across captured baseline and v1 (anchored ask `STRONG`, broad ask `WEAK`).
- Scenario-level context bundle path sets are identical between baseline and v1 for both `ask_broad_correlation` and `ask_symbol_anchored`.
- **v1.1** repeats the same identity: path sets and verifier headline metrics match v1 on the captured WSL run.

---

# 13. Decision


| Question                          | Answer                                        |
| --------------------------------- | --------------------------------------------- |
| Did retrieval improve?            | NO (no measurable delta in current artifacts) |
| Is developer usefulness improved? | NO (no measurable delta in current artifacts) |
| Ready for closure (v1)?           | NO                                            |
| Did **v1.1** improve retrieval vs v1 on this eval set? | NO (same paths, same `generic_infra_ratio` / distractor counts) |
| Ready for closure (v1.1)?       | NO (measurement improved; outcome unchanged)   |


---

# 14. Next actions

## v1.1 empirical re-run

**Done** — see **Retrieval Redesign v1.1 → v1.1 empirical run** above. To reproduce:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/home/harshil/Projects/Motadata" \
  --repeat 2 \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.v1_1.json
```

Inspect `retrieval_metrics` on smoke `export_evidence` / `query` and scenario `actual_summary`: `distractor_count_at_k`, `generic_infra_ratio`, `owner_in_top1`, `owner_in_top3`.

## If future changes still show no path-set or metric delta (as v1.1 did here)

- Treat candidate generation (lexical ceiling) as the next bottleneck, not another broad redesign.
- Optionally add **developer utility** run: `--utility-scenarios docs/validation/motadata_developer_utility_scenarios.v1.json`.

## Longer term (out of v1.1 scope)

- Snippet / debug prose quality, stronger owner enforcement, richer priors — only after v1.1 numbers justify it.

---

# 15. Final verdict

Retrieval redesign v1 is:

- [ ] Successful
- [ ] Partially successful
- [x] Not effective

**v1.1 corrective pass** (hard caps + verifier metrics):

- [ ] Successful
- [ ] Partially successful
- [x] Not effective on **retrieval outcome** for this eval set (instrumentation improved; paths and headline ratios unchanged vs v1)

**Justification (evidence-only):**

- Captured baseline and v1 artifacts show no measurable delta on primary reported metrics (scenario pass, broad ask quality, anchored ask quality, top paths).
- Broad ask remains `WEAK` with noisy context bundle in both runs.
- For both ask scenarios, selected context bundle path lists are exactly identical between baseline and v1 in current run artifacts.
- **v1.1** WSL run: same ordered path sets as v1 for `ask_broad_correlation` and `ask_symbol_anchored`; `generic_infra_ratio` still `0.75` / `0.125` respectively; `distractor_count_at_k` still `0`.
- Therefore: implementation exists, but measured developer-outcome improvement is not demonstrated in this evaluation set (including v1.1).

---

