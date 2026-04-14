# Action 10 — Host Profile B (Native Linux) — Final verdict

## 1. Environment summary

| Field | Value |
|-------|--------|
| OS | Linux (session host: native; `uname` not captured in pack — run locally if needed) |
| MCODER_ROOT | /home/harshil/Harshil-PoCs/m-coder |
| MOTADATA_ROOT | /home/harshil/Projects/Motadata |
| Context Layer URL | http://127.0.0.1:8091 (health OK at capture) |
| Plan-Gate URL | http://127.0.0.1:8089 (health OK at capture) |
| vLLM | http://127.0.0.1:8000/v1/models OK |
| GPU | Local listeners on 127.0.0.1 (vLLM PID observed on :8000) |

## 2. Scenario results (HTTP / stack — this run)

| Scenario | Result | Evidence |
|----------|--------|----------|
| Health — Context Layer | PASS | health/context_layer_healthz.json |
| Health — Plan-Gate | PASS | health/plan_gate_healthz.json |
| Ask (primary fixed query, POST /v1/ask after export) | PASS | ask/v1_ask_response.json (`evidence_first_meta.ask_path` = `v1_evidence`) |
| Explain/Debug | NOT_PROVEN | No IDE selection / Explain run in this pass |
| Execute OK | PASS | execute_ok/echo_hello_response.json (`outcome` EXECUTED) |
| Execute blocked | PASS | execute_blocked/rm_rf_response.json (`outcome` REFUSED, executed false) |
| Execute failed | PASS | execute_failed/py_exit1_response.json (`outcome` EXECUTED_FAILED) |
| No-match (primary fixed query) | PASS | nomatch/v1_ask_response.json (PLAN_ONLY; no fabricated definition) |
| Failure mode | PASS | failure/before_healthz.txt, curl_when_down.txt (connection refused), after_healthz.txt after restart |

## 3. Host A vs Host B (functional)

| Dimension | Host A (baseline) | Host B (this run) | Verdict |
|-----------|-------------------|-------------------|---------|
| Ask evidence-first | PASS | PASS (HTTP v1_evidence); IDE Ask not captured | NOT_PROVEN (IDE) / PASS (HTTP) |
| Explain/Debug | PASS | NOT_PROVEN | NOT_PROVEN |
| Execute OK / blocked / failed | PASS | PASS | PASS |
| No-match honesty | PASS | PASS | PASS |
| Failure mode | PASS | PASS (no fail-open on connection) | PASS |
| request_id traceability | PASS | NOT_PROVEN | plan_gate.log empty at capture — observability gap |

## 4. Drift / classification

- **Environment/config (closure-blocking):** Inspected `idea64.vmoptions` has **no** `-Dmotadata.*` lines. Evidence-first Ask from the **IDE** cannot be claimed equivalent to Host A until VM options (or env) are set and plugin output is captured.
- **Observability (non-blocking):** `runtime/.run/plan_gate.log` was size 0 after Plan-Gate restart; request_id correlation from server log file is NOT_PROVEN for this run. Behavior still evidenced via JSON artifacts.

## 5. Closure verdict (addendum format)

```text
Action 10 — Host Profile B
Status: FAIL

Reason:
- Governed stack (Context Layer, Plan-Gate, vLLM) health checks passed; POST /v1/ask with fixed primary query shows v1_evidence path; execute outcomes are distinct (EXECUTED / REFUSED / EXECUTED_FAILED); failure mode shows connection refused when Plan-Gate is down, then recovery.
- Inspected IntelliJ idea64.vmoptions does not set motadata.ask.evidence_first or explicit motadata.context_layer.url / motadata.plan_gate.url; plugin-visible Ask evidence-first closure row is therefore not proven for the IDE.
- Explain/Debug not executed in this pass (NOT_PROVEN — acceptable only as observability if IDE behavior matches Host A; not demonstrated here).

Functional parity with Host A: No

Closure blockers:
- Add and apply Linux IDE Custom VM options, restart IDE, re-run Ask with fixed primary query from fixed_queries.txt and capture plugin dialog showing v1_evidence / evidence_first_meta (or equivalent). Until then, Action 10 cannot be marked closed for “JetBrains on native Linux” as a whole.
- Optional: capture plugin output for failure mode (RUNTIME_UNAVAILABLE) to match Host A narrative.

Non-blocking observability gaps:
- plan_gate.log empty or not populated for request_id grep
- Explain/Debug traceability not exercised (behavior unproven for this host)

Can roadmap advance?
- No — for Action 10 “close Host Profile B” until IDE evidence-first + plugin captures are satisfied (or explicitly scoped as “backend-only PASS”).
```
