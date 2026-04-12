# Debug path validation report

**Source artifacts (authoritative JSON):** `~/Projects/Backend-Validation-artifacts/`

| Scenario label (capture) | Response JSON | Evidence JSON | Ask request JSON |
|--------------------------|---------------|---------------|------------------|
| Strong (Capture-1) | `ask_capture_1_strong.json` | `ask_capture_1_strong.evidence.json` | `ask_capture_1_strong.ask_v1.json` |
| Weak (Capture-2) | `ask_capture_2_weak.json` | `ask_capture_2_weak.evidence.json` | `ask_capture_2_weak.ask_v1.json` |
| Insufficient (Capture-3) | `ask_capture_3_insufficient.json` | `ask_capture_3_insufficient.evidence.json` | `ask_capture_3_insufficient.ask_v1.json` |
| No match (Capture-4) | `ask_capture_4_no_match.json` | `ask_capture_4_no_match.evidence.json` | `ask_capture_4_no_match.ask_v1.json` |
| EXPLAIN_DEBUG / vLLM (Capture-5) | `ask_capture_explain_debug_vllm.json` | `ask_capture_explain_debug_vllm.evidence.json` | `ask_capture_explain_debug_vllm.ask_v1.json` |

Lab notes: `Capture-5.md` (terminal + JSON transcript).

**Runbook nominal expectations** (from [DEBUG_PATH_VALIDATION_RUNBOOK.md](../DEBUG_PATH_VALIDATION_RUNBOOK.md) “Query set”): typical `evidence_quality` targets Strong → `STRONG`, Weak → `WEAK`, Insufficient → `INSUFFICIENT`, No match → `NO_MATCH`. **Observed values below are taken only from the saved Plan-Gate responses.**

**Shared bundle metadata (Captures 1–5):** `evidence_bundle.schema_hint` = `layer5.evidence_bundle.v1`; `workspace_identity_hash` = `332faea4f80388375ab45b49336d62f9abd4b15253333513c198711f32172c95`; `evidence_bundle.canonical_root` = `/root/Harshil-PoCs/Motadata` (identity string from export; not used here to infer server filesystem access).

---

## 1 — Capture-1 (labeled “Strong”)

### 1. Scenario

| Field | Value |
|--------|--------|
| **Query** | `Explain how alert correlation engine works in this repo` |
| **Expected intent** (runbook / design) | Debug / code-oriented phrasing (not specified as enum in runbook) |
| **Expected quality** (runbook “typical”) | `STRONG` |
| **request_id** | `5056a894-f93e-4b39-9f9f-3c283f68e544` |

### 2. Evidence

**top-k files** (`context_bundle.files`, order as returned):

- `motadata/src/test/resources/log_reduce.log`
- `motadata/test-plugin-metrics/sharepoint_online_poll.json`
- `motadata/test-plugin-metrics/oracle_index_poll.json`
- `motadata/test-plugin-metrics/snmp_interface_poll.json`
- `motadata/test-plugin-metrics/mysql_index_poll.json`
- `motadata/db-files/report-templates/js/highcharts.js`
- `motadata/test-plugin-metrics/snmp_device_discovery.json`
- `motadata/src/test/java/com/mindarray/visualization/TestVisualizationManager.java`

**Classification (path-based, same rules as runbook helper):** mix of log fixture, plugin-metric JSON fixtures, third-party JS (`highcharts.js`), and one Java test file — not predominantly `core_aiops_code` in this top-k.

### 3. Metadata

| Field | Value |
|--------|--------|
| `intent_type` | `GENERIC_INTENT` |
| `evidence_quality` | `INSUFFICIENT` |
| `quality_reasons` | `DIVERSITY_VIOLATION`, `NOISE_DOMINATED`, `QUERY_TOO_GENERIC` |
| `dominance_metrics` | `top_k_size`: 8; `core_code_in_top_k_pct`: 0.0; `code_in_top_k_pct`: 0.125; `noise_in_top_k_pct`: 0.875; `core_in_top_3_count`: 0; `max_consecutive_noise`: 5.0 |
| `policy_version` | `quality_gate.v1` |

### 4. Response behavior

- `governance_posture`: `PLAN_ONLY`; `execution`: false.
- `plan_summary.steps`: **[]** (empty).
- `plan_summary.notes`: `["No context files matched enough grounded evidence; plan steps are ungrounded."]`
- `ui.title`: `Grounding blocked (PLAN ONLY)`.
- **Reasoning:** blocked for grounded plan steps (no steps emitted).

### 5. Validation checks

| Check | Result |
|--------|--------|
| vLLM used | **No** — `explain_debug` absent in response (null / not present in saved JSON). |
| No hidden repo access (evidence path) | **Yes** — `context_resolution.no_repo_filesystem`: **true**; `context_source`: `layer5.evidence_bundle.v1`; `evidence_first_meta.no_context_engine`: **true**. |
| Quality gate behavior | Matches recorded metadata: `INSUFFICIENT` with empty plan steps. |
| No hallucination | No fabricated code explanation in structured output; grounding explicitly refused. |

### 6. Verdict

- **Verdict:** **FAIL** *relative to runbook nominal label* (“Strong” / typical `STRONG`): observed `evidence_quality` is **`INSUFFICIENT`**, not `STRONG`.
- **Reason:** Recorded `metadata` and empty `plan_summary.steps` contradict the nominal “strong debug” expectation for this scenario name.

---

## 2 — Capture-2 (labeled “Weak”)

### 1. Scenario

| Field | Value |
|--------|--------|
| **Query** | `Why this engine is slow?` |
| **Expected intent** (runbook / design) | Weak debug |
| **Expected quality** (runbook “typical”) | `WEAK` |
| **request_id** | `db6a02d5-1548-43bb-b622-3180c0e8ed25` |

### 2. Evidence

**top-k files:**

- `motadata/test-plugin-metrics/cisco_ucs_chassis_poll.json`
- `motadata/db-files/report-templates/js/highcharts.js`
- `motadata/test-plugin-metrics/cisco_ucs_rack_mount_poll.json`
- `motadata/test-plugin-metrics/cisco_ucs_fabric_interconnect_poll.json`
- `motadata/db-files/report-templates/js/accessibility.js`
- `motadata/src/test/resources/log_reduce.log`
- `motadata/test-plugin-metrics/linux_disk_poll.json`
- `motadata/src/test/resources/discovery-parameters.json`

**Classification:** plugin JSON fixtures, vendor/report JS, test resources — dominant noise/fixture pattern per `dominance_metrics`.

### 3. Metadata

| Field | Value |
|--------|--------|
| `intent_type` | `GENERIC_INTENT` |
| `evidence_quality` | `INSUFFICIENT` |
| `quality_reasons` | `DIVERSITY_VIOLATION`, `NOISE_DOMINATED`, `QUERY_TOO_GENERIC` |
| `dominance_metrics` | `top_k_size`: 8; `core_code_in_top_k_pct`: 0.0; `code_in_top_k_pct`: 0.25; `noise_in_top_k_pct`: 0.75; `core_in_top_3_count`: 0; `max_consecutive_noise`: 3.0 |
| `policy_version` | `quality_gate.v1` |

### 4. Response behavior

- `governance_posture`: `PLAN_ONLY`; `execution`: false.
- `plan_summary.steps`: **[]** (empty).
- `plan_summary.notes`: `["No context files matched enough grounded evidence; plan steps are ungrounded."]`
- `ui.title`: `Grounding blocked (PLAN ONLY)`.

### 5. Validation checks

| Check | Result |
|--------|--------|
| vLLM used | **No** — `explain_debug` absent. |
| No hidden repo access | **Yes** — `context_resolution.no_repo_filesystem`: **true**. |
| Quality gate behavior | `INSUFFICIENT`; empty steps. |
| No hallucination | No grounded plan steps produced. |

### 6. Verdict

- **Verdict:** **FAIL** *relative to runbook nominal label* (typical `WEAK`): observed **`INSUFFICIENT`**, not `WEAK`.
- **Reason:** Metadata shows `INSUFFICIENT` and same blocking pattern as scenario 1; no `WEAK` label in the saved response.

---

## 3 — Capture-3 (labeled “Insufficient”)

### 1. Scenario

| Field | Value |
|--------|--------|
| **Query** | `Fix this issue` |
| **Expected intent** (runbook / design) | Insufficient / block |
| **Expected quality** (runbook “typical”) | `INSUFFICIENT` |
| **request_id** | `58ab5cb3-21d3-4ef8-b908-64cab12cfeb8` |

### 2. Evidence

**top-k files:**

- `motadata/db-files/report-templates/js/highcharts.js`
- `motadata/db-files/report-templates/js/accessibility.js`
- `motadata/db-files/counters-description.json`
- `motadata/test-plugin-metrics/sap_maxdb_command_monitor_poll.json`
- `motadata/src/main/java/com/mindarray/integration/AtlassianJiraIntegration.java`
- `motadata/db-files/report-templates/js/exporting.js`
- `motadata/src/main/java/com/mindarray/api/AbstractAPI.java`
- `motadata/src/main/java/com/mindarray/api/Agent.java`

**Classification:** mix of `db-files` JS, JSON, plugin poll JSON, and several `src/main/java` files (integration/API).

### 3. Metadata

| Field | Value |
|--------|--------|
| `intent_type` | `GENERIC_INTENT` |
| `evidence_quality` | `STRONG` |
| `quality_reasons` | `QUERY_TOO_GENERIC` |
| `dominance_metrics` | `top_k_size`: 8; `core_code_in_top_k_pct`: 0.0; `code_in_top_k_pct`: 0.75; `noise_in_top_k_pct`: 0.125; `core_in_top_3_count`: 0; `max_consecutive_noise`: 1.0 |
| `policy_version` | `quality_gate.v1` |

### 4. Response behavior

- `governance_posture`: `PLAN_ONLY`; `execution`: false.
- `plan_summary.steps` (4 steps), first step text (verbatim from JSON):  
  `Open motadata/db-files/report-templates/js/highcharts.js and scan for logic related to "issue".`  
  (Additional steps reference `accessibility.js`, `counters-description.json`, repository search for `"issue"`, trace control flow — full list in `ask_capture_3_insufficient.json`.)
- `ui.title`: `Evidence-driven Plan (PLAN ONLY)`.

### 5. Validation checks

| Check | Result |
|--------|--------|
| vLLM used | **No** — `explain_debug` absent. |
| No hidden repo access | **Yes** — `context_resolution.no_repo_filesystem`: **true**. |
| Quality gate behavior | Recorded label is **`STRONG`** with reason `QUERY_TOO_GENERIC` — **conflicts** with runbook nominal `INSUFFICIENT` for this scenario. |
| No hallucination | Plan steps are generic search/read instructions keyed off token `"issue"`; no claim that a specific bug was identified. |

### 6. Verdict

- **Verdict:** **FAIL** *relative to runbook nominal label* (typical `INSUFFICIENT`): observed **`STRONG`** with plan steps.
- **Reason:** Saved `metadata.evidence_quality` is `STRONG`, not `INSUFFICIENT`.

---

## 4 — Capture-4 (labeled “No match”)

### 1. Scenario

| Field | Value |
|--------|--------|
| **Query** | `Explain quantumHandler in this repo` |
| **Expected intent** (runbook / design) | Symbol/code ask; no match expected |
| **Expected quality** (runbook “typical”) | `NO_MATCH` |
| **request_id** | `3b7ff117-c007-477c-99bf-41081eb3cf9e` |

### 2. Evidence

**top-k files:**

- `motadata/test-plugin-metrics/sharepoint_online_poll.json`
- `motadata/test-plugin-metrics/oracle_index_poll.json`
- `motadata/test-plugin-metrics/snmp_interface_poll.json`
- `motadata/test-plugin-metrics/mysql_index_poll.json`
- `motadata/db-files/report-templates/js/highcharts.js`
- `motadata/src/test/resources/log_reduce.log`
- `motadata/test-plugin-metrics/snmp_device_discovery.json`
- `motadata/src/test/java/com/mindarray/visualization/TestVisualizationManager.java`

**Classification:** same pattern as scenario 1 — fixtures, vendor JS, log, test Java; no path containing `quantumHandler` in the listed `relative_path` values.

### 3. Metadata

| Field | Value |
|--------|--------|
| `intent_type` | `CODE_INTENT` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `DIVERSITY_VIOLATION`, `LOW_CODE_RATIO`, `LOW_CORE_RATIO`, `NOISE_DOMINATED`, `NO_CORE_IN_TOP3`, `NO_SYMBOL_MATCH` |
| `dominance_metrics` | `top_k_size`: 8; `core_code_in_top_k_pct`: 0.0; `code_in_top_k_pct`: 0.125; `noise_in_top_k_pct`: 0.875; `core_in_top_3_count`: 0; `max_consecutive_noise`: 4.0 |
| `policy_version` | `quality_gate.v1` |

### 4. Response behavior

- `governance_posture`: `PLAN_ONLY`; `execution`: false.
- `plan_summary.steps` (4 steps), first step (verbatim):  
  `Open motadata/test-plugin-metrics/sharepoint_online_poll.json and scan for logic related to "quantumhandler".`
- `plan_summary.notes`: `["Evidence quality is WEAK; plan/explanation may be incomplete."]`
- `ui.title`: `Evidence-driven Plan (PLAN ONLY)`.

### 5. Validation checks

| Check | Result |
|--------|--------|
| vLLM used | **No** — `explain_debug` absent. |
| No hidden repo access | **Yes** — `context_resolution.no_repo_filesystem`: **true**. |
| Quality gate behavior | `WEAK` with **`NO_SYMBOL_MATCH`** in `quality_reasons` — **not** `NO_MATCH`. |
| No hallucination | Plan does not assert that `quantumHandler` exists in the repo; steps are search-oriented. |

### 6. Verdict

- **Verdict:** **FAIL** *relative to runbook nominal label* (typical `NO_MATCH`): observed **`WEAK`**, not `NO_MATCH`.
- **Reason:** Recorded `evidence_quality` is `WEAK`; symbol miss is reflected via `NO_SYMBOL_MATCH` in reasons.

---

## 5 — Capture-5 (EXPLAIN_DEBUG / model reasoning)

### 1. Scenario

| Field | Value |
|--------|--------|
| **Query** | `Explain the flow of AlertCorrelationEngine class and how alerts are grouped` |
| **Request** | `task_type`: `EXPLAIN_DEBUG`; `selected_file`: `motadata/test-plugin-metrics/sap_maxdb_command_monitor_poll.json` (rank-0 entry from export); `client_context.selection`: snippet text from that entry (`ask_capture_explain_debug_vllm.ask_v1.json`). |
| **request_id** | `ee1aaadf-abe4-46de-b0c8-3eb41ca2fa67` |

### 2. Evidence (top-k paths)

From `ask_capture_explain_debug_vllm.json` `context_bundle.files` (order as returned):  
`motadata/test-plugin-metrics/sap_maxdb_command_monitor_poll.json`, `motadata/test-plugin-metrics/cisco_ucs_fabric_interconnect_poll.json`, `motadata/test-plugin-metrics/sharepoint_online_poll.json`, `motadata/src/main/resources/entity-schemas/flow-domain-mappers.json`, `motadata/src/main/resources/entity-schemas/compliance-rules.json`, `motadata/db-files/counters-description.json`, `motadata/src/main/resources/entity-schemas/config-templates.json`, `motadata/src/main/java/com/mindarray/store/ObjectConfigStore.java`.

### 3. Metadata

| Field | Value |
|--------|--------|
| `intent_type` | `CODE_INTENT` |
| `evidence_quality` | `WEAK` |
| `quality_reasons` | `DIVERSITY_VIOLATION`, `LOW_CODE_RATIO`, `LOW_CORE_RATIO`, `NO_CORE_IN_TOP3`, `NO_SYMBOL_MATCH` |
| `dominance_metrics` | `top_k_size`: 8; `core_code_in_top_k_pct`: 0.0; `code_in_top_k_pct`: 0.125; `noise_in_top_k_pct`: 0.375; `core_in_top_3_count`: 0; `max_consecutive_noise`: 3.0 |
| `policy_version` | `quality_gate.v1` |

### 4. Response behavior

- `governance_posture`: `PLAN_ONLY`; `execution`: false.
- `context_resolution.no_repo_filesystem`: **true**.
- **`explain_debug` present** (no `error` key): includes `summary`, `logic_flow`, `likely_bug_risk`, `evidence`, `confidence_limits`. The `summary` states the selected snippet does not contain `AlertCorrelationEngine` and asks for relevant Java source for a precise answer — i.e. output is hedged to weak evidence, not a fabricated class walkthrough.
- `plan_summary.steps`: `["Explain/debug analysis completed; see structured output above."]`
- `plan_summary.notes`: `["Evidence quality is WEAK; plan/explanation may be incomplete."]`

### 5. Validation checks

| Check | Result |
|--------|--------|
| `explain_debug` populated | **Yes** — structured fields present; **no** `explain_debug.error`. |
| vLLM / HTTP trace in JSON | **Not in payload** — the artifact does not include raw `/v1/chat/completions` logs; success is inferred from structured output without `error` per `runtime/ask_service/reasoner.py` behavior. |
| No hidden repo access | **Yes** — `no_repo_filesystem`: true. |
| Quality gate | **WEAK**, not blocked; reasoner branch allowed. |

### 6. Verdict

- **Model invocation (closure):** **PASS** — `EXPLAIN_DEBUG` request; response includes **`explain_debug`** with structured content.
- **Retrieval vs query:** The class name was **not** in the rank-0 snippet; model output correctly reflects **low grounding** (`confidence_limits` in response). Improving class-level demos is a **retrieval / selection** follow-up, not a failure of the model-invocation *mechanism*.

---

## Why `explain_debug` / vLLM did not appear (code contract)

This is **not** inferred; it follows Plan-Gate behavior in `runtime/ask_service/v1_ingest.py`:

1. **Quality gate blocks reasoning:** If `quality.blocked` is true (`evidence_quality` is `INSUFFICIENT` or `NO_MATCH`), the handler returns immediately with `explain_debug: null` and no model call.
2. **Default path is template planning:** If `task_type` is omitted or not `EXPLAIN_DEBUG`, the handler uses `PlanOnlyPlanner` only — no `explain_debug`.
3. **EXPLAIN_DEBUG branch:** `explain_debug()` (which POSTs to vLLM at `MOTADATA_EXPLAIN_VLLM_URL` + `/v1/chat/completions`) runs only when **all** hold: **not** blocked, `task_type == "EXPLAIN_DEBUG"`, `selected_file` set, and `(selection text or non-empty bundle items)`.

The saved **`ask_capture_[1-4]_*.ask_v1.json`** requests omit `task_type` / `selected_file` / `client_context` (equivalent to `general`), so Captures **1–4** **never exercised** the model reasoning branch — regardless of retrieval quality. **Capture-5** uses `EXPLAIN_DEBUG` (see §5).

---

## Model invocation validation (closure checklist)

**Purpose:** Prove model-backed reasoning when the product requires it, alongside “no hidden repo access.”

| Scenario (artifact) | `explain_debug` present | Model used (from response) | Evidence |
|---------------------|-------------------------|----------------------------|----------|
| Capture-1 (`ask_capture_1_strong.json`) | **No** | **No** | No `explain_debug` key; request had no `EXPLAIN_DEBUG` fields (`ask_capture_1_strong.ask_v1.json`). |
| Capture-2 (`ask_capture_2_weak.json`) | **No** | **No** | Same. |
| Capture-3 (`ask_capture_3_insufficient.json`) | **No** | **No** | Same. |
| Capture-4 (`ask_capture_4_no_match.json`) | **No** | **No** | Same. |
| Capture-5 (`ask_capture_explain_debug_vllm.json`) | **Yes** | **Yes** (structured output; **no** `explain_debug.error`) | `task_type` `EXPLAIN_DEBUG` in `ask_capture_explain_debug_vllm.ask_v1.json`; response includes `summary` / `logic_flow` / etc. Raw HTTP trace to vLLM is **not** in the JSON artifact. |

**Optional follow-up:** Attach Plan-Gate or vLLM server logs for `request_id` `ee1aaadf-abe4-46de-b0c8-3eb41ca2fa67` if auditors require HTTP-level proof beyond the response body.

Runbook: [DEBUG_PATH_VALIDATION_RUNBOOK.md](../DEBUG_PATH_VALIDATION_RUNBOOK.md) — **§2.4 Model invocation proof (`EXPLAIN_DEBUG` + vLLM)**.

---

## Revised overall verdict (closure-oriented)

| Check | Status | Evidence in this report |
|-------|--------|-------------------------|
| No hidden repo access (`no_repo_filesystem`) | **PASS** | All five capture JSON responses: `true`. |
| Truthfulness / gating (blocked vs plan, no fabricated symbol claims in structured output) | **PASS** | Per-scenario sections; Capture 4 search-oriented steps. |
| Deterministic gating / policy | **PASS** | `metadata.policy_version` and recorded reasons. |
| **Model invocation (vLLM / `explain_debug`)** | **PASS** | Capture-5: `explain_debug` populated without `error`; `EXPLAIN_DEBUG` in request (`ask_capture_explain_debug_vllm.json`). |
| Runbook nominal quality labels vs observed | **FAIL** | Documented in §1–4 verdicts. |

**Closure status:** **Model invocation (response-level proof)** — **closed** for Capture-5. **HTTP / log-level proof** to vLLM remains optional if stakeholders require it. Repo-access and evidence-first path are validated across Captures 1–5.

---

## Overall debug path verdict (original scope)

| Mechanism | Evidence from captures |
|-----------|-------------------------|
| Evidence-first Ask (`layer5.evidence_bundle.v1`) | Captures 1–5: `context_resolution.context_source` = `layer5.evidence_bundle.v1`, `no_repo_filesystem` = **true**. |
| vLLM / `explain_debug` on this path | Capture-5 includes structured `explain_debug` (§5). Captures 1–4 used `general` only (see **Model invocation validation**). |
| Alignment with runbook **nominal** quality labels (Strong / Weak / Insufficient / No match) | **No** — all four differ from the runbook “typical” row (see per-scenario verdicts). |

**Overall verdict (vs runbook nominal expectations):** **FAIL** — observed `evidence_quality` values do not match the four named scenario targets.

**Violations of handbook / runbook guarantees (as stated in [DEBUG_PATH_VALIDATION_RUNBOOK.md](../DEBUG_PATH_VALIDATION_RUNBOOK.md)):**

- The runbook lists **typical** `evidence_quality` targets per query; **this execution did not reproduce those labels** on the captured GPU/WSL stack and workspace snapshot.
- The runbook does not guarantee those labels; the mismatch is therefore a **validation outcome**, not proof that `no_repo_filesystem` was false (it was **true** in all five capture JSON files).

**Note:** `Capture-*.md` files may include shell stderr (e.g. `DeprecationWarning`) and `[INFO]` lines; **field values in this report are aligned to the `ask_capture_*.json` files** where they differ.
