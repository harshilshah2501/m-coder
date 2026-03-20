
Here’s how the diagram, the current system, and the spec fit together.

---

## Diagram ↔ Current behavior

The diagram shows:

- **Remote server (GPU):** Plan-Gate :8089, vLLM :8000  
- **Local:** WSL (AIOps repo) + Windows JetBrains  
- **Plugin** talking to the GPU

The “communication gap” in the description is exactly the issue: **Plan-Gate builds `context_bundle` on the GPU server**, but the **repo lives in WSL**. So either:

- The server has no access to that path → `context_bundle.files` stays empty (or you rely on `ASK_DEFAULT_REPO_ROOT` with a synced copy on the server), or  
- You sync the repo to the GPU and treat the server as filesystem authority → works for demos but not for “real” WSL workspace.

So the diagram is an accurate picture of **today’s** architecture and why Repo-Aware Ask is brittle when the repo is only in WSL.

---

## How the spec fixes that

The spec is the **target** architecture that removes that gap.

**1. Same topology, different data flow**

- **Diagram:** Plugin → (directly?) → GPU (Plan-Gate + vLLM).  
- **Spec (§3):**  
  - Plugin → **Workspace Intelligence Layer (WSL)** → structured grounded context bundle  
  - Then that bundle → **Plan-Gate (GPU)** → vLLM → governed response back to plugin.

So the **physical** split (WSL repo, Windows IDE, GPU server) stays; the **logical** change is: **context is built in WSL where the code lives**, then only the **evidence bundle** is sent to the GPU.

**2. Who does what**

| Component | Diagram (current) | Spec (target) |
|----------|--------------------|----------------|
| **WSL** | Holds repo only | **Workspace Intelligence Layer**: retrieval, indexing, symbol/call/import graph, snippet extraction, evidence packaging. **Source of truth for code context.** |
| **Plugin** | Sends path + query to GPU | Calls **WSL Context Layer** for retrieval; sends **structured context bundle** to Plan-Gate; never expects GPU to read repo paths. |
| **Plan-Gate (GPU)** | Resolves `repo_root`, runs ContextEngine on server disk | Receives **structured evidence** only; no repo-path resolution; validation, governance, planning, explanation over the bundle. |
| **vLLM (GPU)** | Same | Reasoning over **grounded evidence**; not used for retrieval. |

So the diagram’s “Plan-Gate must either receive file content from the plugin or access WSL” is resolved by the spec: **Plan-Gate receives a pre-built evidence bundle** from the plugin (which got it from the WSL Context Layer). Plan-Gate never touches the WSL filesystem.

**3. Principle that matches the diagram**

Spec §2:

> **Code should be retrieved where it lives. Reasoning should happen where compute lives. Governance should happen where control lives.**

That’s exactly what the diagram needs: **retrieval in WSL**, **reasoning on GPU**.

**4. API boundary that fixes the gap**

- **Current:** Plugin sends `repo_root` (+ query, revision) → Plan-Gate resolves path on server → ContextEngine runs on server → often empty or server-side copy only.  
- **Spec (§7.1–7.2):**  
  - Plugin → **Context Layer (WSL):** e.g. `POST /context/retrieve` (query, active_file, selection, task_type) → returns ranked files, snippets, reasons, selectors_used, revision.  
  - Plugin → **Plan-Gate (GPU):** `POST /v1/ask` with **structured context bundle** (and query) → Plan-Gate returns grounded answer; it does **not** get a `repo_root` to resolve.

So the “context_bundle.files empty” issue goes away because the **bundle is built in WSL** and sent as payload, instead of the GPU trying to build it from a path it can’t see.

**5. Canonical bundle shape (§9)**

The spec’s bundle (workspace, task, selection, **evidence[]** with file_path, reasons, snippets, selectors_used) is what Plan-Gate and vLLM consume. That’s the “structured grounded context bundle” in the diagram’s intended flow: **WSL produces it, GPU consumes it.**

---

## Summary

- **Diagram:** Correct representation of current setup and why there’s a gap (repo in WSL, context built on GPU).  
- **Spec:** Defines the architecture that removes that gap by introducing the **Workspace Intelligence Layer in WSL** and changing the contract so Plan-Gate receives **evidence bundles** instead of repo paths.  
- **Milestones (§14):** M1 = fix current stack for demos; M2–M4 = WSL Context Layer MVP, evidence contract, Ask/Explain refactor so Ask uses WSL and Plan-Gate gets evidence only.

So the diagram and the spec are aligned: the diagram shows *why* the current design fails for WSL + Windows + GPU; the spec describes the final architecture where retrieval is local to the workspace and the GPU only does reasoning and governance on the context you send it.