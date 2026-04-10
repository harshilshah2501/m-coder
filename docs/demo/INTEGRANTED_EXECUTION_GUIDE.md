# Motadata AI Coding Assistant — Final Integrated Execution & Demo Guide

> Status (2026-04): historical consolidated guide.
>
> For canonical setup and demo execution, use this golden path:
> - [../MOTADATA_DEMO_SETUP_RUNBOOK.md](../MOTADATA_DEMO_SETUP_RUNBOOK.md)
> - [../runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md](../runtime/JETBRAINS_PLUGIN_DEMO_GUIDE.md)
> - [NEAR_PRODUCTION_VERTICAL_SLICE_RUNBOOK.md](NEAR_PRODUCTION_VERTICAL_SLICE_RUNBOOK.md)
>
> For current closure state and latest inclusions, use:
> - [../LIVE_ROADMAP_TRACKER.md](../LIVE_ROADMAP_TRACKER.md)
> - [../mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md](../mvp_declaration/GOVERNED_SYSTEM_V1_PRODUCTION_CLOSURE_DECLARATION.md)

* * *

## 1. Purpose

This document consolidates the **final working model, execution flow, and demo procedure** for the Motadata AI Coding Assistant.

The system is not a generic coding assistant.

> It is a **governed reasoning system over real production code**, with deterministic planning, bounded execution, and auditability.

This guide ensures:

* End-to-end execution works from **JetBrains IDEA (Windows)**
* Runtime and GPU services are correctly orchestrated
* Ask → Plan → Execute flow is validated
* Demo is **repeatable, grounded, and trustworthy**

* * *

## 2. System Architecture (Final Form)

### Layers

1. **JetBrains Plugin (Windows JVM)**
  
  * Entry point
  * Sends structured requests (/v0/ask, /v0/execute)
2. **Governed Runtime (GPU machine)**
  
  * Plan-Gate
  * Context Engine (repo-aware retrieval)
  * Deterministic Guard
  * Ledger + canonical_hash
3. **Reasoning Layer (vLLM)**
  
  * Local model (mandatory in governed mode)
  * Used for explain/debug reasoning
4. **Codebase (Local on GPU machine)**
  
  * Source of truth for all repo-aware operations

* * *

## 3. Critical Principle — Source of Truth

> The runtime reads code from its **local filesystem only**.

* JetBrains plugin paths (Windows) are **NOT used** for file access
* Repo must exist on GPU machine
* Ask requests may contain Windows paths, but runtime resolves via:

    ASK_DEFAULT_REPO_ROOT

If mismatch occurs:

* Runtime falls back
* `context_resolution` is included in response

* * *

## 4. One-Command Governed Startup (Recommended)

### Step 1 — Configure once

Create:

    runtime/config/demo_stack.env

Key fields:

    VLLM_BASE_MODEL=/absolute/local/path/to/model
    VLLM_SERVED_MODEL_NAME=your-model-name
    VLLM_PORT=8000
    
    PLAN_GATE_PORT=8089
    
    ASK_DEFAULT_REPO_ROOT=/home/harshil/Harshil-PoCs/m-coder

Rules:

* `VLLM_BASE_MODEL` → **local path only (mandatory)**
* Repo path must exist on GPU machine

* * *

### Step 2 — Start full stack

    bash runtime/scripts/governed_services.sh start

What happens:

1. Validates config (fail-fast)
2. Starts vLLM
3. Waits for `/v1/models` with correct model name
4. Starts Plan-Gate
5. Waits for `/healthz`
6. Writes logs + PIDs to:

    runtime/.run/

Success is printed **only when both services are ready**.

* * *

## 5. Connectivity Validation (Windows → GPU)

From PowerShell:

    curl http://127.0.0.1:8089/healthz

Expected:

    200 OK

* * *

### Important signal

    POST /v0/ask with {}
    → 400 Schema validation

This means:

* Runtime reachable
* Correct service bound

* * *

## 6. JetBrains IDEA Validation (Primary Path)

### This is the real test — NOT PowerShell

PowerShell is only for diagnostics.

### Steps

1. Open project in IntelliJ (Windows)
2. Ensure plugin is installed
3. Ensure runtime URL =

    http://127.0.0.1:8089

4. Select a real code file
  
5. Run:
  

* **Ask Motadata AI**

* * *

### Expected behavior

You should see:

* PLAN ONLY response
* Context bundle populated
* Relevant files selected
* Structured reasoning steps

* * *

### Failure modes

| Symptom | Meaning |
| --- | --- |
| Runtime not available | connectivity issue |
| Empty plan | request malformed |
| **files = []** | retrieval failure (CRITICAL) |

* * *

## 7. What “Correct Ask” Looks Like

A valid response must include:

### 1. Context Bundle

* revision present
* files > 0
* selectors_used populated

### 2. Files

Each file should:

* be relevant to query
* include reason (symbol/import/etc.)

### 3. Plan

* 3–6 steps
* specific to code
* not generic

* * *

### Current Gap (Observed)

    files = []

Meaning:

> Retrieval is not grounding the response in actual code

This must be fixed before demo.

* * *

## 8. Golden Demo (Definition of Success)

### Step 1 — Choose real AIOps code

* 40–120 LOC
* Contains real logic

* * *

### Step 2 — Ask

Prompt:

> What does this code do and where is the most likely failure risk?

* * *

### Step 3 — Expected output

Must:

* reference real functions
* reference real files
* identify real failure risk

Must NOT:

* be generic
* hallucinate architecture

* * *

### Step 4 — Follow-up

> What is the smallest safe fix?

Must:

* be local
* minimal
* safe

* * *

## 9. Stability Requirement

Run same demo 5–10 times

System must:

* not crash
* not vary wildly
* remain grounded

* * *

## 10. Audit Proof (Optional but Powerful)

Show:

* request_id
* canonical_hash
* trace reconstruction

This is your enterprise differentiator

* * *

## 11. What NOT to Do

Do NOT:

* add features
* change architecture
* expand scope

> Closure = stabilization, not expansion

* * *

## 12. Final Closure Checklist

All must be TRUE:

* IntelliJ → runtime works
* Ask returns grounded files
* Plan is meaningful
* Demo works repeatedly
* vLLM reasoning works
* No manual setup needed

* * *

## 13. Current Status

You are at:

> **~85–90% complete**

Remaining work:

* Fix retrieval (files empty)
* Validate golden demo
* Ensure stability

* * *

## 14. Final Truth

Right now the system can say:

> "Here’s how I would investigate"

It must evolve to:

> "Here are the exact files I investigated, and here’s what I found"

That transition is the last mile.

* * *

## 15. Execution Priority

1. Fix empty context_bundle.files
2. Validate real code Ask
3. Run in IntelliJ (not PowerShell)
4. Stabilize demo

* * *

**End of Document**