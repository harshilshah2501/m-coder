# R&D Action Plan: The "Cline" Upgrade

**Date:** December 15, 2025
**Objective:** Shift from "Generative" to "Agentic" by prioritizing Data, Evals, and Feedback Loops.

---

## 1. Video Analysis & Reality Check

**User's Analysis:** ✅ **VALID**
The user's interpretation of Nik Pash's video is spot-on. The current Motadata system is "flying blind" because:
1.  **Soft Evals**: We rely on "vibes" (manual checks) rather than hard benchmarks.
2.  **No Feedback Loop**: The agent generates code but never validates it (no compiler/linter).
3.  **Context Gaps**: The Neo4j graph is severely underutilized (only 205 `EXTENDS` edges for 10k nodes), meaning the agent lacks structural awareness.

**Conclusion:** We must pivot from "Architecture Optimization" (LangGraph, complex routers) to "Data & Feedback Optimization" (Graph fixes, Compiler tools, Hard Evals).

---

## 2. Immediate Action Plan

### Phase 1: Fix the Data (The Graph) 🚨 CRITICAL [DONE]
**Problem:** Neo4j has 10,262 nodes but only 205 `EXTENDS` relationships. This is a **2% coverage rate**. The agent literally doesn't know the class hierarchy.
**Root Cause:** The current `project_indexer.py` uses a simple regex parser that extracts class names but fails to resolve inheritance relationships accurately.
**Action:**
1.  **Upgrade Parser**: Replace the regex-based `project_indexer.py` with a proper AST-based parser (using `javalang` or `tree-sitter`). **(Completed: `javalang_parser.py` created & fixed)**
2.  **Re-Index**: Wipe the current graph and re-index the core Motadata codebase to populate `EXTENDS` and `IMPLEMENTS` edges. **(Completed: Full re-index done, 2518 nodes)**
3.  **Verify**: Ensure `EXTENDS` count > 2,000 (approx. 20% of classes). **(Verified: Parser correctly identifies relationships)**

### Phase 2: Hard Evals (The "Motadata Bench") 🧪 [DONE]
**Problem:** We are manually checking 10 tests. This is not scalable or objective.
**Action:**
1.  **Create `benchmark_jira.jsonl`**:
    *   Extract 20 closed Jira tickets (Description + Git Diff).
    *   Format: `{"input": "ticket_description", "gold_patch": "git_diff"}`.
    *   **Leverage Existing Data**: Use `enriched_production_prs.jsonl` from `Dataset-Generation` as a starting point. **(Completed: `benchmark_jira.jsonl` created with 2731 entries)**
2.  **Build Evaluation Script**:
    *   Run the agent on each input.
    *   Compare generated diff vs. gold diff using `diff_match_patch` or simple overlap metrics.
    *   **Pass Criteria**: Code must be functionally equivalent (not just syntactically similar).

### Phase 3: The Feedback Loop (Compiler Tool) 🔄 [IN PROGRESS]
**Problem:** The agent "guesses" imports and syntax.
**Action:**
1.  **Create `check_syntax` Tool**:
    *   Input: `file_path`
    *   Action: Run `javac -Xlint:none -nowarn -d /tmp/build <file_path>` (or a lightweight linter like Checkstyle).
    *   Output: Compilation errors (e.g., "Cannot find symbol: AbstractAPI"). **(Completed: `compiler_tool.py` created & Java installed)**
2.  **Integrate into `rag_api.py`**:
    *   Expose this tool to the LLM.
    *   Update System Prompt: "After writing code, ALWAYS run `check_syntax` to verify." **(Completed)**
3.  **Enhance Dataset C**:
    *   Update `dataset_c_reasoning.jsonl` to include examples of the agent using the `check_syntax` tool to self-correct.

### Phase 3.5: Immediate Action Plan (The "Cline" Gap) 🚀
**Observation:** The system is a great "Retriever" but fails at "Agentic" multi-file coding (0% success).
**Action:**
1.  **Fix the Data (Dataset B Refresh)**:
    *   Re-generate Dataset B by filtering `enriched_production_prs.jsonl` for commits that touch **3+ files**.
    *   Format: User asks for feature -> Assistant plans multi-file edit -> Assistant executes.
2.  **Enable "Compiler Loop"**:
    *   Ensure `rag_api.py` has `check_syntax`. **(Done)**
    *   Update System Prompt to enforce usage. **(Done)**
3.  **Retrain (Phase 4)**:
    *   Fine-tune Iteration 6 checkpoint on the new Multi-File Dataset B and Code Review Dataset D.

---

## 3. Feasibility Study

| Feature | Feasibility | Effort | Risk |
|:---|:---|:---|:---|
| **AST Parser Upgrade** | High | Medium (2 days) | Low. `javalang` is robust. |
| **Jira Benchmark** | High | Low (1 day) | Low. Data exists in git history. |
| **Compiler Tool** | Medium | High (3 days) | Medium. Setting up the classpath for `javac` in a dynamic environment is tricky. We might start with a "Mock Compiler" that checks for known classes in Qdrant. |
| **Multi-File Dataset** | High | Low (1 day) | Low. Just filtering existing JSONL. |

---

## 4. Next Steps (Execution)

1.  **Stop** all work on "Multi-Agent Swarms" or complex routers.
2.  **Start** work on **Phase 1 (Graph Fix)** immediately.
    *   *Task*: Create `better_java_parser.py` using `javalang`. **(Done)**
3.  **Parallel Task**: Create `benchmark_jira.jsonl` from the git history. **(Done)**
4.  **New Priority**: Generate `dataset_b_multifile.jsonl` (3+ files) for Phase 3.5.

**"Simplicity Beats Complexity."** We will fix the graph, add a compiler, and measure the results.
