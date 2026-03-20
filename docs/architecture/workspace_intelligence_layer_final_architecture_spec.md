# Workspace Intelligence Layer — Final Architecture Spec

## 1. Objective

Design the final production architecture for the Motadata AI Coding Assistant where:

- **JetBrains IDEA runs on Windows**
- **Code repository lives in WSL**
- **Context Layer runs near the workspace in WSL**
- **Plan-Gate + vLLM run on GPU server**
- **Governance, reasoning, and execution remain centralized**
- **Code retrieval, indexing, and evidence grounding stay local to the workspace**

This architecture replaces the temporary assumption that the GPU runtime should read the developer repository directly.

---

## 2. Core Principle

> **Code should be retrieved where it lives. Reasoning should happen where compute lives. Governance should happen where control lives.**

That leads to a clean split:

- **WSL Context Layer** = workspace intelligence and source-of-truth for code retrieval
- **GPU Plan-Gate + vLLM** = governed reasoning, planning, bounded generation, execution authority
- **JetBrains Plugin** = interaction surface and orchestration client

---

## 3. Final High-Level Architecture

```text
JetBrains IDEA (Windows)
   ↓
JetBrains Plugin
   ↓
Workspace Intelligence Layer (WSL)
   ↓ structured grounded context bundle
Plan-Gate (GPU)
   ↓
vLLM (GPU)
   ↓
Governed response / bounded fix / execution decision
   ↓
JetBrains Plugin UI
```

---

## 4. Component Responsibilities

### 4.1 JetBrains Plugin (Windows)

Responsibilities:

- Capture user intent
- Capture active file, selection, caret, diagnostics, editor state
- Call WSL Context Layer for retrieval and grounding
- Call GPU Plan-Gate for reasoning/planning/execution
- Render grounded answer / plan / patch / decision
- Apply bounded edits only through governed flow

Must NOT own:

- heavyweight indexing
- full retrieval engine
- core reasoning
- policy decisions

---

### 4.2 Workspace Intelligence Layer (WSL)

This is the new major subsystem.

Responsibilities:

- Repo discovery and workspace resolution
- Git revision and dirty-state detection
- Incremental indexing
- Symbol extraction
- Call graph / import graph / file relationships
- Lexical retrieval
- Semantic retrieval
- Snippet extraction
- Evidence packaging
- Local deterministic answers for structural queries

This is the **source of truth for code context**.

---

### 4.3 Plan-Gate (GPU)

Responsibilities:

- Request validation
- Governance / policy enforcement
- Task classification
- Bounded investigation plans
- Explanation synthesis over grounded evidence
- Bounded fix generation
- Execution gating
- Audit trail / canonical hash / ledger / trace

Plan-Gate must receive **structured evidence**, not raw repo-path assumptions.

---

### 4.4 vLLM (GPU)

Responsibilities:

- High-quality reasoning over grounded code evidence
- Explain/debug synthesis
- Risk analysis
- Bounded fix proposal
- Comparative judgment

vLLM should not be used as the retrieval engine.

---

## 5. What the Context Layer Handles Locally

These should be answered locally without calling vLLM whenever possible.

### 5.1 Structural / Deterministic queries

- Where is function `X` defined?
- Which files reference symbol `Y`?
- Which modules import `Z`?
- What tests touch this file/module?
- What changed in this file since revision `R`?
- What symbols exist in the selected file?
- Which callers/callees surround this function?

### 5.2 Workspace-state queries

- Repo root
- Revision / branch
- Dirty state
- Active project/module
- Index freshness
- File ownership / module metadata

### 5.3 Context assembly

- Top candidate files
- Relevant snippets
- Selection reasons
- Selector provenance
- Snippet spans
- Evidence graph

### 5.4 Fast local diagnostics

- Syntax parse failures
- Missing/unresolved symbol
- Duplicate definitions
- Unindexed file
- Unsupported language segment

---

## 6. What Must Go to Plan-Gate + vLLM

These require judgment, synthesis, or governed action.

### 6.1 Reasoning tasks

- What does this function do in system context?
- What is the most likely failure mode?
- Why is this correlation logic risky?
- Summarize behavior across multiple files
- Compare two implementation strategies
- Assess blast radius

### 6.2 Planning tasks

- What is the bounded investigation plan?
- What should be checked next?
- Which follow-up questions matter?

### 6.3 Bounded coding tasks

- What is the smallest safe fix?
- Produce bounded patch proposal
- Validate patch against existing code evidence
- Prepare governed execution payload

---

## 7. Final API Boundaries

## 7.1 Plugin ↔ Context Layer APIs

### `POST /workspace/resolve`

Returns:

- repo_root
- revision
- branch
- dirty_files
- language mix
- index status

### `POST /symbols/lookup`

Input:

- symbol name
- optional module/file scope
  Returns:
- definitions
- references
- signatures
- candidate files

### `POST /context/retrieve`

Input:

- task_type (`EXPLAIN`, `PLAN`, `BOUNDED_FIX`, `DEBUG`)
- query
- active_file
- selected_text / selected_span
- max_files
- max_snippets
  Returns:
- ranked files
- snippets
- reasons
- selectors used
- revision
- evidence summary

### `POST /context/expand`

Input:

- seed files / symbols
  Returns:
- callers / callees
- imports
- siblings
- tests
- config links

### `GET /healthz`

### `GET /index/status`

---

## 7.2 Plugin ↔ Plan-Gate APIs

### `POST /v1/ask`

Input:

- task_type
- user query
- selection metadata
- workspace metadata
- structured context bundle
  Returns:
- grounded answer
- cited evidence IDs
- confidence / limitations
- optional follow-up suggestions

### `POST /v1/plan`

Input:

- intent
- structured context bundle
- governance envelope
  Returns:
- bounded plan
- rationale
- no execution

### `POST /v1/execute`

Input:

- approved action
- bounded patch intent
- structured context bundle
- policy envelope
  Returns:
- governed execution result
- audit IDs
- artifacts

---

## 7.3 Context Layer ↔ Retrieval Models (Optional, narrow)

These are acceptable.

### `POST /v1/embeddings`

Use for:

- query embeddings
- snippet embeddings
- semantic retrieval

### `POST /v1/rerank`

Use for:

- candidate reranking
- snippet prioritization

The Context Layer should **not** use general chat/completion APIs for user-visible answers.

---

## 8. Retrieval Pipeline (State-of-the-Art)

### Stage 1 — Intent decomposition

Input signals:

- task type
- natural-language query
- active file bias
- selected text bias
- symbol literals
- diagnostics context
- recent/open file history

### Stage 2 — Candidate generation

Parallel retrieval from:

- exact symbol index
- lexical search
- import graph neighbors
- call graph neighbors
- sibling/path proximity
- semantic search
- Git diff / recency bias
- config/test adjacency

### Stage 3 — Candidate scoring

Score by:

- exact symbol match
- path/module proximity
- graph distance
- semantic similarity
- active-file overlap
- selection overlap
- recency and editor focus
- test/config relevance

### Stage 4 — Snippet extraction

Extract:

- definition block
- surrounding context window
- caller/callee snippets
- config/constants nearby
- error-handling branches

### Stage 5 — Evidence bundle assembly

Assemble:

- files
- snippets
- reasons
- selector provenance
- workspace revision
- dirty-state metadata
- evidence graph

### Stage 6 — Upstream reasoning

Send only structured evidence bundle to Plan-Gate.

---

## 9. Canonical Context Bundle Shape

```json
{
  "workspace": {
    "repo_id": "aiops-agent",
    "repo_root": "/home/harshil/projects/aiops-agent",
    "revision": "abc123",
    "branch": "feature/x",
    "dirty": true
  },
  "task": {
    "type": "EXPLAIN",
    "query": "What does processFiles do in agent module?"
  },
  "selection": {
    "active_file": "agent/processor.py",
    "selected_span": null
  },
  "evidence": [
    {
      "file_path": "agent/processor.py",
      "symbol": "processFiles",
      "reasons": ["symbol_exact", "active_file", "callgraph_seed"],
      "snippets": [
        {
          "snippet_id": "snip-1",
          "kind": "definition",
          "start_line": 120,
          "end_line": 188,
          "content": "..."
        }
      ]
    }
  ],
  "selectors_used": ["symbol_exact", "callgraph", "imports", "semantic"]
}
```

This becomes the reasoning substrate for Plan-Gate and vLLM.

---

## 10. Capability Modes (Clear Split)

### Mode A — Local Structural Answer

Answered fully by Context Layer.
Examples:

- find symbol
- show references
- list callers
- show imports

### Mode B — Grounded Explanation

Context Layer retrieves evidence.
Plan-Gate + vLLM explain over that evidence.

### Mode C — Bounded Plan

Context Layer retrieves evidence.
Plan-Gate builds governed investigation plan.

### Mode D — Bounded Fix / Execute

Context Layer retrieves evidence.
Plan-Gate reasons, validates, and gates action.

This separates:

- **lookup**
- **understanding**
- **planning**
- **acting**

---

## 11. Incremental Indexing Strategy

The Context Layer should support:

- initial full repo scan
- per-file incremental re-index on save/change
- lazy graph updates for touched files
- revision-aware invalidation
- background semantic embedding updates
- dirty-file priority indexing

Key requirement:

> **Fresh enough for interactive developer use, deterministic enough for audit.**

---

## 12. Performance Strategy

### Low-latency path

For common Ask/Explain:

- precomputed symbol index
- lexical + graph retrieval first
- semantic retrieval only when needed
- bounded evidence size before GPU call

### High-quality path

For harder queries:

- semantic rerank
- graph expansion
- multi-snippet bundle
- evidence compression before Plan-Gate

### Principle

> Retrieve broadly, send narrowly.

---

## 13. Fine-Tuning / SFT / LoRA Position

### Do you need more SFT/LoRA to make this architecture work?

**Not as a prerequisite for the Context Layer architecture itself.**

The Context Layer is primarily a systems/indexing/retrieval problem.
You can build and validate it without another fine-tuning round.

### What fine-tuning helps with later

Additional SFT/LoRA may help once retrieval is strong and stable, specifically for:

- better explain/debug style
- better bounded-fix formatting
- improved refusal / governance phrasing
- stronger enterprise code reasoning over structured evidence bundles
- more consistent patch discipline

### What fine-tuning does NOT fix

Fine-tuning will NOT fix:

- weak retrieval
- bad symbol resolution
- missing snippet grounding
- wrong repo boundary
- poor evidence selection

### Recommended sequence

1. Build strong Context Layer first
2. Validate grounded evidence quality
3. Measure reasoning gaps
4. Then decide whether another SFT/LoRA pass is justified

So the answer is:

> **No, you do not need another SFT/LoRA iteration to define or implement the Context Layer architecture.**
> You may want one later to improve reasoning quality once retrieval is mature.

---

## 14. Revised Milestones

### Milestone 1 — Demo Closure on Current Stack

- Fix empty `context_bundle.files`
- Validate one grounded golden demo
- Keep current remote-repo workaround alive temporarily

### Milestone 2 — Workspace Intelligence MVP

- WSL service with repo resolution
- symbol lookup
- lexical retrieval
- snippet extraction
- revision + dirty-state reporting

### Milestone 3 — Structured Evidence Bundle Contract

- finalize plugin ↔ context layer contract
- finalize context layer ↔ Plan-Gate evidence schema

### Milestone 4 — Ask / Explain Refactor

- Ask uses WSL Context Layer
- Plan-Gate receives evidence, not repo-path assumptions

### Milestone 5 — Bounded Fix Enablement

- reuse grounded evidence bundle
- add bounded-fix reasoning path
- governed diff preview and execution flow

### Milestone 6 — Advanced Retrieval

- semantic retrieval
- reranking
- multi-language expansion
- graph-aware prioritization

### Milestone 7 — Reasoning Tuning (Only if needed)

- assess failure cases
- decide whether SFT/LoRA iteration adds real value

---

## 15. Final Decision

The final system should NOT rely on the GPU runtime directly reading a developer’s WSL repo.

The correct long-term architecture is:

- **Windows JetBrains Plugin** = interaction surface
- **WSL Context Layer** = workspace intelligence and code truth
- **GPU Plan-Gate + vLLM** = reasoning, governance, bounded action

This is the clean industry-grade split.

---

## 16. Final Takeaway

> **Move context closer to the code. Keep reasoning and governance close to the GPU.**

That is the architecture that will scale, remain auditable, and still feel like a state-of-the-art coding system.



--------------------------------------------------------------------------

Remarks:

Created in canvas.

On SFT/LoRA: **not yet required**.

The short truth is:

* **Context Layer quality is a systems problem first**

* **Reasoning quality becomes a tuning problem later**

So the right sequence is:

1. **Build the WSL Context Layer**

2. **Make retrieval/evidence bundles strong**

3. **Validate real Ask/Explain quality**

4. **Only then** decide whether another SFT/LoRA round is worth it

What fine-tuning can help later:

* cleaner explain/debug style

* better bounded-fix discipline

* more consistent governance phrasing

* stronger synthesis across structured evidence bundles

What it will **not** fix:

* weak retrieval

* missing symbols/files

* bad snippet selection

* wrong repo boundary

So the answer is:

> **No, further SFT/LoRA is not a prerequisite for this architecture change.**  
> It may become useful after the Context Layer is solid and you can clearly measure reasoning gaps.

The new canvas doc includes that decision and a revised milestone sequence.

-----------

Created in canvas.

On SFT/LoRA: **not yet required**.

The short truth is:

* **Context Layer quality is a systems problem first**

* **Reasoning quality becomes a tuning problem later**

So the right sequence is:

1. **Build the WSL Context Layer**

2. **Make retrieval/evidence bundles strong**

3. **Validate real Ask/Explain quality**

4. **Only then** decide whether another SFT/LoRA round is worth it

What fine-tuning can help later:

* cleaner explain/debug style

* better bounded-fix discipline

* more consistent governance phrasing

* stronger synthesis across structured evidence bundles

What it will **not** fix:

* weak retrieval

* missing symbols/files

* bad snippet selection

* wrong repo boundary

So the answer is:

> **No, further SFT/LoRA is not a prerequisite for this architecture change.**  
> It may become useful after the Context Layer is solid and you can clearly measure reasoning gaps.

The new canvas doc includes that decision and a revised milestone sequence.
