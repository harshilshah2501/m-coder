# RAG System Debugging Guide

When your Fine-Tuned Model + RAG system fails (hallucinates, wrong answer, no answer, truncated), use this guide to identify where the failure occurred and how to fix it.

---

## 🔍 System Architecture & Failure Points

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: RAG RETRIEVAL (Qdrant/Neo4j)                                      │
│  ─────────────────────────────────────                                      │
│  Log File: logs/layer1_retrieval.log                                        │
│                                                                             │
│  Failure Modes:                                                             │
│    • No documents retrieved (empty context)                                 │
│    • Wrong documents retrieved (irrelevant context)                         │
│    • Low confidence scores (<0.3)                                           │
│    • Code not indexed                                                       │
│                                                                             │
│  Fix Location: project_indexer.py, rag_api.py (search methods)              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: CONTEXT INJECTION                                                 │
│  ─────────────────────────────────                                          │
│  Log File: logs/layer2_context.log                                          │
│                                                                             │
│  Failure Modes:                                                             │
│    • Context too long → truncated                                           │
│    • Context poorly formatted                                               │
│    • Relevant info buried in noise                                          │
│                                                                             │
│  Fix Location: rag_api.py (context building in chat_completions)            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: SYSTEM PROMPT                                                     │
│  ─────────────────────────────────                                          │
│  Log File: logs/layer3_prompt.log                                           │
│                                                                             │
│  Failure Modes:                                                             │
│    • Model ignores RAG context                                              │
│    • Model doesn't know to say "I don't know"                               │
│    • No grounding instructions                                              │
│                                                                             │
│  Fix Location: rag_api.py (system_prompt variable)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: LLM GENERATION (vLLM)                                             │
│  ─────────────────────────────────                                          │
│  Log File: logs/layer4_llm.log                                              │
│                                                                             │
│  Failure Modes:                                                             │
│    • Hallucination despite good context                                     │
│    • Truncated output (max_tokens too low)                                  │
│    • Empty response                                                         │
│    • Repetition loops                                                       │
│                                                                             │
│  Fix Location: vLLM config, generation parameters, fine-tuning data         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Log Files Reference

| Log File | Layer | What It Tracks |
|----------|-------|----------------|
| `logs/layer1_retrieval.log` | Layer 1 | Qdrant/Neo4j queries, results count, confidence scores |
| `logs/layer2_context.log` | Layer 2 | Context size, truncation warnings, injected files |
| `logs/layer3_prompt.log` | Layer 3 | System prompt construction, message counts |
| `logs/layer4_llm.log` | Layer 4 | LLM requests, response times, finish reasons |
| `logs/diagnostics.log` | All | Combined failure summaries with suggested fixes |

### Quick Log Commands

```bash
# View recent failures (combined)
tail -50 rag-system/logs/diagnostics.log

# Check Layer 1 retrieval issues
grep -E "ERROR|NO RESULTS|WARNING" rag-system/logs/layer1_retrieval.log | tail -20

# Check Layer 2 context issues  
grep "TRUNCATED" rag-system/logs/layer2_context.log | tail -10

# Check Layer 4 LLM issues
grep -E "MINIMAL_RESPONSE|ERROR|TRUNCATED" rag-system/logs/layer4_llm.log | tail -20

# Get failure stats via API
curl -s http://localhost:8081/v1/diagnostics/failures | python3 -m json.tool
```

---

## 🚨 Failure Types & Fixes

### 1. HALLUCINATION
**Symptoms:**
- Model invents class/method names not in codebase
- Incorrect API signatures or method parameters
- References files that don't exist

**Likely Layer:** LAYER 1 (Retrieval) or LAYER 4 (LLM)

**Check:**
```bash
# Check what was retrieved
grep "Results:" rag-system/logs/layer1_retrieval.log | tail -5

# Check retrieval scores (low scores = irrelevant results)
grep "Scores:" rag-system/logs/layer1_retrieval.log | tail -5
```

**Fixes:**
| Fix | Location | How |
|-----|----------|-----|
| Check if project is indexed | API | `curl http://localhost:8081/v1/index/list` |
| Re-index project | API | `curl -X POST http://localhost:8081/v1/index/create -d '{"workspace_root": "/path"}'` |
| Lower confidence threshold | `rag_api.py` | Change `MIN_CONFIDENCE_THRESHOLD` in Config class |
| Add fine-tuning data | Training | Add examples that teach model to say "I don't know" |

---

### 2. WRONG ANSWER
**Symptoms:**
- Answer is factually incorrect about the code
- Wrong file paths returned
- Correct class name but wrong description

**Likely Layer:** LAYER 1 (Retrieval) or LAYER 2 (Context)

**Check:**
```bash
# Check what documents were retrieved
grep "Top:" rag-system/logs/layer1_retrieval.log | tail -5

# Check WORKSPACE_ROOT setting
grep "WORKSPACE_ROOT" rag-system/rag_api.py
```

**Fixes:**
| Fix | Location | How |
|-----|----------|-----|
| Improve query keywords | User | Rephrase the question with more specific terms |
| Check WORKSPACE_ROOT | `rag_api.py` or systemd service | Ensure path is correct |
| Re-index with better parsing | `project_indexer.py` | Improve Java parsing regex |

---

### 3. NO ANSWER / EMPTY RESPONSE
**Symptoms:**
- Empty response ("")
- Response < 50 characters
- "I don't have enough context"

**Likely Layer:** LAYER 1 (Retrieval) or LAYER 4 (LLM)

**Check:**
```bash
# Check if anything was retrieved
grep "NO RESULTS" rag-system/logs/layer1_retrieval.log | tail -5

# Check LLM response issues
grep "MINIMAL_RESPONSE\|EMPTY" rag-system/logs/layer4_llm.log | tail -5

# Check vLLM health
curl http://localhost:8080/health
```

**Fixes:**
| Fix | Location | How |
|-----|----------|-----|
| Index/re-index project | API | `curl -X POST http://localhost:8081/v1/index/create ...` |
| Check Qdrant health | Terminal | `curl http://localhost:6333/health` |
| Check vLLM health | Terminal | `curl http://localhost:8080/health` |
| Increase max_tokens | Request | Add `"max_tokens": 2048` to request |
| Restart services | Terminal | `sudo systemctl restart motadata-orchestrator` |

---

### 4. TRUNCATED RESPONSE
**Symptoms:**
- Response cuts off mid-sentence
- `finish_reason: "length"` in response
- Incomplete code blocks

**Likely Layer:** LAYER 4 (LLM)

**Check:**
```bash
# Check finish reasons
grep "finish:" rag-system/logs/layer4_llm.log | tail -10
```

**Fixes:**
| Fix | Location | How |
|-----|----------|-----|
| Increase max_tokens | Request payload | `"max_tokens": 4096` |
| Ask for concise response | Prompt | Add "Be concise" to query |
| Reduce context size | Request payload | `"rag_top_k": 3` instead of 5 |

---

## 🔧 Quick Health Checks

Run these commands to quickly diagnose system health:

```bash
# 1. Check all services are running
sudo systemctl status motadata-orchestrator motadata-rag

# 2. Check RAG API health
curl -s http://localhost:8081/health | python3 -m json.tool

# 3. Check Qdrant health  
curl -s http://localhost:6333/health

# 4. Check vLLM health
curl -s http://localhost:8080/health

# 5. List indexed projects
curl -s http://localhost:8081/v1/index/list | python3 -m json.tool

# 6. Get recent failures
curl -s http://localhost:8081/v1/diagnostics/failures | python3 -m json.tool

# 7. Test a simple query
curl -s -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "motadata-coder", "messages": [{"role": "user", "content": "What is AbstractConfigStore?"}]}' \
  | python3 -m json.tool
```

---

## 🔄 Debugging Workflow

```
1. Identify Failure Type
   ↓
2. Check relevant log file (see table above)
   ↓
3. Look for session_id in logs to trace request
   ↓
4. Identify which layer failed
   ↓
5. Apply fix from table above
   ↓
6. Restart service if needed: sudo systemctl restart motadata-rag
   ↓
7. Test again
```

### Example Debug Session

```bash
# 1. User reports: "Model said AbstractConfigStore doesn't exist"
# This is likely HALLUCINATION or NO_ANSWER

# 2. Check diagnostics log
tail -20 rag-system/logs/diagnostics.log
# Output: [20241212_153045_abc123] FAILURE DETECTED: NO_CONTEXT at LAYER1_RETRIEVAL

# 3. Check retrieval log for that session
grep "abc123" rag-system/logs/layer1_retrieval.log
# Output: [abc123] NO RESULTS RETRIEVED

# 4. Diagnosis: Project not indexed or wrong workspace

# 5. Check indexed projects
curl http://localhost:8081/v1/index/list
# Output: [] (empty - no projects indexed!)

# 6. Fix: Index the project
curl -X POST http://localhost:8081/v1/index/create \
  -H "Content-Type: application/json" \
  -d '{"workspace_root": "/home/user/project", "async_mode": true}'

# 7. Wait for indexing, then test again
```

---

## 📊 Component Responsibilities

| Component | Port | Responsibility | Failure Impact |
|-----------|------|----------------|----------------|
| **RAG API** | 8081 | Context retrieval, chat endpoint | No context injection |
| **Qdrant** | 6333 | Vector storage & search | No semantic search |
| **Neo4j** | 7687 | Graph relationships | No caller/callee info |
| **vLLM** | 8080 | LLM inference | No response generation |

---

## 🛠️ Common Fix Commands

```bash
# Restart all services
sudo systemctl restart motadata-orchestrator

# Restart just RAG API
sudo systemctl restart motadata-rag

# Re-index a project
curl -X DELETE "http://localhost:8081/v1/index/project_name"
curl -X POST http://localhost:8081/v1/index/create \
  -d '{"workspace_root": "/path/to/project"}'

# Clear logs (if too large)
> rag-system/logs/diagnostics.log
> rag-system/logs/layer1_retrieval.log

# Check systemd logs
sudo journalctl -u motadata-rag --no-pager -n 50
```

