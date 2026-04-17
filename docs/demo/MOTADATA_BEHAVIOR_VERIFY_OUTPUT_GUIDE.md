# Motadata behavior verifier output — plain-language guide

This document walks through what you see when you run `runtime/scripts/motadata_behavior_verify.py` with `--print dev`, and how that relates to the saved report **`runtime/.run/motadata_behavior_validation.json`** (or whatever path you pass to `--out`).

**Related files**

- Verifier script: `runtime/scripts/motadata_behavior_verify.py`
- Scenario definitions (expected vs actual): `docs/validation/motadata_aiops_behavior_scenarios.v1.json`
- Quality gates (retrieval / evidence rules): `docs/validation/motadata_evidence_quality_policy.v1.json`
- Full operator runbook: `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`

---

## 1) Two outputs at once

Every run produces:

1. **Text on the terminal** — human-readable, especially rich with `--print dev`.
2. **A JSON file** — the machine-readable “source of truth” for pass/fail and for comparing runs over time.

Default JSON path in the demobook:

`runtime/.run/motadata_behavior_validation.json`

Open that file after a run to see the same story in structured form: top-level keys include `all_pass`, `smoke`, `scenario_suite`, `quality_policy`, `workspace_root`, `timestamp_utc`.

---

## 2) Important: the first `all_pass` line can mislead you in `--print dev`

When you use **`--print dev`**, the script prints a header like:

```text
repeat: 2  stable: True  all_pass: True
```

That header is built from the **smoke pipeline only** (the repeated “full stack” check). It does **not** include the scenario suite result in that printed line.

So you can see:

- Header: `all_pass: True` (smoke only)
- Later: `=== Scenario suite ===` … `all_pass: False`

The **real** overall result is in the JSON file’s top-level **`all_pass`**, which combines smoke **and** scenarios (and utility scenarios if you use them). The process **exit code** also follows that combined value: `0` only if combined `all_pass` is true.

**Rule of thumb:** trust **`motadata_behavior_validation.json` → `all_pass`** and **`echo $?`** after the command finishes, not only the dev header line.

---

## 3) What the verifier is doing (big picture)

One invocation does two different jobs when you pass **`--scenarios`** and you are **not** using `--scenarios-only`:

### A) Smoke runs (`repeat` times)

A **smoke run** is one end-to-end pass through the live system. It roughly does:

1. Health checks (Context Layer, Plan-Gate, vLLM where required).
2. **Query path:** export evidence from the Context Layer, then **Ask** on Plan-Gate with evidence-first v1.
3. **Debug path:** a separate **EXPLAIN_DEBUG** call (different from the Ask query).
4. **Plan path:** `POST /v0/plan` with a small synthetic “PR merge” style event.
5. **Code path:** `POST /v0/execute` with a safe probe command (same idea as scenarios, but wired inside smoke).
6. **Agent semantics:** checks that there is no real public agent route the way older designs might have had, while Ask still carries assist metadata.

The script runs that whole sequence **`--repeat`** times (you used `2`). That answers: “If I run the same checks twice, do I get the same kind of result?”

### B) Scenario suite (from the JSON file you passed)

After smoke, it runs each **row** in `motadata_aiops_behavior_scenarios.v1.json`. Each row is a small contract test: “for this capability, the live system must satisfy these expectations.”

The quality policy file tightens some Ask rows (anchors, owner in top-k, etc.) when you pass **`--quality-policy`**.

**Concrete queries, commands, and fields copied from the scenario JSON:** see [§3.5](#scenario-json-queries).

---

<a id="scenario-json-queries"></a>

## 3.5) Real queries and payloads from the scenario JSON (and smoke defaults)

The canonical scenario pack lives at **`docs/validation/motadata_aiops_behavior_scenarios.v1.json`**. Each `scenarios[]` row is one contract test. Below are the **exact strings and fields** from that file (schema version `motadata_aiops_behavior_scenarios.v1`), plus how **smoke** relates when you do not override CLI flags.

### File-level defaults (from the JSON)

| Field | Value |
|--------|--------|
| `defaults.top_k` | `8` (used when a scenario does not override `top_k`) |

### Smoke run (CLI) — default Ask + EXPLAIN_DEBUG strings

If you do **not** pass `--query` or `--debug-query`, `motadata_behavior_verify.py` uses these defaults (they are aligned with the verification guide and overlap the scenario pack wording):

| CLI flag | Default string |
|----------|------------------|
| `--query` | `How does alert correlation and enrichment work?` |
| `--debug-query` | `Debug why incident enrichment might be skipped` |

So the **dev view** “Ask” and “EXPLAIN_DEBUG” blocks you see in smoke runs are driven by those defaults unless you override them. The first scenario row **`ask_broad_correlation`** uses almost the same Ask text (see below).

### Ask scenarios — `query` text pinned in JSON

Each row exports evidence with `POST /v1/export_evidence` using this **`query`**, then builds `ask_request.v1.0` and calls **`POST /v1/ask`**. The verifier then checks `expect` (posture, `ask_path`, plan steps, optional text anchors, owner gates, etc.).

| `id` | `query` (exact from JSON) |
|------|----------------------------|
| `ask_broad_correlation` | `How does alert correlation and enrichment work?` |
| `ask_symbol_anchored` | `Where is alert correlation implemented? Reference AvailabilityCorrelationEngine or AlertCorrelationEngine.` |
| `ask_anchor_owner_gate` | `Explain AlertCorrelationEngine behavior for alert correlation in the product.` |
| `ask_anchor_owner_top1` | `Where is alert correlation implemented? Focus on AvailabilityCorrelationEngine.start.` |
| `ask_api_request_routing_owner` | `Where is API request routing handled in Motadata?` |
| `ask_servicenow_sync_owner` | `Where is ServiceNow incident synchronization implemented?` |

**What `expect` means (short):** each row lists required **`governance_posture`**, **`ask_path`** (`v1_evidence`), **`execution: false`**, **`min_plan_steps`**, and sometimes **`text_contains_any`** (answer must mention at least one substring) or **authority / Stage A** gates (`require_owner_in_top3`, `require_stage_a_owner_injected_min`, etc.). The full object per row is in the JSON file.

### Debug scenarios — `query`, `debug_query`, `selected_file`, `selection`

These rows call **`POST /v1/ask`** with **`task_type=EXPLAIN_DEBUG`** (and evidence bundle), using the scenario’s fields. The verifier checks `expect` (e.g. `routing_mode`, required keys, honesty when the file is missing).

| `id` | `query` | `debug_query` | `selected_file` | `selection` |
|------|---------|---------------|-----------------|-------------|
| `debug_explain_selection` | `How does alert correlation and enrichment work?` | `Debug why incident enrichment might be skipped for some events` | `motadata/src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java` | `Trace enrichment and correlation paths; list likely failure points.` |
| `debug_explain_missing_selected_file` | `Why might enrichment be skipped?` | `Explain failure points for a file that is not in retrieved context` | `motadata/src/main/java/com/mindarray/aiops/doesnotexist/MissingEngine.java` | `Trace branch and enrichment behavior.` |

### Plan scenario — `plan_pr_merge_shadow`

This row has **no** natural-language `query` in the JSON. The verifier sends a **fixed synthetic** `plan_request.v0.1` body (shadow PR-merge style `ide_event`) to **`POST /v0/plan`**. The JSON only pins:

- `expect.schema_version`: `decision_response.v0.1`
- `expect.decision_present`: true

So any **non-empty** governed decision (including `REFUSAL`) can satisfy **`decision_present`**.

### Code scenario — `code_echo_probe`

| Field | Value (exact from JSON) |
|--------|-------------------------|
| `command` | `echo motadata-execute-probe` |
| `expect.outcome` | `EXECUTED` |
| `expect.executed` | `true` |

The verifier posts an **`execute_request.v0.1`** with that `command` and your `--workspace-root` as `repo_root`. If your environment returns **`BLOCKED`** instead of **`EXECUTED`**, the scenario **fails** even when the HTTP response is valid — that is a **contract mismatch**, not a transport error (see section 11 in this guide).

### Agent scenario — `agent_no_route`

The JSON row has **no** `query` field. The verifier implementation uses:

- **Export query:** `How does alert correlation and enrichment work?` (hard-coded default when `query` is absent)
- **Ask body `query`:** `smoke` when the scenario omits `query` (see verifier source for `agent` capability)

`expect` requires **`agent_route_404: true`** and **`assist_layer_on_ask: true`**.

### Where this appears in `motadata_behavior_validation.json`

For each scenario, the report stores the same **`id`**, capability, **`expect`**, **`actual_summary`**, and any **`errors`**. Search the JSON for `"scenario_suite"` → `"results"` and match **`id`** to the rows above to see how a specific query behaved on your machine.

---

## 4) Reading the smoke section (your `[run 1]` / `[run 2]` blocks)

### 4.1 `workspace:`

The Motadata tree you pointed `--workspace-root` at. Evidence export and many paths in the output are interpreted relative to this workspace.

### 4.2 `repeat`, `stable`, `all_pass` (in the dev header)

| Field | Plain meaning |
|--------|----------------|
| **repeat** | How many full smoke passes ran. |
| **stable** | “Did both passes look the same in the ways the verifier fingerprints?” If `False`, you might have flakiness (model variance, timing, retrieval order, etc.). |
| **all_pass** (header) | **Smoke-only** pass in `--print dev` (see section 2). |

### 4.3 `[run N] smoke pass=True`

Whether that single smoke pass considered **all** of its internal checks successful (Ask, Debug, Plan, Execute contract shape, Agent checks, etc.). Individual pieces can still look “strict” or “blocked” while still being a **valid** governed outcome.

### 4.4 `request_id` / `trace_id`

- **request_id:** Identifier for the Ask request; use it to correlate logs across services.
- **trace_id:** Optional tracing hook; `None` simply means none was present in what the verifier captured.

---

## 5) The Ask block — “where the product answers your question”

This is the **evidence-first Ask** path: the system retrieved files/snippets from your repo, then produced a **plan-style** answer grounded on that evidence.

### 5.1 `governance_posture` and `ask_path`

| Field | Plain meaning |
|--------|----------------|
| **governance_posture** | High-level safety stance. `PLAN_ONLY` means “answer with planning / explanation grounded in evidence,” not “go run arbitrary shell commands.” |
| **ask_path** | Which Ask ingestion path ran. `v1_evidence` means “v1 Ask request built from an exported evidence bundle” — the intended production-style path. |

### 5.2 `evidence_quality` and `reasons`

A compact verdict on whether the retrieved evidence looks strong enough for the query, plus **why** the scorer said so.

Example pattern:

- **`STRONG`** — good enough to treat the answer as well grounded for policy purposes.
- **Reason codes** (examples from your run):
  - **`OWNER_ANCHOR_RECOVERY`** — the system anchored on an “owner” class/file from authority / Stage A and used that to stabilize retrieval.
  - **`QUERY_TOO_GENERIC`** — the question was broad; the system still produced a useful owner-centric answer but is flagging that the wording was not very specific.

Reason codes are not errors by themselves; they are **explanations**.

### 5.3 `retrieval_metrics` (the short line)

These summarize the top retrieved file list (at the verifier’s `top_k`):

| Metric | Plain meaning |
|--------|----------------|
| **distractor_count@k** | How many retrieved items are flagged as risky distractors at top-k. Lower is better. |
| **generic_infra_ratio** | Fraction of top paths that look like generic infrastructure/utilities rather than domain owners. |
| **owner@1 / owner@3** | Whether the authority “owner” file appears in rank 1 or anywhere in top 3 of exported evidence paths. |
| **anchor_hit_rate** | How often top items are tied to real query anchors (substring / token hooks), not just fuzzy matches. |

### 5.4 `plan_summary.steps`

The **human-facing answer**, as ordered steps. This is what you would show in a demo as “the model’s grounded explanation,” with explicit owner, collaborators, distractors, and domain notes.

### 5.5 `context_bundle.files`

The **actual files** the planner attached as context for this Ask, with a **selection_reason** per file (for example anchored by query tokens).

### 5.6 `Evidence bundle snippets`

Short text previews from retrieved files so you can sanity-check “did retrieval actually pull the right region of code?” without opening every file.

---

## 6) The EXPLAIN_DEBUG block — “debug this selection”

This is a **separate** HTTP call from the Ask above. It uses the **debug query** path and is meant to read like a structured debugging brief: summary, flow, risk.

Typical fields:

| Field | Plain meaning |
|--------|----------------|
| **routing_mode** | `explain_debug` means the Explain/Debug pipeline handled the request (as opposed to falling back to a generic chat-only path). |
| **summary** | Plain-language explanation grounded (when possible) on the selected file and bundle. |
| **logic_flow** | A structured narrative of control flow / conditions the model believes matter. |
| **likely_bug_risk** | Hypothesis lane: what could go wrong or what is uncertain — not a guaranteed bug list. |

**Why it can mention “comment / not executable code”:** If the selected fragment is not real executable logic, the model should say so honestly instead of inventing bytecode-level behavior.

---

## 7) The `/v0/plan` line — policy decision on a synthetic event

The verifier posts a small **shadow** planning event (not your real IDE event from a developer session). You should read this as:

> “Does the Plan-Gate still speak the plan/decision contract correctly on a representative request?”

In your output:

- **`decision: REFUSAL`** — for that synthetic PR-merge scenario, the policy engine’s answer is “refuse.” That can be **totally fine** for the smoke check: the scenario for plan often only asserts that a **decision exists** and the schema is correct, not that it must approve.

---

## 8) The `/v0/execute` line — governed execution probe

This is the **execute** path: Plan-Gate receives a command and returns a governed outcome.

Your smoke output shows:

- **`outcome: BLOCKED`**
- **`executed: False`**
- **`posture: safe_execute`**

Plain reading:

> “The system acknowledged the execute request, but the policy posture did not allow it to actually run the command as an executed action in this environment/configuration.”

That can still be a **valid** governed response (HTTP 200 + well-formed execute contract). The smoke “code check” mainly verifies the response is coherent, not that every environment must allow echo.

---

## 9) `agent semantics`

This encodes the product rule:

- **`/v0/agent` returns 404** — there is intentionally **no** separate public “agent” HTTP route; agent-like behavior is folded into governed Ask/Execute flows.
- **`assist_layer on ask: True`** — Ask responses still include assist metadata (advisory layer), consistent with the current architecture.

---

## 10) Scenario suite section — “pinned contracts per capability”

After smoke, the verifier prints each scenario row.

### 10.1 `file:`

Which scenario JSON file was executed.

### 10.2 `all_pass: False/True`

Whether **every** scenario row passed. One failure makes this `False`.

### 10.3 Each scenario line: `[PASS]` / `[FAIL]`, `id`, `capability`

| Part | Plain meaning |
|------|----------------|
| **id** | Stable scenario name (used in reports and bug reports). |
| **capability** | Which subsystem is under test: `ask`, `debug`, `plan`, `code`, `agent`. |
| **description** | Human intent of the scenario. |
| **expect** | The contract: fields that must match for PASS. |
| **actual** | Compact summary of what the verifier observed (`actual_summary`). |
| **error:** lines | Concrete mismatches for FAIL rows. |

### 10.4 Ask scenarios: what `expect` vs `actual` is doing

Ask scenarios typically assert things like:

- `ask_path` is `v1_evidence`
- governance is `PLAN_ONLY`
- execution is not enabled
- minimum number of plan steps
- sometimes: text must mention certain symbols
- sometimes: owner must appear in top-3, Stage A must inject owner lane, etc.

The **`dev:`** blocks under Ask scenarios are **extra demonstrator output**: steps, attached files, Stage A pool, snippet previews — useful for demos and debugging failing gates.

### 10.5 Debug scenarios

These assert structured EXPLAIN_DEBUG behavior (keys present, routing mode, honesty cases like missing selected files).

### 10.6 Plan scenarios

These assert schema and presence of a decision, not necessarily “approve.”

### 10.7 Agent scenario

Asserts “404 on `/v0/agent`” and assist presence on Ask.

---

## 11) Your specific failure — `code_echo_probe`

Your log shows:

```text
[FAIL] code_echo_probe (code)
  error: outcome want EXECUTED got BLOCKED
  error: executed want True got False
```

What that means in one sentence:

> The scenario **requires** a successful echo execution, but your live stack returned a **blocked** execute outcome instead.

This is **not** contradicting the smoke header by magic — it’s a stricter **scenario contract** than the smoke execute check.

**Why it happens**

- The scenario `code_echo_probe` explicitly expects:

```json
"outcome": "EXECUTED",
"executed": true
```

- Your Plan-Gate returned a valid execute response, but with **`BLOCKED`** / **`executed: false`** under `safe_execute` posture.

**What to do next (operator choices)**

1. **Treat as environment/policy mismatch** — adjust Plan-Gate execute policy / sandbox settings for the environment where you want echo to run, then rerun until the scenario matches intent.
2. **Treat as scenario drift** — if `BLOCKED` is the intended default for this deployment class, update the scenario expectation in `motadata_aiops_behavior_scenarios.v1.json` only after product owners agree (otherwise you weaken the contract accidentally).

**How to confirm in the JSON artifact**

Open `runtime/.run/motadata_behavior_validation.json` and inspect:

- `scenario_suite.results[]` for the object with `"id": "code_echo_probe"` — you will see the same errors in structured form.
- `smoke` section for the execute probe summary on each run — useful to compare “smoke thinks execute contract OK” vs “scenario wants EXECUTED.”

---

## 12) How to read `motadata_behavior_validation.json` quickly

Suggested order:

1. **`all_pass`** — final truth for automation.
2. **`smoke.runs`** — each run’s summarized checks (repeatability lives here).
3. **`scenario_suite.all_pass` and `scenario_suite.results`** — which contract row failed and why.
4. **`quality_policy`** — which policy file path was used (if any).

---

## 13) Quick glossary

| Term | Meaning |
|------|---------|
| **Smoke** | A broad end-to-end health + capability pass repeated for stability. |
| **Scenario** | A narrow contract test with explicit expected fields. |
| **Evidence-first Ask** | Export bundle from Context Layer, then Ask v1 on Plan-Gate using that bundle. |
| **Stage A** | A fusion stage that shapes candidate files before final ranking; scenarios may assert its diagnostics. |
| **Quality policy** | Extra gates on retrieval quality for certain scenario rows. |
| **posture** | Policy/safety stance for execute (for example `safe_execute`). |

---

*If ports, scenario IDs, or verifier flags change, update this guide alongside `docs/MOTADATA_DEMOBOOK.md` and `docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md`.*
