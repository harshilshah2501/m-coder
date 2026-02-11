# Iteration 8: Addressing Tool Obsession & Inconsistency

**Date:** December 16, 2025  
**Goal:** Fix the "Tool Obsession" vs "Tool Refusal" inconsistency in Iter 7  
**Target Metrics:**
- Tool Obsession Rate: <10% (currently 40%)
- Agentic Pass Rate: >80% (currently 20%)
- Standard Evaluation: >70% (currently 50%)

---

## Problem Analysis

### Issue 1: Training Data Mismatch
**Root Cause:** Dataset C (11,485 examples) was sourced from older training sets that reference "ChromaDB" instead of "Qdrant". The model learned outdated tool names.

**Evidence:**
```json
{
  "function": {
    "name": "find_similar_methods",
    "description": "Find methods similar to a query using semantic search in ChromaDB"  // ❌ Wrong!
  }
}
```

**Impact:** The model uses `vector_search()` (a hallucinated alias) instead of the proper `find_similar_methods()`.

---

### Issue 2: No Mode Indicator
**Root Cause:** Training examples don't clearly signal when the model should use tools vs answer directly.

**Evidence:**
- Standard Eval Prompt: "Answer directly without tools" → Model ignores this (40% tool obsession).
- Agentic Eval Prompt: "Use tools to find..." → Model refuses ("I don't have enough context").

**Impact:** The model can't distinguish between "Chat Mode" (direct answer) and "Agent Mode" (tool use).

---

### Issue 3: Over-Memorization
**Root Cause:** The model memorized large portions of the Motadata codebase during training.

**Evidence:**
- Test AG5: Asked to retrieve `Discovery.java` → Model outputs the entire file from memory instead of calling `get_context_for_method()`.

**Impact:** The model skips retrieval tools because it "already knows" the answer, defeating the purpose of RAG.

---

## Solution: 3-Phase Approach

### Phase 1: Immediate Fix (No Retraining)
**Timeline:** 1-2 days  
**Objective:** Reduce tool obsession in production without waiting for Iter 8.

#### 1.1 System Prompt Templates
Update `rag_api.py` to use explicit mode-based prompts:

```python
SYSTEM_PROMPTS = {
    "chat": """You are Motadata Coder, a code assistant. Answer questions directly based on your training. 
    DO NOT use tools or output XML/JSON. Provide clear, concise answers.""",
    
    "agent": """You are Motadata Coder, an AI agent with access to the following tools:
    [... tool definitions ...]
    
    You MUST use these tools to retrieve information. Do NOT answer from memory.
    Output tool calls in JSON format: {"tool": "name", "args": {...}}"""
}
```

#### 1.2 Post-Processing Filter
Add a response cleaner to strip tool artifacts:

```python
def clean_response(response: str, mode: str) -> str:
    if mode == "chat":
        # Remove tool call patterns
        response = re.sub(r'<thought>.*?</thought>', '', response, flags=re.DOTALL)
        response = re.sub(r'vector_search\(.*?\)', '', response)
        response = re.sub(r'<tool_code>.*?</tool_code>', '', response, flags=re.DOTALL)
    return response.strip()
```

#### 1.3 API Mode Parameter
Add a `mode` field to `/v1/chat/completions`:

```json
{
  "model": "motadata-coder",
  "messages": [...],
  "mode": "chat"  // or "agent"
}
```

---

### Phase 2: Dataset Cleanup & Augmentation
**Timeline:** 3-5 days  
**Objective:** Prepare high-quality training data for Iter 8.

#### 2.1 Fix Dataset C (Reasoning)
1. **Find & Replace:**
   - `ChromaDB` → `Qdrant`
   - `vector_search` → Remove (let the model learn official tool names only)

2. **Add Mode Indicators:**
   ```json
   {
     "role": "system",
     "content": "You are an agent. Use tools to answer. ..."  // Explicit mode
   }
   ```

3. **Validation Script:**
   ```bash
   python3 validate_dataset_c.py
   # Checks:
   # - No ChromaDB references
   # - All tool calls use official names
   # - System prompts include mode keywords
   ```

#### 2.2 Create Dataset D (Balanced Direct Answers)
Generate ~5,000 examples where the model should answer WITHOUT tools:

**Example 1 (Knowledge):**
```json
{
  "messages": [
    {"role": "system", "content": "You are Motadata Coder. Answer directly. No tools."},
    {"role": "user", "content": "What is AbstractConfigStore?"},
    {"role": "assistant", "content": "AbstractConfigStore is a base class for configuration stores in Motadata..."}
  ]
}
```

**Example 2 (Code Review):**
```json
{
  "messages": [
    {"role": "system", "content": "You are a code reviewer. Analyze the code directly."},
    {"role": "user", "content": "Review this code: [code snippet]"},
    {"role": "assistant", "content": "Issues found: 1. Missing null check..."}
  ]
}
```

**Generation Strategy:**
- Use Iter 7 to self-generate examples (prompt it to answer without tools)
- Manually curate 500 "golden" examples
- Auto-generate 4,500 variations using templates

---

### Phase 3: Iteration 8 Training
**Timeline:** 2-3 days (training) + 1 day (evaluation)  
**Objective:** Retrain with balanced data.

#### 3.1 Dataset Composition
| Dataset | Size | Purpose | Mode |
|---------|------|---------|------|
| Dataset A (Jira) | 691 | Code Quality & Patterns | Mixed |
| Dataset B (Multi-file) | 210 | Feature Creation | Agent |
| Dataset C (Reasoning - Cleaned) | 11,485 | Graph Traversal & Logic | Agent |
| **Dataset D (Direct Answers)** | **5,000** | **Anti-Tool-Obsession** | **Chat** |
| **Total** | **17,386** | | |

#### 3.2 Training Config
```python
# Emphasize mode-switching capability
lora_config = LoraConfig(
    r=16,
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05
)

training_args = TrainingArguments(
    per_device_train_batch_size=4,
    num_train_epochs=2,
    learning_rate=2e-4,
    # Add mode-aware loss weighting if possible
)
```

#### 3.3 Evaluation Criteria
| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool Obsession Rate | <10% | `evaluate_finetuned_model.py` |
| Agentic Pass Rate | >80% | `evaluate_agentic.py` |
| Knowledge Retention | >90% | Type A tests |
| Multi-file Creation | >50% | Type B tests |

---

## Action Plan (Prioritized)

### Week 1: Immediate Mitigations
- [ ] **Day 1-2:** Implement system prompt templates in `rag_api.py` (Phase 1.1)
- [ ] **Day 2-3:** Add post-processing filter (Phase 1.2)
- [ ] **Day 3:** Deploy and test with existing Iter 7 model

### Week 2: Data Preparation
- [ ] **Day 4-5:** Clean Dataset C (Phase 2.1)
- [ ] **Day 6-8:** Generate Dataset D (Phase 2.2)
- [ ] **Day 8:** Validate all datasets

### Week 3: Training & Deployment
- [ ] **Day 9-11:** Train Iteration 8
- [ ] **Day 11:** Merge and deploy
- [ ] **Day 12:** Full evaluation suite

---

## Expected Outcomes

### Short-term (Phase 1 - No Retraining)
- **Tool Obsession:** 40% → ~25% (post-processing helps but doesn't fix root cause)
- **User Experience:** Cleaner responses in "chat" mode

### Long-term (Phase 3 - Iter 8)
- **Tool Obsession:** 40% → <10%
- **Agentic Capability:** 20% → >80%
- **Overall Quality:** Model becomes "mode-aware" and adapts behavior to context

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Dataset D generation produces low-quality examples | High | High | Manual curation of 10% (500 examples) |
| Iter 8 over-corrects and loses agentic capability | Medium | High | Keep Dataset C at 66% of total data |
| Tool names still inconsistent after cleanup | Low | Medium | Automated validation script |
| Training time exceeds GPU budget | Low | Medium | Use 4-bit quantization, gradient checkpointing |

---

## Success Metrics

**Definition of Success for Iteration 8:**
1. Standard Evaluation: **>70% pass rate** (vs 50% in Iter 7)
2. Agentic Evaluation: **>80% pass rate** (vs 20% in Iter 7)
3. Tool Obsession: **<10%** (vs 40% in Iter 7)
4. No regression in Knowledge/Reasoning categories (maintain 4.0+/5)

**Go/No-Go Decision:**
- If Week 1 mitigations reduce tool obsession to <25%, proceed with Iter 8.
- If not, investigate alternative approaches (e.g., DPO training, tool-conditional prompts).

---

**Prepared by:** GitHub Copilot  
**Reviewed by:** [Pending]  
**Approved for Execution:** [Pending]
