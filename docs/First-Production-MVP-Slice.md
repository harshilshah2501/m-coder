Here’s a **ready-to-print trace sheet** for brutal, step-by-step validation from **JetBrains UI**.

Use this as the single source of truth while testing. It is built for the production slice defined in your charter: plugin → Context Layer → Plan-Gate → vLLM/execute, with explicit path visibility and no silent theater.

* * *

Motadata AI Coding Assistant — End-to-End Trace Sheet
=====================================================

**Purpose:** Trace every JetBrains action end-to-end and prove:

* which endpoint path actually ran

* whether evidence-first was used

* whether vLLM was invoked

* whether UI truth matches backend truth

**Environment profile:** __________________________
------------

**Date:** __________________________
------------

**Tester:** __________________________
------------

**Branch / commit:** __________________________
------------

Plugin build/version:
------------

---

A. Preflight
------------

### A1. Config snapshot

* Evidence-first JVM flag set: `Yes / No`

* Context Layer URL: __________________________

* Plan-Gate URL assumption: `127.0.0.1:8089 / other`

* Active host profile:
  
  * `A: Windows + JetBrains + WSL + GPU`
  
  * `B: Native Linux + JetBrains + local repo + GPU`

### A2. Health checks

| Component     | Command / check  | Expected              | Actual             | Pass/Fail |
| ------------- | ---------------- | --------------------- | ------------------ | --------- |
| Context Layer | `GET /healthz`   | `status=ok`           | __________________ | ______    |
| Plan-Gate     | `GET /healthz`   | healthy               | __________________ | ______    |
| Plan-Gate     | `GET /version`   | v0/v1 schemas visible | __________________ | ______    |
| vLLM          | `GET /v1/models` | served model visible  | __________________ | ______    |

### A3. Live logs attached

| Component              | Log file / source          | Attached? |
| ---------------------- | -------------------------- | --------- |
| Context Layer          | __________________________ | Yes / No  |
| Plan-Gate              | __________________________ | Yes / No  |
| vLLM                   | __________________________ | Yes / No  |
| JetBrains/client trace | __________________________ | Yes / No  |

* * *

B. Endpoint and Log Map
-----------------------

### Expected path map by action

| Action               | Context Layer              | Plan-Gate                                 | vLLM                   | Execute |
| -------------------- | -------------------------- | ----------------------------------------- | ---------------------- | ------- |
| Ask (default)        | Maybe no                   | `/v0/ask` unless evidence-first enabled   | No                     | No      |
| Ask (evidence-first) | `/v1/export_evidence`      | `/v1/ask`                                 | Usually no             | No      |
| Debug / Explain      | `/v1/export_evidence`      | `/v1/ask`                                 | `/v1/chat/completions` | No      |
| Plan                 | `/v1/export_evidence`      | `/v1/ask` or `/v0/plan` depending UI flow | Usually no             | No      |
| Code                 | No or optional pre-context | `/v0/execute`                             | No                     | Yes     |

### Log expectations

| Event                       | Where it should appear                   |
| --------------------------- | ---------------------------------------- |
| `POST /v1/export_evidence`  | Context Layer log                        |
| `POST /v1/ask`              | Plan-Gate trace/log or response metadata |
| `POST /v0/ask`              | Plan-Gate trace/log or response shape    |
| `POST /v1/chat/completions` | vLLM log                                 |
| `POST /v0/execute`          | Plan-Gate trace/log + execution output   |

* * *

C. Action Trace Records
=======================

Print one page per action.

* * *

Trace Record 1 — Ask (default path)
-----------------------------------

**Intent:** Confirm what JetBrains does with evidence-first disabled or absent.

### Input

* UI action: `Ask`

* Query: _______________________________________________

* Active file: ___________________________________________

* Selection: ____________________________________________

### Expected

* Likely Plan-Gate path: `/v0/ask`

* No `ask_path: v1_evidence`

* No Context Layer hit unless plugin behavior differs

* UI may show legacy context bundle behavior

### Actual Trace

| Check                                           | Expected        | Actual             | Pass/Fail |
| ----------------------------------------------- | --------------- | ------------------ | --------- |
| Context Layer `/v1/export_evidence` hit         | No / usually no | __________________ | ______    |
| Plan-Gate `/v0/ask` hit                         | Yes             | __________________ | ______    |
| Plan-Gate `/v1/ask` hit                         | No              | __________________ | ______    |
| `ask_path` visible in UI/metadata               | No or absent    | __________________ | ______    |
| `Grounding — layer5.evidence_bundle.v1` visible | No              | __________________ | ______    |
| UI shows files                                  | legacy/optional | __________________ | ______    |
| UI shows notes                                  | likely no       | __________________ | ______    |
| vLLM hit                                        | No              | __________________ | ______    |

### Logs captured

* Context Layer log excerpt: ______________________________________

* Plan-Gate log excerpt: _________________________________________

* vLLM log excerpt: ______________________________________________

### Verdict

* Path used: `v0 / v1 / unknown`

* UI truthfulness: `accurate / misleading / incomplete`

* Notes: ________________________________________________________

* * *

Trace Record 2 — Ask (evidence-first)
-------------------------------------

**Intent:** Prove the production-grade evidence-first path from JetBrains.

### Input

* UI action: `Ask`

* Query: _______________________________________________

* Active file: ___________________________________________

* Selection: ____________________________________________

### Expected

* Context Layer `POST /v1/export_evidence`

* Plan-Gate `POST /v1/ask`

* `ask_path = v1_evidence`

* Grounding visible

* No vLLM needed for standard planner-only Ask

### Actual Trace

| Check                                           | Expected                             | Actual             | Pass/Fail |
| ----------------------------------------------- | ------------------------------------ | ------------------ | --------- |
| Context Layer `/v1/export_evidence` hit         | Yes                                  | __________________ | ______    |
| Plan-Gate `/v1/ask` hit                         | Yes                                  | __________________ | ______    |
| Plan-Gate `/v0/ask` hit                         | No                                   | __________________ | ______    |
| `ask_path = v1_evidence` present                | Yes                                  | __________________ | ______    |
| `Grounding — layer5.evidence_bundle.v1` visible | Yes                                  | __________________ | ______    |
| Evidence files shown in UI                      | Yes                                  | __________________ | ______    |
| Evidence count non-zero                         | Yes                                  | __________________ | ______    |
| `plan_summary.steps` shown                      | Yes                                  | __________________ | ______    |
| `plan_summary.notes` shown                      | Should be yes; current gap likely no | __________________ | ______    |
| vLLM hit                                        | No / not required                    | __________________ | ______    |

### Evidence quality check

| Item                 | Actual                                    |
| -------------------- | ----------------------------------------- |
| Top 3 evidence paths | 1. __________ 2. __________ 3. __________ |
| Relevant to query?   | `Yes / Partly / No`                       |
| Test-file dominance? | `Yes / No`                                |
| Stopword noise?      | `Yes / No`                                |

### Logs captured

* Context Layer log excerpt: ______________________________________

* Plan-Gate log excerpt: _________________________________________

* vLLM log excerpt: ______________________________________________

### Verdict

* Path used: `v1_evidence / other`

* Retrieval quality: `good / weak / misleading`

* UI truthfulness: `accurate / incomplete / misleading`

* Notes: ________________________________________________________

* * *

Trace Record 3 — Debug / Explain
--------------------------------

**Intent:** Prove that Debug actually invokes the LLM path when required.

### Input

* UI action: `Debug / Explain`

* Query: _______________________________________________

* Active file: ___________________________________________

* Selection or method: ___________________________________

### Expected

* Context Layer `POST /v1/export_evidence`

* Plan-Gate `POST /v1/ask`

* Backend chooses `EXPLAIN_DEBUG`

* vLLM `POST /v1/chat/completions`

* Response contains `explain_debug`-style output

### Actual Trace

| Check                                                 | Expected | Actual             | Pass/Fail |
| ----------------------------------------------------- | -------- | ------------------ | --------- |
| Context Layer `/v1/export_evidence` hit               | Yes      | __________________ | ______    |
| Plan-Gate `/v1/ask` hit                               | Yes      | __________________ | ______    |
| `ask_path = v1_evidence` present                      | Yes      | __________________ | ______    |
| `explain_debug` present in response                   | Yes      | __________________ | ______    |
| vLLM `/v1/chat/completions` hit                       | Yes      | __________________ | ______    |
| UI includes debug reasoning, not generic planner text | Yes      | __________________ | ______    |
| Evidence tied to selected file/selection              | Yes      | __________________ | ______    |

### Logs captured

* Context Layer log excerpt: ______________________________________

* Plan-Gate log excerpt: _________________________________________

* vLLM log excerpt: ______________________________________________

### Verdict

* LLM invoked: `Yes / No / unclear`

* Debug path quality: `good / weak / wrong path`

* Notes: ________________________________________________________

* * *

Trace Record 4 — Plan
---------------------

**Intent:** Validate governed planning without execution.

### Input

* UI action: `Plan`

* Query: _______________________________________________

* Active file: ___________________________________________

* Selection: ____________________________________________

### Expected

* Evidence-first path preferred

* Plan-Gate plan response

* `PLAN_ONLY`

* Affected files / steps / rationale visible

* No execution

### Actual Trace

| Check               | Expected                               | Actual             | Pass/Fail |
| ------------------- | -------------------------------------- | ------------------ | --------- |
| Context Layer hit   | Yes / preferred                        | __________________ | ______    |
| Plan-Gate endpoint  | `/v1/ask` or `/v0/plan` depending flow | __________________ | ______    |
| Outcome `PLAN_ONLY` | Yes                                    | __________________ | ______    |
| Steps shown         | Yes                                    | __________________ | ______    |
| Notes shown         | Ideally yes                            | __________________ | ______    |
| Evidence shown      | Yes if v1                              | __________________ | ______    |
| Execution occurred  | No                                     | __________________ | ______    |
| vLLM hit            | No / not required                      | __________________ | ______    |

### Verdict

* Path used: __________________________________

* Planning quality: `good / weak / opaque`

* Notes: ________________________________________________________

* * *

Trace Record 5 — Code / Submit to Runtime
-----------------------------------------

**Intent:** Validate code execution path honestly and safely.

### Input

* UI action: `Code / Submit to Runtime`

* Command or action: _____________________________________

* Active file: ___________________________________________

### Expected

* Plan-Gate `POST /v0/execute`

* Clear executed / refused / blocked outcome

* No fake success

* Exit code or refusal reason visible

### Actual Trace

| Check                        | Expected            | Actual             | Pass/Fail |
| ---------------------------- | ------------------- | ------------------ | --------- |
| `/v0/execute` hit            | Yes                 | __________________ | ______    |
| Outcome visible              | Yes                 | __________________ | ______    |
| Exit code visible            | Yes if executed     | __________________ | ______    |
| Refusal/block reason visible | Yes if not executed | __________________ | ______    |
| Execution truly happened     | Yes / if allowed    | __________________ | ______    |
| Misleading success text      | No                  | __________________ | ______    |

### Logs captured

* Plan-Gate log excerpt: _________________________________________

* Runtime/sandbox output excerpt: _________________________________

### Verdict

* Execution result: `executed / blocked / refused / unclear`

* UX honesty: `accurate / misleading`

* Notes: ________________________________________________________

* * *

Trace Record 6 — No-match honesty
---------------------------------

**Intent:** Confirm the system is honest under weak evidence.

### Input

* UI action: `Ask`

* Query: _______________________________________________

### Expected

* weak or empty evidence

* explicit insufficiency

* no fabricated file paths or false certainty

### Actual Trace

| Check                        | Expected | Actual             | Pass/Fail |
| ---------------------------- | -------- | ------------------ | --------- |
| Evidence weak/empty          | Yes      | __________________ | ______    |
| No hallucinated file path    | Yes      | __________________ | ______    |
| Explicit insufficiency shown | Yes      | __________________ | ______    |
| UI misleading confidence     | No       | __________________ | ______    |

### Verdict

* Honesty quality: `good / weak / hallucinated`

* Notes: ________________________________________________________

* * *

D. Expected Output Cheat Sheet
==============================

Use this while validating so you know what “good” looks like.
Good Ask (evidence-first)
-------------------------

You should see or infer:

* Context Layer `/v1/export_evidence`

* Plan-Gate `/v1/ask`

* `ask_path = v1_evidence`

* evidence files visible

* non-empty steps

* no execution

* no vLLM requirement for ordinary Ask

Good Debug
----------

You should see or infer:

* `/v1/export_evidence`

* `/v1/ask`

* `explain_debug`

* vLLM `/v1/chat/completions`

* reasoning tied to selected file/selection

Good Plan
---------

You should see:

* `PLAN_ONLY`

* steps

* evidence or explicit path

* no execution

Good Code
---------

You should see:

* `/v0/execute`

* executed/refused/blocked clearly stated

* exit code or refusal reason

* no theater

Bad smells
----------

Mark these immediately:

* `(no files selected)` with known non-empty evidence backend

* no visible distinction between `/v0/ask` and `/v1/ask`

* backend notes exist but UI hides them

* debug path that never touches vLLM

* code path says “success” but execution didn’t really happen

* weak evidence presented as strong certainty

* * *

E. Final Run Summary
====================

After all traces, fill this one-page summary.

| Action      | Actual endpoint path | Evidence-first? | LLM used? | UI honest? | Pass/Fail |
| ----------- | -------------------- | --------------- | --------- | ---------- | --------- |
| Ask default | __________________   | Yes / No        | Yes / No  | Yes / No   | ______    |
| Ask v1      | __________________   | Yes / No        | Yes / No  | Yes / No   | ______    |
| Debug       | __________________   | Yes / No        | Yes / No  | Yes / No   | ______    |
| Plan        | __________________   | Yes / No        | Yes / No  | Yes / No   | ______    |
| Code        | __________________   | Yes / No        | Yes / No  | Yes / No   | ______    |
| No-match    | __________________   | Yes / No        | Yes / No  | Yes / No   | ______    |

Overall conclusion
------------------

* Production path clarity: `good / partial / poor`

* Observability: `good / partial / poor`

* UX honesty: `good / partial / poor`

* Biggest blocker: _____________________________________________

* Next required fix: ____________________________________________

* * *

F. Print Notes
==============

Print this as:

* 1 preflight page

* 1 endpoint/log map page

* 6 action trace pages

* 1 final summary page

That gives you a clean **9-page operator packet**.

If you want, I can turn this into a **proper DOCX/PDF printable sheet** next.
