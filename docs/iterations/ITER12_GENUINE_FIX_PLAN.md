# Iter12: Genuine Fix for Training-Evaluation Mismatch

## Root Cause Analysis (Complete Picture)

### Current Evaluation Flow
1. **Task YAML** contains:
   - Task description + requirements (~500 chars)
   - Format instructions (~2,000 chars)
   - 10 production diff examples (~35,000 chars)
   - **NO baseline file content**

2. **Setup script** creates minimal stub files:
   ```java
   public class DependencyQueryProcessor {
     public void query() {}
   }
   ```

3. **RAG Client** (`evaluation/rag_client.py`):
   - Calls `/v1/chat/completions` (vLLM endpoint)
   - **Does NOT retrieve any context**
   - Just forwards prompt to model
   - **This is the broken part!**

4. **Model receives**:
   - Task description
   - Format instructions
   - Example diffs
   - **NO baseline code to modify**

5. **Model generates**:
   - Placeholder diffs with fake code
   - `index 1234567..abcdefg` (fake hashes)
   - `// Implementation for...` (placeholder comments)

### Current Training Data (Iter10/Iter11)
- **Format**: `File: X\nContent: <full file>\nTask: Y\nGenerate diff`
- **File content**: Embedded directly in prompt (500-5000 lines)
- **Model learns**: Generate diffs from file content

### The Mismatch
| Aspect | Training | Evaluation |
|--------|----------|------------|
| File content | Embedded in prompt | **NOT provided** |
| Prompt size | 2K-10K chars | 38K chars |
| Context source | Direct | **Should be RAG** |
| Task format | Simple | Complex with examples |

## The Genuine Fix (3-Part Solution)

### Part 1: Fix RAG Integration
**Goal**: Make RAG actually retrieve and inject baseline file content

**Implementation**:
1. Create proper RAG endpoint at `/v1/rag/completions`
2. RAG flow:
   ```
   User prompt → Extract file paths → Retrieve from codebase → Inject content → LLM
   ```
3. Update `evaluation/rag_client.py` to use RAG endpoint
4. RAG should retrieve:
   - Baseline files mentioned in `expected_files`
   - Related files from codebase (dependencies, imports)
   - Relevant code context (classes, methods)

**Files to modify**:
- `rag-system/rag_api.py` - Add `/v1/rag/completions` endpoint
- `evaluation/rag_client.py` - Use RAG endpoint instead of vLLM direct

### Part 2: Create RAG-Augmented Training Data
**Goal**: Training data matches evaluation format

**Dataset composition**:
1. **Extract baseline files** from git commits (before state)
2. **Create RAG-style prompts**:
   ```
   Task: <description>
   Requirements: <list>
   
   Baseline Files:
   File: src/main/java/Example.java
   ```java
   <full baseline content>
   ```
   
   Generate unified diff to implement the changes.
   ```
3. **Target output**: Unified diff (same as current)

**Data sources**:
- 1,148 existing production commits
- Extract "before" state from git
- Create RAG-augmented prompts
- Keep same diff outputs

### Part 3: Train Iter12 Model
**Goal**: Model learns to work with RAG-retrieved context

**Training configuration**:
- Base model: `motadata-coder-iter6` (proven baseline)
- Training examples: ~1,148 (RAG-augmented format)
- Learning rate: 1e-4
- Epochs: 2
- Format: RAG-style prompts with baseline content

**Expected improvement**:
- Model sees baseline code (like evaluation)
- Generates real diffs (not placeholders)
- Pass rate: 20% → 40-60%

## Implementation Steps

### Step 1: Implement RAG Endpoint (2-3 hours)
```python
# rag-system/rag_api.py
@app.post("/v1/rag/completions")
async def rag_completions(request: RAGRequest):
    # 1. Extract file paths from prompt
    # 2. Retrieve baseline files from workspace/git
    # 3. Inject into prompt
    # 4. Call vLLM
    # 5. Return response
```

### Step 2: Create RAG Training Data (1-2 hours)
```python
# Iter12-Training/create_rag_dataset.py
for commit in commits:
    # 1. Get baseline files (git show commit~1:path)
    # 2. Create RAG-style prompt
    # 3. Keep same diff output
    # 4. Save to train.jsonl
```

### Step 3: Train Iter12 (15 minutes)
```bash
cd Iter12-Training
python3 train_iter12.py
python3 merge_iter12.py
```

### Step 4: Deploy and Evaluate (5 minutes)
```bash
sudo systemctl restart motadata-coder
cd RAG-Datastore
python3 evaluation/run_motadata_bench.py --all
```

## Success Criteria

### Minimum Viable (40% pass rate)
- ✅ RAG retrieves baseline files
- ✅ Model generates real diffs (not placeholders)
- ✅ 4/10 tasks pass
- ✅ 10/10 tasks generate valid diff format

### Target (60% pass rate)
- ✅ RAG retrieves relevant context
- ✅ Model generates accurate diffs
- ✅ 6/10 tasks pass
- ✅ 9+/10 tasks compile successfully

## Timeline
- **Part 1 (RAG)**: 2-3 hours
- **Part 2 (Data)**: 1-2 hours  
- **Part 3 (Training)**: 15 minutes
- **Part 4 (Eval)**: 5 minutes
- **Total**: 4-6 hours

## Risk Mitigation
- Keep Iter11 as backup
- Test RAG endpoint before training
- Validate training data format
- Monitor training loss

