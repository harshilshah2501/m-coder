# Cloud / Agent Task — Master Prompt
## Repo graph enrichment + query routing for Plan-Gate inputs
### Work branch: `feature/repo-graph-enrichment-v1`  
*(Rename allowed — but **one** branch for **all** work; never commit to `main` from the agent.)*

---

> **HOW TO USE**
> 1. Clone/checkout **m-coder** on the machine that will run the work (**WSL with local Motadata + Neo4j is recommended** — see §Mission). `cd` to repo root, e.g. `~/Harshil-PoCs/m-coder`.
> 2. Create/switch to the work branch: `git checkout -b feature/repo-graph-enrichment-v1` (or the name you chose).
> 3. Paste everything **below** `── PROMPT START ──` into the cloud agent (or local agent) as the **single** task prompt.
> 4. Ensure Neo4j is running on **the same host** as the indexer (typically `bolt://127.0.0.1:7687`) and `NEO4J_PASSWORD` is set.

---

## ── PROMPT START ──

## Mission (read first)

**Problem statement:** The stack is not “over-governed.” Governance (Plan-Gate, evidence quality, rewards) should stay **strict**. The gap is **under-using deterministic repository context**: without a structural view of the Java tree, lexical retrieval alone can look like “defensive” outcomes (weak evidence, generic hits) even when the repo contains a clear answer.

**What this task delivers:** **Enrichment upstream of Plan-Gate** — not a bypass:

| Layer | Role |
| ----- | ---- |
| **AST → Neo4j** | Read-only index of `*.java` (inheritance / packages) co-located with the developer’s Motadata checkout. |
| **Query intent router** | Classifies queries and either (a) supplies **structured factual answers** from the graph, (b) **decomposes** broad questions into better retrieval sub-queries, or (c) passes through to the **existing** semantic pipeline. |
| **Plan-Gate** | Remains the **orchestrator**: it still receives requests in the **same contracts** as today. This work improves **inputs** (evidence richness, routing metadata, decomposed queries) — it does **not** remove policies, lower bars, or skip scoring where the existing CLI already scores. |

**Explicit non-goals:**

- Do **not** weaken governance rules, evidence contracts, or ART-lite semantics.
- Do **not** replace Plan-Gate or Context Layer with ad-hoc answers except where the prompt explicitly allows short-circuit **CLI** paths (identity / structural) that still emit **schema-compatible** JSON.
- Do **not** require a **GPU-hosted** Motadata mirror for graph build; prefer **WSL (or Linux) next to `MOTADATA_REPO_ROOT`** so branch choice matches the developer.

---

## Placement: Plan-Gate is not “blind”

- **Today:** `motadata_query_cli.py` orchestrates export → Plan-Gate Ask → optional reward. Plan-Gate already applies posture and metadata.
- **After this task:** The **router + graph** are **input amplifiers** — they run **before** the unchanged retrieval/Plan-Gate path for SEMANTIC queries, or supply a **governed-shaped** response for IDENTITY/STRUCTURAL when the CLI short-circuits **as specified below**.
- Any new fields must be **additive**; existing JSON fields consumed by tooling must remain **backward compatible**.

---

## Environment & paths

Adjust only if your machine differs; keep **absolute** paths in commands.

```
M-CODER REPO:     ~/Harshil-PoCs/m-coder
MOTADATA REPO:    /home/harshil/Projects/Motadata
JAVA ROOT:        …/Motadata/motadata/src/main/java
JAVA FILE COUNT:  ~519 .java (re-count at runtime; do not hardcode in logic)
ROOT NAMESPACE:   com.mindarray
MAVEN MODULE:     …/Motadata/motadata/pom.xml
AUTHORITY YAML:   <m-coder>/runtime/layer5/authority/product_authority_registry.yaml
```

**Neo4j (indexer co-located with Motadata):**

- `NEO4J_URI` default `bolt://127.0.0.1:7687`
- `NEO4J_USER` default `neo4j`
- `NEO4J_PASSWORD` **required** in env (no default in code)

---

## Python execution contract (mandatory)

Every `python3` invocation from repo root **must** use:

```bash
cd ~/Harshil-PoCs/m-coder
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"
```

Without this, imports such as `runtime.*` and `tools.ast_indexer` **will fail**.

---

## CRITICAL BRANCH CONSTRAINT

**Before any edit:**

```bash
git -C ~/Harshil-PoCs/m-coder branch --show-current
```

**Expected:** `feature/repo-graph-enrichment-v1` (or the exact branch name your operator created for this task).

If the branch is `main` or anything unexpected → **STOP** and report: `Wrong branch: <name>. Halting.`

**Rules:**

- All commits on the work branch only.
- Do **not** `git checkout main`, `merge` to main, or `push` to main from the agent.
- Commit after each completed **Task** using the **exact** message given.
- No PR from the agent — human reviews and merges.

---

## Known package roles (`com.mindarray.*`)

Orientation only — **read real files** before assuming inheritance or names.

| Package | Role |
| --- | --- |
| `api` | REST API routers, `AbstractAPI`, domain verticles — **TEST 1 anchor** |
| `aiops` | AIOps correlation, dependency processing |
| `agent` | Agent runtime / metrics |
| `cache` | Caches |
| `compliance` | Compliance |
| `config` | Configuration — **TEST 2 support** |
| `datastore` | Datastore facades |
| `db` | DB services |
| `eventbus` | Event transport |
| `flow` | Flow / IP / geo |
| `ha` | HA |
| `integration` | Integrations |
| `job` | Jobs |
| `log` | Logging |
| `manager` | Bootstrap / lifecycle |
| `netroute` | Routing |
| `nms` | NMS |
| `notification` | Notifications — mail-related surfaces |
| `patch` | Patching |
| `plugin` | Plugins |
| `policy` | Policies |
| `report` | Reporting |
| `rum` | RUM |
| `runbook` | Runbooks |
| `slo` | SLO |
| `store` | Store |
| `streaming` | Streaming |
| `trace` | Trace |
| `util` | Utilities |
| `visualization` | Visualization |

**Exclude from indexing:** `**/target/**` (build output).

---

## Acceptance tests — definition of done

Run with `PYTHONPATH` set and services up (Context Layer, Plan-Gate, vLLM as required by your existing `motadata_query_cli.py`).

```bash
export PYTHONPATH="$(pwd)"
# TEST 1 — Structural / inheritance
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root /home/harshil/Projects/Motadata \
  --query "Which class is the base class for all APIs?" \
  --out /tmp/t1.json --with-reward --reward-out /tmp/t1.reward.json

# TEST 2 — Broad semantic (decomposed retrieval)
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root /home/harshil/Projects/Motadata \
  --query "How does mail server configuration work?" \
  --out /tmp/t2.json --with-reward --reward-out /tmp/t2.reward.json

# TEST 3 — Identity
python3 runtime/scripts/motadata_query_cli.py \
  --workspace-root /home/harshil/Projects/Motadata \
  --query "What model are you?" \
  --out /tmp/t3.json --with-reward --reward-out /tmp/t3.reward.json
```

**PASS criteria (unchanged intent):**

| Test | Criteria |
| --- | --- |
| **1** | quality ∉ {`WEAK`,`INSUFFICIENT`}; `NO_CORE_IN_TOP3` not in reasons; reward total > 0; eligibility ≠ `banned`; answer contains a **concrete** `com.mindarray.api` class name |
| **2** | `HIGH_DISTRACTOR_RATIO`, `NOISE_DOMINATED`, `QUERY_TOO_GENERIC` not in reasons; reward > 0; eligibility ≠ `banned` |
| **3** | reward > 0; eligibility ≠ `banned`; `hard_violations` empty/absent; identity-style answer without retrieval-error boilerplate |

**Reward policy for routed intents (CLI must implement consistently):**

- **IDENTITY:** Do not run full ART-lite if the prompt specifies a stub; write a **minimal valid** `--reward-out` JSON with `total > 0`, `eligibility` not `banned`, and document keys in `metadata`.
- **STRUCTURAL (graph hit):** Full scoring allowed if the response goes through Plan-Gate; if true short-circuit **without** Plan-Gate, use the same stub policy as IDENTITY **or** document in code comments why full scoring ran.
- **DECOMPOSE / SEMANTIC:** Normal scoring.

---

## TASK A — Java AST indexer → Neo4j
**Commit:** `feat(ast): Java AST Neo4j indexer and graph query module`

### A.0 Explore first

Run `find` on `api/`, `notification/`, `config/`; open candidate base classes; confirm `extends` / `implements` in source **before** coding heuristics.

### A.1 Ingestion script

**Path:** `tools/ast_indexer/ingest_java_graph.py`

- Parser: **`javalang`** (pure Python). Pin version in `tools/ast_indexer/requirements.txt` (create if missing).
- Walk all `*.java` under `<MOTADATA>/motadata/src/main/java`, exclude `target/`.
- Per file emit records with at least:
  ```text
  class_name, qualified_name, package, top_package (first segment under com.mindarray, e.g. "api"),
  extends (simple name or None), implements (list of simple names),
  is_abstract, is_interface, file_path (absolute)
  ```
- **Unresolved supers:** If the resolved parent FQN is not present in this workspace, **skip** the `EXTENDS`/`IMPLEMENTS` edge to avoid fake nodes; log once per missing parent. Document policy in module docstring.
- Parse errors: log path, continue; do not abort the batch.
- Progress: every 50 files.

**Neo4j graph model:**

```cypher
(:Class {
  name, qualifiedName, package, topPackage,
  isAbstract, isInterface, filePath
})
(:Package { name, topPackage })
(:Class)-[:EXTENDS { simple_name }]->(:Class)
(:Class)-[:IMPLEMENTS { simple_name }]->(:Class)
(:Class)-[:IN_PACKAGE]->(:Package)
```

**File:** `tools/ast_indexer/schema.cypher` — run once before bulk ingest:

```cypher
CREATE CONSTRAINT class_qualified_name IF NOT EXISTS
  FOR (c:Class) REQUIRE c.qualifiedName IS UNIQUE;
CREATE CONSTRAINT package_name IF NOT EXISTS
  FOR (p:Package) REQUIRE p.name IS UNIQUE;
CREATE INDEX class_name_idx IF NOT EXISTS FOR (c:Class) ON (c.name);
CREATE INDEX class_top_package_idx IF NOT EXISTS FOR (c:Class) ON (c.topPackage);
CREATE FULLTEXT INDEX class_fulltext IF NOT EXISTS
  FOR (c:Class) ON EACH [c.name, c.qualifiedName, c.package];
```

**Env:** `NEO4J_URI` (default `bolt://127.0.0.1:7687`), `NEO4J_USER` (default `neo4j`), `NEO4J_PASSWORD` (**required**).

### A.2 Query module

**Path:** `tools/ast_indexer/query_graph.py`

Implement: `find_base_class`, `find_implementors`, `find_classes_by_concept`, `get_class_detail` with behaviors described in the prior revision, **plus:**

- **`find_base_class`** must prefer **named** abstract roots when multiple candidates tie (e.g. type named `AbstractAPI` in package `com.mindarray.api` wins tie-break over raw in-degree).
- All functions return plain `dict`/`list` suitable for JSON logging in `RouterResult.metadata`.

### A.3 Validate Task A

```bash
cd ~/Harshil-PoCs/m-coder && export PYTHONPATH="$(pwd)"
python3 -c "
from tools.ast_indexer.query_graph import find_base_class
r = find_base_class('api')
assert r is not None and r.get('name'), 'TASK A FAIL'
print('TASK A VALIDATION: PASS', r)
"
```

---

## TASK B — Query intent router (enrichment, not policy bypass)
**Commit:** `feat(router): query intent classifier and routing layer`

### B.1 Module

**Path:** `runtime/core/query_router.py`

Skeleton (adapt names if needed; keep contracts):

```python
class QueryIntent(Enum):
    IDENTITY = "identity"
    STRUCTURAL = "structural"
    DECOMPOSE = "decompose"
    SEMANTIC = "semantic"

@dataclass
class RouterResult:
    intent: QueryIntent
    answer: str | None
    sub_queries: list[str] | None
    skip_rag: bool
    metadata: dict
```

- Expose `QueryRouter.classify(query: str) -> RouterResult`.
- **`metadata`** must always include: `intent`, `match_reason` (short string); for STRUCTURAL include `graph_query_ms` when Neo4j is called.

**Intent order — first match wins:**

1. **IDENTITY** — if any trigger matches (case-insensitive):

   - `what model are you`, `who are you`, `what are you`, `which model`
   - `are you gpt`, `are you claude`, `are you llm`
   - `tell me about yourself`, `what is motadata coder`, `introduce yourself`

   **Answer (exact string, no retrieval):**

   > I am Motadata Coder, an AI-powered coding assistant built for the Motadata product codebase. I am governed by a constitutional AI framework with Plan-Gate runtime enforcement. I help engineers understand, navigate, and reason about the com.mindarray.* codebase across the Motadata Java sources.

   (Adjust the word “519” only if you replace it with a **runtime** file count from ingestion.)

2. **STRUCTURAL** — **narrowed triggers** (reduce false positives):
   - Require **at least one** of:
     - `base class`, `parent class`, `abstract class`, `extends`, `implements`, `inheritance`, `subclass`, `class hierarchy`, `interface for`
   - **And** at least one of:
     - a known `top_package` token present in the query (from the table above), **or**
     - phrase `all APIs` / `all api` / package name + `API`
   - Do **not** classify as STRUCTURAL on generic `which class` / `what class` **alone** (those often go to SEMANTIC).

   If STRUCTURAL fires but the graph returns **None**, **fall through to SEMANTIC** (no empty answer).

3. **DECOMPOSE** — broad questions that need better retrieval focus:

   - Starts with: `how does`, `how do`, `how is`, `how are`, `explain`, `describe`, `walk me through`
   - **Or** contains `configuration`, `workflow`, `mechanism`, `architecture` **and** query is longer than **5** words (split on whitespace).

   **Action:** Produce **three** sub-queries for lexical retrieval (via existing LLM path used by the CLI, **or** deterministic fallback below). `skip_rag=False`, `sub_queries` length 3.

   - **LLM failure fallback:** If sub-query LLM call fails or returns invalid JSON, fall back to **three deterministic** sub-queries: original query; `original + " com.mindarray"`; `original + " class method"` (trim length & tokenize sensibly). Log `metadata.fallback="deterministic_subqueries"`.

4. **SEMANTIC** — default.

### B.2 Integrate into `runtime/scripts/motadata_query_cli.py`

- Import `QueryRouter`, `QueryIntent` from `runtime.core.query_router`.
- **Immediately after** the user query string is known, call `classify(query)` inside **try/except**; on failure, log and continue with **SEMANTIC** behavior.
- **IDENTITY:** Build the same JSON shape the CLI normally writes to `--out`; set `ask_path` / metadata to indicate `identity_router`; write stub `--reward-out` per §Acceptance (reward policy).
- **STRUCTURAL:** If graph returns data, fill answer fields; else fall through to full pipeline.
- **DECOMPOSE:** Run retrieval **per** sub-query, merge/dedupe evidence, then **one** Plan-Gate call with merged context (or three calls if existing code only accepts one query — prefer **one** merged call to avoid triple cost; document choice).
- **SEMANTIC:** No change.
- Do **not** modify Plan-Gate **service** code in this task unless unavoidable.

### B.3 Router unit smoke (no network)

```bash
cd ~/Harshil-PoCs/m-coder && export PYTHONPATH="$(pwd)"
python3 -c "
from runtime.core.query_router import QueryRouter, QueryIntent
r = QueryRouter()
assert r.classify('What model are you?').intent == QueryIntent.IDENTITY
assert r.classify('Which class is the base class for all APIs?').intent == QueryIntent.STRUCTURAL
assert r.classify('How does mail server configuration work?').intent == QueryIntent.DECOMPOSE
assert r.classify('Show me the AlertManager class').intent == QueryIntent.SEMANTIC
print('ROUTER SMOKE: PASS')
"
```

---

## TASK C — Acceptance harness
**Commit:** `test: acceptance tests for query routing — all 3 pass`

**Path:** `tests/test_query_routing.py` (or `runtime/tests/test_query_routing.py` — **pick one** and add a one-line note in `tests/README` or repo README if created).

- Subprocess the three CLI commands; assert PASS table; exit `0` / `1`.

---

## Final report (print before last commit)

```
╔══════════════════════════════════════════════════════════╗
║   MOTADATA CODER — REPO GRAPH ENRICHMENT ACCEPTANCE      ║
╠══════════════════════════════════════════════════════════╣
║ Branch:  <work branch>                                   ║
║ Commits: (git log --oneline -3)                         ║
╠══════════════════════════════════════════════════════════╣
║ TEST 1 (structural):     PASS/FAIL   reward=…            ║
║ TEST 2 (decompose):      PASS/FAIL   reward=…            ║
║ TEST 3 (identity):      PASS/FAIL   reward=…            ║
╠══════════════════════════════════════════════════════════╣
║ javalang version: …                                      ║
║ Neo4j Class nodes: …    relationships: …                 ║
║ Parse errors: X / Y Java files                           ║
╠══════════════════════════════════════════════════════════╣
║ Created:  tools/ast_indexer/*, runtime/core/query_router ║
║ Modified: runtime/scripts/motadata_query_cli.py          ║
║ Tests:    tests/test_query_routing.py (or path chosen)   ║
╠══════════════════════════════════════════════════════════╣
║ Ready for human review: YES / NO                         ║
╚══════════════════════════════════════════════════════════╝
```

---

## Hard stops — do not silently workaround

1. Wrong git branch (see above).
2. `javalang` parse failures **> 10%** of files — stop and report file list sample.
3. Neo4j unreachable and `NEO4J_PASSWORD` unset when running ingestion.
4. CLI **crash** (exception) on SEMANTIC path after integration.
5. **Regression:** a fixed “golden” SEMANTIC query chosen by the operator scores strictly worse on reward total than **before** the change (operator must supply the query once in Task C if needed).

Report: condition, logs, attempts, what you need from the human.

---

## ── PROMPT END ──
