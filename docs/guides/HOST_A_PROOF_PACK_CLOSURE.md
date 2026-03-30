# Host-A proof pack — audit closure (request spine + packaging + sheets)

This document turns **behavioral PASS** (scenarios ran correctly) into **audit-grade closure**: same **`request_id`** visible from plugin output through Plan-Gate (and Context Layer / vLLM where applicable), artifacts **grouped per scenario**, and two **validation sheets** you can paste into a review packet.

**Companion:** [ACTION_7_TRUST_AUDIT.md](./ACTION_7_TRUST_AUDIT.md) (runbook, STEP 5–7). Use this file when reviewers ask for **traceability** beyond narrative markdown captures.

---

## 1. What “closed” means

| Requirement | Meaning |
|-------------|---------|
| **request_id spine** | For each scenario row, you can name one `request_id` and show it in **plugin-facing text** (or `NOT_PROVEN` with reason) **and** in **`.run/plan_gate.log`** (and Context Layer log for evidence-first Ask). |
| **Per-scenario packaging** | One folder per scenario under a single root (`hostA_proof_pack/`), with the **same filenames** so reviewers can diff packs across dates. |
| **Validation sheets** | Two tables (backend + plugin isolation) filled honestly — `PRESENT` / `NOT_PROVEN` / `n/a`, not hand-wavy PASS. |

---

## 2. Canonical directory layout (mandatory structure)

Create one root (timestamped copy is fine):

```text
hostA_proof_pack/
  README.md                    # optional: host, date, MOTADATA_ROOT, MCODER_ROOT
  mapping_request_ids.md       # §3 spine — template: docs/guides/mapping_request_ids.md

  health/                      # optional: tunnel + service smoke (from ACTION_7 STEP 1–2)
  logs/                        # optional: copies of .run/plan_gate.log slice, context_layer journal

  ask/
    plugin.txt                 # copy of notification + full response, or screenshot note
    request.json               # optional: redacted POST body if captured via proxy
    response.json              # optional: if captured
    context.log                # grep slice: CONTEXT_LAYER + same request_id
    plangate.log               # grep slice: PLAN_GATE + same request_id

  debug/
    plugin.txt
    context.log
    plangate.log
    vllm.log                   # optional: Explain path /chat/completions line with same window

  execute_ok/
    plugin.txt
    echo_hello_response.json   # structured execute proof (stdout_summary, exit_code)
    plangate.log

  execute_blocked/
    plugin.txt
    response.json              # or narrative + outcome line
    plangate.log

  execute_failed/
    plugin.txt
    response.json
    plangate.log

  nomatch/
    plugin.txt
    context.log
    plangate.log

  failure/
    before_healthz.txt
    curl_when_down.txt
    after_healthz.txt
    plugin.txt                 # optional: RUNTIME_UNAVAILABLE text
    plangate.log               # optional: line during outage window
```

**Scattered vs coherent:** Narrative files like `Ask_v1.md` / `NoMatch.md` stay valid as **human summaries**; this layout is the **machine-auditable** complement. You can symlink or copy excerpts into `ask/plugin.txt` etc.

---

## 3. GAP 1 — Extract `request_id` (do once per scenario)

### 3.1 Plan-Gate log (primary)

From `MCODER_ROOT` (or the host where Plan-Gate runs):

```bash
cd "$MCODER_ROOT"
grep -i "request_id" .run/plan_gate.log | tail -80
```

Match rows to scenarios by **wall-clock time** (your IDE run) and **route** (`/v1/ask`, `/v0/execute`, …) and **query/command** fragments if logged.

### 3.2 Context Layer (Ask / Explain / No-match — evidence-first)

```bash
grep -E "export_evidence|request_id" /path/to/context_layer.log | tail -80
```

(Exact path depends on how you run the service — stdout, journal, or file.)

### 3.3 Mapping table (fill and save as `mapping_request_ids.md`)

**Template in repo:** [mapping_request_ids.md](./mapping_request_ids.md) — copy to your `hostA_proof_pack/` root and edit.

**Worked example (filled from a real `plan_gate.log` excerpt, with confidence levels):** [HOST_A_PLAN_GATE_LOG_MAPPING.md](./HOST_A_PLAN_GATE_LOG_MAPPING.md).

| Scenario | request_id | Matched by (time / query / route) | Plan-Gate line ref | Context Layer line ref |
|----------|------------|-----------------------------------|--------------------|-------------------------|
| Ask (5.1) | | | | |
| Explain/Debug (5.2) | | | | |
| Execute OK | | | | |
| Execute Blocked | | | | |
| Execute Failed | | | | |
| No-match (5.4) | | | | |
| Failure (5.5) | | optional / `NOT_PROVEN` if only curl proof | | n/a |

If you cannot correlate: mark **`NOT_PROVEN`** for that cell — that is allowed; it defines remaining audit work.

### 3.4 Plugin visibility

The JetBrains plugin surfaces **`request_id`** in **Ask** summary and **full response** text (see `buildAskResultSummaryMessage` / `buildAskResultDialogMessage`). For **Submit to Runtime**, use the dialog text plus JSON captures as today.

---

## 4. GAP 2 — Scenario packaging checklist

Before calling the pack “submission-ready”:

- [ ] Every scenario folder exists **or** explicitly marked N/A (e.g. duplicate execute proof in one JSON — still list paths).
- [ ] Each folder has at least **`plugin.txt`** OR a clear **`README.txt`** stating where the plugin capture lives.
- [ ] Execute OK includes **structured JSON** with `request_id`, `stdout_summary` / `exit_code` where applicable.
- [ ] Failure includes **before / during / after** reachability proof (`healthz` + `curl` error).

---

## 5. GAP 3 — Validation sheets (paste into review packet)

### 5.1 Backend validation sheet

Fill `PRESENT` / `NOT_PROVEN` / `PASS` / `FAIL` honestly. `n/a` where the service is not in the path.

| Scenario | Outcome | Context | Plan-Gate | vLLM | request_id | Verdict |
|----------|---------|---------|-----------|------|------------|---------|
| Ask | | | | n/a | | |
| Explain/Debug | | | | | | |
| Execute OK | | n/a | | n/a | | |
| Execute Blocked | | n/a | | n/a | | |
| Execute Failed | | n/a | | n/a | | |
| No-match | | | | n/a | | |
| Failure | | NOT_PROVEN / n/a | | n/a | | |

**Notes:**

- **Failure row:** “Context” may be `NOT_PROVEN` if you only proved transport fail-closed (curl + healthz), not Layer export — say so in a footnote.
- **vLLM:** `NOT_PROVEN` is normal if Explain model was off; **n/a** if you did not run Explain.

### 5.2 Plugin defect isolation sheet

| Scenario | Plugin output | Matches backend | request_id visible in plugin | Verdict |
|----------|---------------|-----------------|------------------------------|---------|
| Ask | | | | |
| Explain/Debug | | | | |
| Execute OK | | | | |
| Execute Blocked | | | | |
| Execute Failed | | | | |
| No-match | | | | |
| Failure | | | | |

**“Matches backend”:** same outcome / grounding story as Plan-Gate + metadata (allowing for UI truncation).

---

## 6. Final closure criteria (single checklist)

| Requirement | Status (tick when true) |
|-------------|---------------------------|
| All Host-A scenarios executed (ACTION_7 §5.1–5.5) | |
| Backend behavior documented (PASS narratives) | |
| Governance invariants (fail-closed, execute boundary) | |
| Per-scenario folder layout (`§2`) | |
| `request_id` mapping table (`§3.3`) filled or `NOT_PROVEN` explicit | |
| Backend validation sheet (`§5.1`) | |
| Plugin isolation sheet (`§5.2`) | |

---

## 7. Optional — submission-ready single document

To produce one **enterprise-style** PDF/Markdown for auditors:

1. Export this file + filled sheets + `mapping_request_ids.md`.
2. Append **ACTION_7 STEP 7** executive summary (verbatim or summarized).
3. Attach **tree listing** of `hostA_proof_pack/` (`tree -L 2`).

---

## 8. Paths used on Host-A (example)

Adjust to your machine; not authoritative.

| Artifact | Example path |
|----------|----------------|
| Ask / runtime narratives | `~/Harshil-PoCs/Ask_v1.md`, `~/Harshil-PoCs/Exec_Runtime.md`, `~/Harshil-PoCs/NoMatch.md` |
| Evidence bundle (failure, execute) | `~/Harshil-PoCs/Action_7_Evidences/` |

Keep **one** canonical `hostA_proof_pack_<date>/` per review cycle to avoid confusion.
