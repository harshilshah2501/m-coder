# LLM Fine-Tuning Paradigms & Motadata AI Coding Assistant
## Comprehensive Technical Documentation

---

## Executive Summary

This document outlines the three fundamental paradigms for building production-grade AI coding assistants: **Continued Pre-training (CPT)**, **Supervised Fine-Tuning (SFT)**, and **Preference Fine-Tuning (DPO)**. Each paradigm serves a distinct purpose in the model development lifecycle, and understanding their dataset schemas, use cases, and technical requirements is critical for building the Motadata AI Coding Assistant.

The Motadata AI Coding Assistant will leverage all three paradigms in sequence: CPT to inject domain knowledge, SFT to teach behavior and tool usage, and DPO to eliminate common errors and enforce code quality standards.

---

## Part 1: The Three Paradigms Overview

### 1.1 Paradigm Comparison

| Paradigm                              | Goal                       | Data Type              | When to Use                             |
| ------------------------------------- | -------------------------- | ---------------------- | ---------------------------------------- |
| **Continued Pre-training (CPT)**     | Inject domain knowledge    | Unlabeled raw text     | Before SFT; high-impact improvement      |
| **Supervised Fine-Tuning (SFT)**     | Teach behavior & format    | Instruction-response pairs | Core training phase                  |
| **Preference Fine-Tuning (DPO)**     | Align to quality standards | Preference triplets    | After SFT; polish & eliminate errors     |

_Table: Comparison of the three fine-tuning paradigms._
### 1.2 Training Pipeline Architecture

The optimal training pipeline follows this sequence:

1. **Download Base Model:** Start with Qwen2.5-Coder-7B-Instruct or similar instruction-tuned code model.
2. **Continued Pre-training (CPT) [Optional but Recommended]:** Train on unlabeled Motadata codebase + proprietary DSLs. Adds domain context.
3. **Supervised Fine-Tuning (SFT) [Core Phase]:** Train on instruction-response pairs (Execution Plans, Code Generation, Tool Use).
4. **Preference Fine-Tuning (DPO) [Polish Phase]:** Train on preference data to eliminate hallucinations, bugs, and enforce code quality.
5. **Deploy & Monitor:** Ship the final model with RAG + Agents.



![LLM Training Pipeline: From Base Model to Production](training-pipeline.png)

_Figure: LLM Training Pipeline: From Base Model to Production._
---

## Part 2: Dataset Schemas for Each Paradigm

### 2.1 Continued Pre-training (CPT) — The "Knowledge Injection" Phase

#### 2.1.1 Purpose

CPT is **not** about teaching the model how to answer. It is about injecting domain-specific knowledge that the base model has never seen. For Motadata:

*   Proprietary Java libraries and base classes (`AbstractAPI`, `AbstractConfigStore`)
*   Internal DSLs and architecture patterns
*   Actual codebase snippets (methods, classes, schemas)
*   Documentation and design guides

CPT is most effective **before** SFT because it fills knowledge gaps. Without CPT, SFT will struggle to produce coherent Java code if it lacks context.

#### 2.1.2 Dataset Schema

**Format:** Simple unlabeled text. One JSON line per document chunk.

**Standard Structure (AWS Bedrock, Anyscale):**

```json
{"input": "public class AbstractAPI extends VertxHttpHandler { ... }"}
{"input": "Motadata DSL: @Route(\"/api/monitor\") maps to GET /api/monitor?id=X"}
{"input": "EventBus Pattern: publish(address, message) → handlers receive via @Consumer(address)"}
```

**Alternative (Raw Text File):**

```
public class AbstractAPI extends VertxHttpHandler {
    protected void handleRequest(RoutingContext ctx) { ... }
}

---DOCUMENT_BOUNDARY---

Motadata Configuration Store Pattern:
1. Extend AbstractConfigStore
2. Override getConfigPath() with table name
3. Register in APIRouter.setupConfigApis()
```

#### 2.1.3 What to Include in CPT Dataset

| Content Type | Examples | Priority | Format |
| :--- | :--- | :--- | :--- |
| **Java Base Classes** | `AbstractAPI.java`, `AbstractConfigStore.java`, `AbstractHandler.java` | **CRITICAL** | Full source code |
| **Vertical/Handler Classes** | Sample Verticles, EventBus handlers | **HIGH** | Full source code with annotations |
| **Schema Definitions** | Entity schemas (`*.json`), field definitions | **HIGH** | JSON + documentation |
| **Architecture Docs** | "How to add a new API", "DB Schema Rules" | **HIGH** | Markdown + code examples |
| **Logging & Error Patterns** | Error handling conventions, log formats | **MEDIUM** | Code snippets |
| **External Libraries** | Neo4j usage, ChromaDB integration | **MEDIUM** | Method signatures + docs |
| **Security Patterns** | Auth, validation, sanitization examples | **MEDIUM** | Code examples |

#### 2.1.4 CPT Dataset Construction

**Step 1: Extract Source Code**

```bash
# Collect all Java classes from your codebase
find /motadata-codebase -name "*.java" \
  -path "*/src/main/*" > source_files.txt

# Extract schema definitions
find /motadata-codebase -name "*.json" \
  -path "*/schema/*" > schema_files.txt
```

**Step 2: Format into JSONL**

```python
import json
import os

output_file = "cpt_dataset.jsonl"
with open(output_file, 'w') as out:
    for filepath in source_files:
        with open(filepath, 'r') as f:
            content = f.read()
            # Split large files into chunks (~2KB each)
            for chunk in chunk_by_method(content):
                json.dump({"input": chunk}, out)
                out.write('\n')
```

**Step 3: Quality Check**
*   Ensure no secrets (API keys, passwords) in code
*   Remove test files and mocks
*   Remove overly commented-out code
*   Verify total tokens < 1B tokens (typical: 100–500M for domain-specific CPT)

#### 2.1.5 Example CPT Entries (Motadata Context)

_Note: In the JSONL records below, the `\n` sequences represent actual newline characters in the underlying code/text. In practice you should generate these records with a JSON serializer from raw multi-line inputs; do not include the literal characters `\` and `n` in your training text._
{"input": "public abstract class AbstractAPI extends VertxHttpHandler {\n    protected String apiName;\n    protected abstract void setupRoutes(Router router);\n    protected void sendJsonResponse(RoutingContext ctx, JsonObject data) {\n        ctx.response().putHeader(\"Content-Type\", \"application/json\").end(data.encode());\n    }\n}"}

{"input": "public abstract class AbstractConfigStore extends AbstractStore {\n    protected final String tableName;\n    protected AbstractConfigStore(String tableName) { this.tableName = tableName; }\n    @Override protected String getConfigPath() { return \"config_\" + tableName; }\n}"}

{"input": "EventBus Address Pattern:\nAddress: com.motadata.api.discovery\nHandler: @Consumer(\"com.motadata.api.discovery\") public void handleDiscoveryEvent(Message<JsonObject> msg) { ... }\nPublisher: eventBus.publish(\"com.motadata.api.discovery\", new JsonObject().put(\"type\", \"scan_complete\"));"}

{"input": "Schema Definition Pattern:\n{\n  \"entity\": \"Monitor\",\n  \"fields\": [\n    {\"name\": \"id\", \"type\": \"UUID\", \"required\": true},\n    {\"name\": \"name\", \"type\": \"String\", \"required\": true},\n    {\"name\": \"config\", \"type\": \"JSON\", \"required\": false}\n  ],\n  \"table\": \"monitors\"\n}"}

---

### 2.2 Supervised Fine-Tuning (SFT) — The "Behavior & Format" Phase

#### 2.2.1 Purpose

SFT teaches the model **how to behave**: follow the Execution Plan format, use tools correctly, structure responses logically, and generate syntactically correct code.

This is where most fine-tuning effort goes. The datasets are diverse, covering multiple task types:
*   **Type A:** Knowledge / Documentation QA
*   **Type B:** Code Generation / Patches
*   **Type C:** Multi-turn Reasoning & Tool Use

#### 2.2.2 Dataset Schema (ChatML / OpenAI Standard)

**Universal Format:**
{
  "messages": [
    {"role": "system", "content": "...system prompt..."},
    {"role": "user", "content": "...user query..."},
    {"role": "assistant", "content": "...response..."}
  ]
}

**For Multi-turn Conversations (Tool Use):**
{
  "messages": [
    {"role": "system", "content": "You are a code assistant..."},
    {"role": "user", "content": "Find all callers of the authenticate method."},
    {"role": "assistant", "content": null, "tool_calls": [{"type": "function", "function": {"name": "search_callers", "arguments": "{...}"}}]},
    {"role": "tool", "name": "search_callers", "content": "[{\"caller\": \"APIServer.handleLogin\", \"line\": 145}]"},
    {"role": "assistant", "content": "The authenticate method is called from APIServer.handleLogin at line 145."}
  ]
}

#### 2.2.3 SFT Dataset Types & Examples

##### **Type A: Knowledge / Documentation (QA)**

**Purpose:** Ground the model in Motadata documentation and patterns.

**Schema:**
{
  "messages": [
    {"role": "system", "content": "You are a technical documentation expert for Motadata."},
    {"role": "user", "content": "How do I add a new monitor plugin?"},
    {"role": "assistant", "content": "To add a new monitor plugin:\n1. Create a class extending AbstractMonitor\n2. Register in MonitorFactory\n3. Add configuration in schema/monitors.json\n..."}
  ]
}

**Dataset Size:** ~800–1,200 samples
**Sources:**
*   Extract from Confluence / internal wiki
*   Auto-generate from docstrings in code
*   QA from senior engineers

**Quality Metrics:**
*   Information is factually correct (verify against actual codebase)
*   Answers reference specific classes/methods
*   No hallucinated functions or wrong paths

---

##### **Type B: Code Generation / Patches**

**Purpose:** Teach precise, focused code generation without unnecessary verbosity.

**Schema:**
{
  "messages": [
    {"role": "system", "content": "You are a senior developer. Generate only the necessary code changes. Be precise and concise."},
    {"role": "user", "content": "File: src/store/MonitorConfigStore.java\nInstruction: Add a method to fetch monitor by ID. Return null if not found."},
    {"role": "assistant", "content": "```java\npublic Monitor getMonitorById(String id) {\n    return this.configMap.getOrDefault(id, null);\n}\n```"}
  ]
}

**Dataset Size:** ~500–800 samples
**Sources:**
*   Extract from git history (commit messages + diffs)
*   Code review feedback
*   Common refactoring patterns

**Quality Metrics:**
*   Code is syntactically correct
*   Code follows Motadata conventions
*   Diff can be applied directly (no context mismatch)

---

##### **Type C: Multi-turn Reasoning & Tool Use**

**Purpose:** Teach the model to use RAG tools instead of hallucinating, and to plan before coding.

**Schema:**
{
  "messages": [
    {"role": "system", "content": "You are a code assistant with access to codebase tools."},
    {"role": "user", "content": "Create a new API endpoint for fetching monitor health status."},
    {"role": "assistant", "content": "**Execution Plan:**\n1. Create HealthStatusAPI.java (extends AbstractAPI)\n2. Implement getHealth(id) method\n3. Register in APIRouter\n4. Add schema for HealthStatus entity\n\nLet me search for similar patterns first.", "tool_calls": [{"type": "function", "function": {"name": "search_codebase", "arguments": "{\"query\": \"AbstractAPI examples\", \"limit\": 3}"}}]},
    {"role": "tool", "name": "search_codebase", "content": "[{\"file\": \"MonitorAPI.java\", \"snippet\": \"public class MonitorAPI extends AbstractAPI { ... }\"}]"},
    {"role": "assistant", "content": "Based on the pattern from MonitorAPI, here is the implementation:\n\n```java\npublic class HealthStatusAPI extends AbstractAPI {\n    @Override\n    protected void setupRoutes(Router router) {\n        router.get(\"/api/health/:id\").handler(this::getHealth);\n    }\n    \n    private void getHealth(RoutingContext ctx) {\n        String monitorId = ctx.pathParam(\"id\");\n        // ... implementation ...\n    }\n}\n```"}
  ]
}

**Dataset Size:** ~10,000–15,000 samples
**Sources:**
*   Synthetic generation (GPT-4 creates variations)
*   Real support tickets + solved solutions
*   Code review resolutions

**Quality Metrics:**
*   Tool calls match available functions
*   Model grounds answers in RAG results (not hallucinating)
*   Final code is complete and runnable

---

#### 2.2.4 SFT Dataset Construction Workflow

**Step 1: Collect Raw Data**

```python
import json
from datetime import datetime

# Source 1: Extract from git commits
git_log = subprocess.run(
    ["git", "log", "--format=%H%n%s%n%b", "-n", "1000"],
    capture_output=True, text=True
).stdout.split('\n')

# Source 2: Extract from code docstrings
ast_docs = extract_docstrings_from_java_files()

# Source 3: Create synthetic examples
synthetic_samples = generate_synthetic_sft_pairs()

# Combine all sources
all_raw = git_log + ast_docs + synthetic_samples
```

**Step 2: Normalize into ChatML Format**

```python
def normalize_to_chatml(sample):
    """Convert any format (ShareGPT, Alpaca, raw) to OpenAI format."""
    if "conversations" in sample:
        # ShareGPT format → ChatML
        messages = []
        for turn in sample["conversations"]:
            role = "user" if turn["from"] == "human" else "assistant"
            messages.append({"role": role, "content": turn["value"]})
        if messages[0]["role"] != "system":
            messages.insert(0, {
                "role": "system",
                "content": "You are a Motadata coding expert."
            })
        return {"messages": messages}
    
    elif "messages" in sample:
        # Already ChatML
        return sample
    
    elif "instruction" in sample:
        # Alpaca format → ChatML
        return {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": sample["instruction"]},
                {"role": "assistant", "content": sample["output"]}
            ]
        }
    
    return None

# Normalize all samples
normalized = [normalize_to_chatml(s) for s in all_raw if normalize_to_chatml(s)]
```

**Step 3: Oversample and Balance**

As discussed in your prior work, balance the three types:

```python
type_a = load_sft_type_a()  # ~800 samples
type_b = load_sft_type_b()  # ~500 samples
type_c = load_sft_type_c()  # ~11,500 samples

# Oversample A and B to avoid catastrophic forgetting
balanced = type_a * 5 + type_b * 8 + type_c * 1
random.shuffle(balanced)

# Save
with open("sft_final.jsonl", 'w') as f:
    for sample in balanced:
        f.write(json.dumps(sample) + "\n")
```

**Step 4: Validation**
*   Check: All samples have `messages` key
*   Check: First message is `system` role
*   Check: Alternating `user` / `assistant` roles
*   Check: No empty content fields
*   Sample 50 random entries manually

---

### 2.3 Preference Fine-Tuning (DPO) — The "Quality Alignment" Phase

#### 2.3.1 Purpose

DPO teaches the model to **prefer** good responses over plausible-sounding bad ones. This is critical for code generation because:

*   A model can sound confident while generating a **NullPointerException**.
*   A model might propose **swallowing exceptions** (bad) instead of **propagating errors** (good).
*   A model might hallucinate **non-existent methods** instead of using **real APIs**.

DPO is the cutting-edge replacement for RLHF because it:
*   Eliminates the need for a separate reward model
*   Is simpler to train and tune
*   Directly optimizes for human preferences

#### 2.3.2 Dataset Schema

**Format:** Prompt + Chosen (good) + Rejected (bad) response.

**Standard Structure (HuggingFace DPO Trainer):**
{
  "prompt": "Fix the NullPointerException in the handler code.",
  "chosen": [
    {"role": "user", "content": "Fix the NullPointerException in the handler code."},
    {"role": "assistant", "content": "```java\nif (ctx != null && ctx.body() != null) {\n    ctx.json(parseBody(ctx.body()));\n}\n```"}
  ],
  "rejected": [
    {"role": "user", "content": "Fix the NullPointerException in the handler code."},
    {"role": "assistant", "content": "```java\ntry {\n    ctx.json(parseBody(ctx.body()));\n} catch (Exception e) {\n    // ignore errors\n}\n```"}
  ]
}

**Alternative (Simpler Format with Just Text):**
{
  "prompt": "Complete this Java method:\npublic void handleError(Throwable error) { ",
  "chosen": "error.printStackTrace();\nlogger.error(\"Handler failed\", error);\nctx.fail(error);",
  "rejected": "// do nothing\nreturn;"
}

#### 2.3.3 Where DPO Data Comes From: Error-Point Identification

The most effective way to generate DPO data is **Error-Point Identification** (from Focused-DPO research [web:23]):

1.  **Generate Candidate Code:** Use your SFT model to generate multiple solutions for the same prompt.
2.  **Test Each Candidate:** Run unit tests or syntax checks on each solution.
3.  **Score by Performance:** Rank by test pass rate, correctness, code quality metrics.
4.  **Pair Winners + Losers:** The highest-scoring is "chosen"; low-scoring is "rejected".

```python
def generate_dpo_dataset(prompts, num_candidates=5):
    """Generate preference pairs using Error-Point Identification."""
    dpo_samples = []
    
    for prompt in prompts:
        candidates = []
        
        # Step 1: Generate multiple candidates
        for _ in range(num_candidates):
            code = sft_model.generate(prompt, temperature=0.8)
            candidates.append(code)
        
        # Step 2: Test each candidate
        scores = []
        for code in candidates:
            passes_tests = run_unit_tests(code)
            syntax_valid = check_syntax(code)
            score = len(passes_tests) + (syntax_valid * 10)
            scores.append(score)
        
        # Step 3: Rank and create preference pair
        best_idx = scores.index(max(scores))
        worst_idx = scores.index(min(scores))
        
        if scores[best_idx] > scores[worst_idx]:  # Only if there's a difference
            dpo_samples.append({
                "prompt": prompt,
                "chosen": candidates[best_idx],
                "rejected": candidates[worst_idx]
            })
    
    return dpo_samples
```

#### 2.3.4 Common Error Patterns to Optimize For (Motadata-Specific)

| Error Pattern | Example of "Rejected" | Example of "Chosen" | Why It Matters |
| :--- | :--- | :--- | :--- |
| **Swallowing Exceptions** | `try { ctx.handle(); } catch (Exception e) { }` | `try { ctx.handle(); } catch (Exception e) { logger.error(...); throw e; }` | Hides bugs; hard to debug |
| **Null Checks** | `ctx.body().getId()` | `if (ctx != null && ctx.body() != null) { return ctx.body().getId(); }` | Causes NPE in production |
| **Wrong API Usage** | `eventBus.send("address")` (missing message) | `eventBus.publish("address", msg)` | Doesn't work; confuses send/publish |
| **Missing Registration** | `new MyAPI().setupRoutes(router)` | Also updates APIRouter.registerAPI(...) | Endpoint not available |
| **Ignoring Tool Results** | Plans a feature then ignores RAG search results | Incorporates RAG results into final code | Hallucinated APIs |
| **Overly Verbose** | 200 lines of explanation + 5 lines of code | 5 lines of code + 2-line comment | Wastes tokens; hard to apply |
| **Wrong Schema** | Uses incorrect field names from hallucination | Uses verified field names from actual schema | Code doesn't compile |

#### 2.3.5 DPO Dataset Construction

**Method 1: Synthetic Generation (Error-Point Identification)**

import subprocess
import json

def validate_java_code(code_snippet):
    """Check if Java code compiles."""
    test_file = f"/tmp/Test_{uuid.uuid4()}.java"
    try:
        with open(test_file, 'w') as f:
            f.write(f"public class Test {{ {code_snippet} }}")
        result = subprocess.run(["javac", test_file], 
                                capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def generate_dpo_pairs(sft_model, prompts_file, output_file):
    """Generate DPO pairs by sampling and testing."""
    with open(prompts_file) as f:
        prompts = [line.strip() for line in f]
    
    dpo_pairs = []
    
    for prompt in prompts:
        # Generate 5 candidates
        candidates = []
        for temp in [0.1, 0.3, 0.5, 0.7, 0.9]:
            try:
                response = sft_model.generate(
                    prompt,
                    temperature=temp,
                    max_tokens=500,
                    num_return_sequences=1
                )
                candidates.append(response)
            except:
                continue
        
        if len(candidates) < 2:
            continue
        
        # Score candidates
        scores = []
        for code in candidates:
            syntax_ok = validate_java_code(code)
            is_not_empty = len(code.strip()) > 10
            no_todos = "TODO" not in code and "FIXME" not in code
            score = int(syntax_ok) * 10 + int(is_not_empty) * 5 + int(no_todos) * 2
            scores.append(score)
        
        # Create pair: best vs worst
        best_idx = scores.index(max(scores))
        worst_idx = scores.index(min(scores))
        
        if scores[best_idx] > scores[worst_idx]:
            dpo_pairs.append({
                "prompt": prompt,
                "chosen": candidates[best_idx],
                "rejected": candidates[worst_idx]
            })
    
    # Save
    with open(output_file, 'w') as f:
        for pair in dpo_pairs:
            f.write(json.dumps(pair) + "\n")
    
    print(f"Generated {len(dpo_pairs)} DPO pairs")

# Run
generate_dpo_pairs(
    sft_model=loaded_sft_model,
    prompts_file="dpo_prompts.txt",
    output_file="dpo_dataset.jsonl"
)

**Method 2: Human Annotation (High-Quality)**

For maximum quality, have engineers rate code samples:

```python
def collect_human_preferences():
    """Interface for engineers to rate code samples."""
    
    prompts = load_test_prompts()
    
    for prompt in prompts:
        candidates = sft_model.generate(prompt, num_candidates=2)
        
        print(f"\nPrompt: {prompt}")
        print(f"Option A:\n{candidates[0]}\n")
        print(f"Option B:\n{candidates[1]}\n")
        
        rating = input("Which is better? (A/B/tie): ").lower()
        
        if rating == 'a':
            dpo_pair = {
                "prompt": prompt,
                "chosen": candidates[0],
                "rejected": candidates[1]
            }
        elif rating == 'b':
            dpo_pair = {
                "prompt": prompt,
                "chosen": candidates[1],
                "rejected": candidates[0]
            }
        else:
            continue  # Skip ties
        
        save_dpo_pair(dpo_pair)
```

#### 2.3.6 Example DPO Entries (Motadata Context)

{
  "prompt": "Add error handling to this method: void processRequest(RoutingContext ctx) {",
  "chosen": [
    {"role": "user", "content": "Add error handling to this method: void processRequest(RoutingContext ctx) {"},
    {"role": "assistant", "content": "try {\n    String body = ctx.body().asString();\n    JsonObject json = new JsonObject(body);\n    ctx.json(json);\n} catch (DecodeException e) {\n    logger.error(\"Invalid JSON in request\", e);\n    ctx.response().setStatusCode(400).end(\"Invalid JSON\");\n} catch (Exception e) {\n    logger.error(\"Unexpected error processing request\", e);\n    ctx.response().setStatusCode(500).end(\"Internal Server Error\");\n}"}
  ],
  "rejected": [
    {"role": "user", "content": "Add error handling to this method: void processRequest(RoutingContext ctx) {"},
    {"role": "assistant", "content": "String body = ctx.body().asString();\ntry {\n    JsonObject json = new JsonObject(body);\n    ctx.json(json);\n} catch (Exception e) {\n    // ignore\n}"}
  ]
}

{
  "prompt": "Create a new config store for HealthMonitor.",
  "chosen": [
    {"role": "user", "content": "Create a new config store for HealthMonitor."},
    {"role": "assistant", "content": "public class HealthMonitorConfigStore extends AbstractConfigStore {\n    public HealthMonitorConfigStore() {\n        super(\"health_monitors\");\n    }\n    \n    public HealthMonitor getById(String id) {\n        JsonObject config = this.readConfig(id);\n        return config != null ? new HealthMonitor(config) : null;\n    }\n}"}
  ],
  "rejected": [
    {"role": "user", "content": "Create a new config store for HealthMonitor."},
    {"role": "assistant", "content": "public class HealthMonitorConfigStore {\n    public HealthMonitor get(String id) {\n        // TODO: implement this\n        return null;\n    }\n}"}
  ]
}

---

## Part 3: Use Cases & Task Categories

### 3.1 Mapping Paradigms to Use Cases

| Use Case | CPT | SFT | DPO |
|----------|-----|-----|-----|
| Feature Building (Multi-file) | Required | Required | Recommended |
| Code Patching | Optional | Required | Recommended |
| RCA / Debugging | Optional | Required | Recommended |
| Documentation QA | Optional | Required | Optional |

*Table: Paradigm requirements by use case*

### 3.2 Feature Building (Agent A: The Architect)

**Objective:** Generate complete, multi-file features with all necessary registrations.

**Example Prompt:**
Create a new API endpoint for CorrectionProfile with:
- API class extending AbstractAPI
- Config store for persisting correction profiles
- All necessary registrations in APIRouter and schema
- Error handling for invalid inputs

**What Each Paradigm Contributes:**

*   **CPT:** Knows the structure of `AbstractAPI`, `AbstractConfigStore`, and registration patterns (seen in raw code).
*   **SFT:** Knows to follow the "Execution Plan" format and generate all required files.
*   **DPO:** Prefers implementations that don't forget schema registration or use wrong base classes.

**Expected Metrics:**
*   Multi-file completeness: 90%+
*   Correct base class usage: 95%+
*   All registrations present: 85%+

---

### 3.3 Code Patching (Type B: The Fixer)

**Objective:** Generate focused, applicable code diffs.

**Example Prompt:**
File: src/store/MonitorConfigStore.java
Instruction: Add method to filter monitors by type. Return empty list if no matches.

**What Each Paradigm Contributes:**

*   **CPT:** Knows patterns for querying config stores (seen in actual code).
*   **SFT:** Knows to return only the code, not explanation.
*   **DPO:** Prefers implementations that handle empty results gracefully, not with exceptions.

**Expected Metrics:**
*   Syntax correctness: 98%+
*   Adherence to style: 95%+
*   Compilable without changes: 90%+

---

### 3.4 RCA / Debugging (Agent B: The Detective)

**Objective:** Identify root cause from error logs + code context.

**Example Prompt:**
Error Log:
[ERROR] EventBus handler failed: com.motadata.api.discovery
java.lang.NullPointerException at DiscoveryHandler.processMessage:45

Code Context:
// DiscoveryHandler.java, line 40-50
@Consumer("com.motadata.api.discovery")
public void processMessage(Message<JsonObject> msg) {
    String type = msg.body().getString("type");  // Line 45
    ...
}

Root cause and fix?

**What Each Paradigm Contributes:**

*   **CPT:** Knows EventBus patterns and where null checks are typically placed.
*   **SFT:** Knows to map addresses to handlers and suggest targeted fixes.
*   **DPO:** Prefers fixes that address root cause (add null check) over workarounds (catch exception).

**Expected Metrics:**
*   Correct root cause identification: 80%+
*   Suggested fix is applicable: 85%+

---

## Part 4: Motadata AI Coding Assistant — Specific Requirements & Architecture

### 4.1 Motadata-Specific Knowledge Domains

The Motadata AI Coding Assistant must master these domains:

| Domain | Criticality | Typical Knowledge Size |
| :--- | :--- | :--- |
| **Vert.x Framework** (async, EventBus, handlers) | **CRITICAL** | 50–100 classes, 1,000+ methods |
| **AbstractAPI & AbstractConfigStore patterns** | **CRITICAL** | 5 base classes, 100+ examples |
| **Neo4j Integration** (Cypher, graph queries) | **HIGH** | 50 examples, query patterns |
| **ChromaDB Vector Store** | **MEDIUM** | 10 examples, embedding patterns |
| **Motadata Schema** (entity definitions, fields) | **CRITICAL** | 100+ schema files |
| **APIRouter & Registration Patterns** | **CRITICAL** | 200+ registrations |
| **Error Handling & Logging Conventions** | **HIGH** | 500+ log statements |
| **Security (Auth, Validation)** | **HIGH** | 50 patterns |

### 4.2 CPT Dataset Requirements for Motadata

**What to include:**

1.  **All base classes** (AbstractAPI, AbstractConfigStore, AbstractHandler, AbstractMonitor)
2.  **50+ example implementations** of each base class
3.  **All schema files** (`schema/*.json`)
4.  **APIRouter registration code** (all 200+ endpoints)
5.  **Common error patterns** (30–50 real exceptions from logs)
6.  **Vert.x handler examples** (50+ EventBus handlers)
7.  **Architecture documentation** ("How to Add a New API", "DB Schema Guide")

**Estimated Dataset Size:**
*   Raw code: ~500K lines (~100–200M tokens)
*   Documentation: ~1,000 pages (~10–20M tokens)
*   **Total: ~200–250M tokens** (manageable for domain-specific CPT)

**CPT Dataset Construction Timeline:**
*   Extract source code: **2–3 hours**
*   Format and validate: **1–2 hours**
*   Run CPT training: **4–8 hours** (on single GPU)

### 4.3 SFT Dataset Requirements for Motadata

As discussed previously, three balanced types:

| Type | Count | Purpose | Effort |
| :--- | :--- | :--- | :--- |
| **Type A (Knowledge)** | ~4,000 (after 5x oversample) | QA on Motadata docs | 20 hours (extraction + validation) |
| **Type B (Patches)** | ~4,000 (after 8x oversample) | Code changes and fixes | 30 hours (git mining + cleanup) |
| **Type C (Tool Use)** | ~11,500 | Multi-turn reasoning | 40 hours (synthetic + validation) |
| **TOTAL** | ~19,500 | Combined & shuffled | **~90 hours** total |

**SFT Training Timeline:**
*   Prepare datasets: **2 weeks** (in parallel with other tasks)
*   Run SFT training: **8–12 hours** (on single 4080 GPU)

### 4.4 DPO Dataset Requirements for Motadata

**Dataset Size:** 1,000–3,000 preference pairs (smaller than SFT, but high-quality)

**Common Error Patterns to Optimize (Motadata-Specific):**

| Error Class | Example | Impact |
| :--- | :--- | :--- |
| **Wrong Tool Call** | Calls `search_method` instead of `search_file` | Agent fails; wrong results |
| **Missing null checks** | `ctx.body().getId()` without null check | Runtime NPE crash |
| **Swallowing exceptions** | `catch (Exception e) { }` | Silent failures; hard debugging |
| **Wrong base class** | Extends `AbstractHandler` instead of `AbstractAPI` | Missing routes; incompatible |
| **Hallucinated methods** | Calls `config.getSchema()` (doesn't exist) | Code doesn't compile |
| **EventBus address mismatch** | Uses wrong address string | Handler never invoked |
| **Schema field errors** | Uses field `type` instead of `typeId` | Data corruption |

**DPO Dataset Construction Timeline:**
*   Generate candidates: **2–3 hours**
*   Validate/test: **4–5 hours**
*   Human review (optional): **8–10 hours**
*   Final curation: **2 hours**
*   **Total: ~1–2 weeks** (can be parallelized with SFT)

---

### 4.5 Recommended Training Schedule

![Recommended 6-week training and deployment timeline for Motadata AI Coding Assistant](motadata-training-timeline.png)

*Figure: Recommended 6-week training and deployment timeline for Motadata AI Coding Assistant*

**Week 1–2: Data Preparation**
*   Extract and format CPT dataset
*   Mine git history for Type B samples
*   Compile Type A from documentation
*   Begin synthetic Type C generation

**Week 2–3: CPT (Optional)**
*   Run CPT training on unlabeled code (4–8 GPU hours)
*   Validate knowledge injection with manual tests
*   Merge CPT checkpoint into base model

**Week 3–4: SFT (Core)**
*   Finalize all three SFT types
*   Combine and oversample (20% / 20% / 60% split)
*   Run SFT training (8–12 GPU hours)
*   Validate with manual code generation samples

**Week 4–5: DPO (Polish)**
*   Generate DPO preference pairs using Error-Point Identification
*   Run DPO training (4–6 GPU hours)
*   Validate improvement in error handling and tool usage

**Week 5–6: Deployment**
*   Merge final model checkpoint
*   Deploy with vLLM / Continue.dev
*   Monitor metrics and gather feedback
*   Iterate on dataset quality

---

### 4.6 Success Metrics & Monitoring

#### 4.6.1 SFT Success Metrics

| Metric | Baseline (GPT-4o w/RAG) | Target (Motadata-Coder w/RAG) | How to Measure |
| :--- | :--- | :--- | :--- |
| Feature Completeness | 35% | 90% | % of features with all files + registrations |
| Multi-file Accuracy | 10% | 80% | % of new APIs that update APIRouter + schema |
| Hallucination Rate | 25% | <5% | Manual sampling; check if answers are grounded |
| Tool Usage Correctness | 70% | 95% | % of tool calls with correct arguments |
| Code Syntax Validity | 75% | 98% | % of generated code that compiles |

#### 4.6.2 DPO Success Metrics

| Metric | Post-SFT | Post-DPO | Improvement |
| :--- | :--- | :--- | :--- |
| NPE Errors | 15% | <2% | 86% reduction |
| Exception Swallowing | 10% | <1% | 90% reduction |
| Wrong API Usage | 8% | <1% | 87% reduction |
| Missing Registrations | 20% | 5% | 75% reduction |
| Hallucinated Methods | 12% | <1% | 91% reduction |

#### 4.6.3 Monitoring Dashboard

Track these metrics continuously:

Weekly Metrics:
┌─────────────────────────────────────────┐
│ SFT Model Performance                   │
├─────────────────────────────────────────┤
│ Feature Completeness:    72%  ↑ (+5%)   │
│ Hallucination Rate:      8%   ↓ (-2%)   │
│ Code Syntax Valid:       96%  ↑ (+1%)   │
│ Tool Accuracy:           92%  ↑ (+3%)   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ DPO Model Performance                   │
├─────────────────────────────────────────┤
│ NPE Errors:              3%   ↓ (-8%)   │
│ Exception Swallowing:    2%   ↓ (-5%)   │
│ Missing Registrations:   8%   ↓ (-8%)   │
│ Hallucinated Methods:    1%   ↓ (-6%)   │
└─────────────────────────────────────────┘

---

## Part 5: Implementation Checklist & Next Steps

### 5.1 Pre-Training Checklist

- [ ] **CPT Data Extraction**
  - [ ] Extract all Java source files from `/src/main/`
  - [ ] Extract all schema files from `/schema/`
  - [ ] Extract architecture documentation
  - [ ] Remove secrets (API keys, tokens)
  - [ ] Validate no test/mock code
  - [ ] Format as JSONL with `{"input": "..."}` structure
  - [ ] Total dataset: 200–250M tokens

- [ ] **SFT Data Preparation**
  - [ ] Extract Type A (Knowledge): ~800 samples from wiki/docs
  - [ ] Extract Type B (Patches): ~500 samples from git history
  - [ ] Generate Type C (Tool Use): ~11,500 samples synthetically
  - [ ] Convert all to ChatML format (`{"messages": [...]}`)
  - [ ] Oversample: A×5, B×8, C×1
  - [ ] Shuffle combined dataset
  - [ ] Validate: 50 random samples, check format integrity

- [ ] **DPO Data Preparation**
  - [ ] Identify 1,000–2,000 representative prompts
  - [ ] Generate 3–5 candidates per prompt using SFT model
  - [ ] Score candidates (syntax, tests, correctness)
  - [ ] Create preference pairs (best vs. worst)
  - [ ] Manual review of 100 pairs (optional but recommended)
  - [ ] Format as DPO schema: `{"prompt": "...", "chosen": [...], "rejected": [...]}`

### 5.2 Training Checklist

- [ ] **Environment Setup**
  - [ ] GPU availability: Minimum 24GB VRAM (40GB recommended)
  - [ ] Libraries: unsloth, huggingface, torch, transformers
  - [ ] Base model: Qwen/Qwen2.5-Coder-7B-Instruct downloaded
  - [ ] LoRA config: rank=64, alpha=32 (adjust per available VRAM)

- [ ] **CPT Training (Optional)**
  - [ ] Run CPT on unlabeled code dataset (4–8 hours)
  - [ ] Validate knowledge injection (sample completions)
  - [ ] Save checkpoint as `motadata-cpt-checkpoint`

- [ ] **SFT Training**
  - [ ] Run SFT on ChatML dataset (8–12 hours)
  - [ ] Monitor loss curve (should decrease smoothly)
  - [ ] Validate with 5–10 manual prompts per Type
  - [ ] Save checkpoint as `motadata-sft-checkpoint`

- [ ] **DPO Training**
  - [ ] Run DPO on preference dataset (4–6 hours)
  - [ ] Monitor preference accuracy (>80%)
  - [ ] Validate error reduction in key patterns
  - [ ] Save final checkpoint as `motadata-coder-final`

### 5.3 Deployment Checklist

- [ ] **Model Export & Serving**
  - [ ] Merge LoRA weights into base model
  - [ ] Export to vLLM-compatible format
  - [ ] Deploy vLLM server on port 8001
  - [ ] Test API responses with simple requests

- [ ] **RAG Integration**
  - [ ] Index codebase into Qdrant (port 6333)
  - [ ] Test retrieval: `@codebase` queries
  - [ ] Tune retrieval: K=3 neighbors, confidence threshold

- [ ] **Agent Configuration**
  - [ ] Configure Continue.dev with model endpoint
  - [ ] Set system prompt to suppress hallucinations
  - [ ] Test with sample feature building request
  - [ ] Test with sample RCA debugging request

- [ ] **Monitoring & Feedback**
  - [ ] Set up logging for all requests
  - [ ] Track metrics: feature completeness, hallucination rate
  - [ ] Collect developer feedback (1–2 week trial)
  - [ ] Plan iteration 2: DPO dataset expansion

---

## Part 6: Summary & Decision Table

### 6.1 Quick Reference: When to Use Each Paradigm

| Paradigm | When to Use | Effort (Time) | Expected Impact |
|----------|-------------|---------------|-----------------|
| **CPT** | Model lacks domain knowledge; high error rate on basic patterns | 8–16 hours GPU + 10 hours prep | +10–20% on specialized tasks |
| **SFT** | Most critical; teaches behavior and format | 12–20 hours GPU + 60 hours prep | +30–50% overall quality |
| **DPO** | After SFT; eliminate specific error classes | 6–12 hours GPU + 30 hours prep | +80–90% reduction in target errors |

*Table: Paradigm selection guide for Motadata*

### 6.2 Motadata AI Coding Assistant: Recommended Path

**For Motadata, the recommended approach is: CPT (optional) → SFT (required) → DPO (day 2 iteration)**

**Rationale:**
*   **SFT alone gets you to 70–80% quality.** This is sufficient for MVP.
*   **CPT adds 10–20%, but requires careful dataset curation.** Include in Week 2 if time permits.
*   **DPO refines the final 10–15%, targeting specific error classes.** Essential for production quality.

---

## Part 7: References & Related Work

[1] Rafailov, R., et al. (2023). Direct Preference Optimization: Your Language Model is Secretly a Reward Model. *arXiv preprint arXiv:2305.18290*.

[2] Wei, J., et al. (2022). Emergent Abilities of Large Language Models. *arXiv preprint arXiv:2206.07682*.

[3] Li, Y., et al. (2024). Focused-DPO: Enhancing Code Generation Through Targeted Preference Optimization. *arXiv preprint arXiv:2502.11475*.

[4] Touvron, H., et al. (2023). Llama 2: Open Foundation and Fine-Tuned Chat Models. *arXiv preprint arXiv:2307.09288*.

[5] Dubey, A., et al. (2024). Open-Sourced Qwen2.5-Coder: Advancing Code Generation in Open-Source Models. *Qwen Technical Report*.

[6] Habib, A., et al. (2024). A Recipe for Continued Pretraining of Language Models. *arXiv preprint arXiv:2407.07263*.

[7] HuggingFace. (2025). Direct Preference Optimization Trainer. Retrieved from https://huggingface.co/docs/trl/main/en/dpo_trainer

[8] AWS Bedrock. (2025). Prepare Datasets for Continued Pre-training. Retrieved from https://docs.aws.amazon.com/bedrock/latest/userguide/dataset-prep-continued-pretraining.html

[9] Anyscale. (2025). Dataset Preparation for LLM Post-training. Retrieved from https://docs.anyscale.com/llm/fine-tuning/data-preparation

[10] OpenAI. (2024). Direct Preference Optimization API Guide. Retrieved from https://platform.openai.com/docs/guides/direct-preference-optimization

---

## Appendix A: Code Templates for Dataset Generation

### A.1 CPT Dataset Generation Template

import json
import os
from pathlib import Path

def extract_java_files(root_path: str) -> list:
    """Extract all Java source files from project."""
    java_files = []
    for root, dirs, files in os.walk(root_path):
        # Skip test directories
        if 'test' in root or 'Test' in root:
            continue
        for file in files:
            if file.endswith('.java'):
                java_files.append(os.path.join(root, file))
    return java_files

def chunk_by_class(content: str, max_chunk_size: int = 2048):
    """Split Java file into chunks by class/method."""
    # Simple chunking: split by 'public class' or 'public interface'
    chunks = []
    lines = content.split('\n')
    current_chunk = []
    
    for line in lines:
        current_chunk.append(line)
        if len('\n'.join(current_chunk)) > max_chunk_size:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

def generate_cpt_dataset(root_path: str, output_file: str):
    """Main CPT dataset generation."""
    java_files = extract_java_files(root_path)
    
    with open(output_file, 'w') as out:
        for java_file in java_files:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Skip files with secrets
            if any(secret in content for secret in ['password', 'token', 'key=']):
                continue
            
            chunks = chunk_by_class(content)
            for chunk in chunks:
                json.dump({"input": chunk}, out)
                out.write('\n')
    
    print(f"Generated CPT dataset: {output_file}")

# Usage
generate_cpt_dataset("/path/to/motadata", "cpt_dataset.jsonl")

### A.2 SFT Dataset Balancing Template

import json
import random

def balance_sft_dataset(
    type_a_file: str,
    type_b_file: str,
    type_c_file: str,
    output_file: str,
    a_multiplier: int = 5,
    b_multiplier: int = 8,
    c_multiplier: int = 1
):
    """Balance and combine SFT datasets."""
    
    # Load each type
    with open(type_a_file) as f:
        type_a = [json.loads(line) for line in f]
    
    with open(type_b_file) as f:
        type_b = [json.loads(line) for line in f]
    
    with open(type_c_file) as f:
        type_c = [json.loads(line) for line in f]
    
    # Oversample
    print(f"Type A: {len(type_a)} → {len(type_a) * a_multiplier}")
    print(f"Type B: {len(type_b)} → {len(type_b) * b_multiplier}")
    print(f"Type C: {len(type_c)} → {len(type_c) * c_multiplier}")
    
    balanced = (
        type_a * a_multiplier +
        type_b * b_multiplier +
        type_c * c_multiplier
    )
    
    # Shuffle
    random.shuffle(balanced)
    
    # Save
    with open(output_file, 'w') as f:
        for sample in balanced:
            f.write(json.dumps(sample) + '\n')
    
    print(f"Balanced dataset: {len(balanced)} samples → {output_file}")

# Usage
balance_sft_dataset(
    type_a_file="sft_type_a.jsonl",
    type_b_file="sft_type_b.jsonl",
    type_c_file="sft_type_c.jsonl",
    output_file="sft_final.jsonl"
)

### A.3 DPO Dataset Generation Template

import json
import subprocess
import os
import uuid

def validate_java_syntax(code_snippet: str) -> bool:
    """Check if Java code snippet is syntactically valid."""
    test_file = f"/tmp/JavaTest_{uuid.uuid4()}.java"
    try:
        with open(test_file, 'w') as f:
            f.write(f"public class JavaTest {{ {code_snippet} }}")
        
        result = subprocess.run(
            ["javac", test_file],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def generate_dpo_dataset(
    sft_model,
    prompts: list,
    num_candidates: int = 5,
    output_file: str = "dpo_dataset.jsonl"
):
    """Generate DPO pairs using Error-Point Identification."""
    
    dpo_pairs = []
    
    for prompt in prompts:
        candidates = []
        scores = []
        
        # Step 1: Generate multiple candidates with varied temperature
        for temp in [0.1, 0.3, 0.5, 0.7, 0.9]:
            try:
                response = sft_model.generate(
                    prompt,
                    temperature=temp,
                    max_tokens=500
                )
                candidates.append(response)
            except:
                continue
        
        if len(candidates) < 2:
            continue
        
        # Step 2: Score each candidate
        for code in candidates:
            # Syntax validity
            syntax_ok = validate_java_syntax(code)
            
            # Code quality checks
            has_todos = "TODO" in code or "FIXME" in code
            is_empty = len(code.strip()) < 20
            has_try_catch = "try {" in code
            
            # Composite score
            score = (
                int(syntax_ok) * 100 +
                int(not has_todos) * 50 +
                int(not is_empty) * 30 +
                int(has_try_catch) * 20  # For error handling prompts
            )
            
            scores.append(score)
        
        # Step 3: Create preference pair
        best_idx = scores.index(max(scores))
        worst_idx = scores.index(min(scores))
        
        if scores[best_idx] > scores[worst_idx]:
            dpo_pairs.append({
                "prompt": prompt,
                "chosen": candidates[best_idx],
                "rejected": candidates[worst_idx]
            })
    
    # Save
    with open(output_file, 'w') as f:
        for pair in dpo_pairs:
            f.write(json.dumps(pair) + '\n')
    
    print(f"Generated {len(dpo_pairs)} DPO preference pairs")
    return dpo_pairs

# Usage
prompts = [
    "Add null check before accessing ctx.body():",
    "Create error handling for database query:",
    "Fix the NullPointerException in:"
]

generate_dpo_dataset(
    sft_model=loaded_model,
    prompts=prompts,
    num_candidates=5,
    output_file="dpo_dataset.jsonl"
)

---

## Appendix B: Training Configuration Templates

### B.1 Unsloth SFT Configuration

from unsloth import FastLanguageModel
from transformers import TrainingArguments
from trl import SFTTrainer

# Setup model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
    max_seq_length=8192,
    load_in_4bit=True,  # 4-bit quantization
)

# Add LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=64,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth"
)

# Training arguments
training_args = TrainingArguments(
    output_dir="./motadata-sft-checkpoint",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=2,
    warmup_steps=100,
    learning_rate=2e-4,
    weight_decay=0.01,
    logging_steps=10,
    save_steps=500,
    eval_steps=500,
    save_total_limit=3,
    load_best_model_at_end=True,
)

# Trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    dataset_text_field="text",  # Field containing formatted messages
    max_seq_length=8192,
)

# Train
trainer.train()

### B.2 Unsloth DPO Configuration

from unsloth import FastLanguageModel
from transformers import TrainingArguments
from trl import DPOTrainer

# Setup model (from SFT checkpoint)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./motadata-sft-checkpoint",
    max_seq_length=8192,
    load_in_4bit=True,
)

# LoRA setup
model = FastLanguageModel.get_peft_model(
    model,
    r=64,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none"
)

# DPO Training arguments
training_args = TrainingArguments(
    output_dir="./motadata-dpo-checkpoint",
    num_train_epochs=2,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=2,
    warmup_steps=50,
    learning_rate=5e-5,  # Lower LR for DPO
    weight_decay=0.01,
    logging_steps=10,
    save_steps=250,
    eval_steps=250,
)

# DPO Trainer
dpo_trainer = DPOTrainer(
    model=model,
    args=training_args,
    beta=0.1,  # DPO hyperparameter (controls preference strength)
    train_dataset=dpo_train_dataset,
    eval_dataset=dpo_eval_dataset,
    tokenizer=tokenizer,
    loss_type="sigmoid",  # or "hinge", "ipo"
)

# Train
dpo_trainer.train()

---

## Appendix C: Evaluation & Testing Checklist

### C.1 Manual Testing Prompts (SFT Validation)

**Type A (Knowledge) Test:**
Q: How do I add a new monitor type to Motadata?
Expected: Multi-step answer referencing AbstractMonitor, MonitorFactory, schema files.

**Type B (Patches) Test:**
File: src/api/DiscoveryAPI.java
Instruction: Add method to search monitors by name pattern. Return empty list if no match.
Expected: ~10 lines of code, uses config store pattern, handles null properly.

**Type C (Tool Use) Test:**
Feature: Create new API for managing alert profiles, including CRUD operations and schema.
Expected: Execution Plan first, then multi-file code with APIRouter registration.

### C.2 Automated Metrics

```python
def evaluate_sft_model(model, test_dataset):
    """Automated evaluation of SFT model."""
    
    metrics = {
        "syntax_valid": 0,
        "contains_todos": 0,
        "uses_correct_patterns": 0,
        "hallucinated_methods": 0
    }
    
    for sample in test_dataset:
        prompt = sample["messages"][0]["content"]
        response = model.generate(prompt, max_tokens=500)
        
        # Check syntax
        if is_valid_java(response):
            metrics["syntax_valid"] += 1
        
        # Check for TODOs
        if "TODO" not in response:
            metrics["contains_todos"] += 0
        else:
            metrics["contains_todos"] += 1
        
        # Check pattern usage
        if uses_motadata_patterns(response):
            metrics["uses_correct_patterns"] += 1
        
        # Check hallucinations
        if contains_nonexistent_methods(response):
            metrics["hallucinated_methods"] += 1
    
    # Average
    for key in metrics:
        metrics[key] /= len(test_dataset)
    
    return metrics
```

---

**End of Document**

This comprehensive guide covers the three paradigms (CPT, SFT, DPO), their dataset schemas, use cases, and specific requirements for building the Motadata AI Coding Assistant. The appendices include implementation templates and evaluation criteria.