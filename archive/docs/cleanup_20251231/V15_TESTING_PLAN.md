# V15 Testing & Benchmarking Plan

**Current Date**: December 31, 2025

## Phase Overview

After successful training and adapter merging, the V15 model is ready for comprehensive testing and benchmarking.

---

## Phase 1: Inference Testing ⏳ IN PROGRESS

### 1.1 Load Model
**Goal**: Verify merged model can be loaded and used for inference

**Steps**:
1. Load tokenizer from merged model
2. Load model weights
3. Test basic inference
4. Verify output format

**Expected Output**: Model loads successfully, generates valid text

### 1.2 Test Each Capability
**Goal**: Verify all 7 capabilities work correctly

**Capabilities to Test**:
1. **Tool Use** (15.4%)
   - Test: Can model call tools correctly?
   - Sample: "Use the search tool to find..."

2. **Direct Generation** (30.8%)
   - Test: Can model generate code directly?
   - Sample: "Write a function that..."

3. **Single-File Edits** (23.1%)
   - Test: Can model edit single files?
   - Sample: "Edit the function to..."

4. **Multi-File Edits** (11.5%)
   - Test: Can model handle multiple files?
   - Sample: "Update both files to..."

5. **Code Review** (11.5%)
   - Test: Can model review code?
   - Sample: "Review this code for..."

6. **File Creation** (5.8%)
   - Test: Can model create new files?
   - Sample: "Create a new file with..."

7. **Refactoring** (1.9%)
   - Test: Can model refactor code?
   - Sample: "Refactor this code to..."

---

## Phase 2: Benchmark Testing ⏳ NEXT

### 2.1 Reasoning Tasks
**Goal**: Measure model's reasoning capability

**Metrics**:
- Pass rate on reasoning tasks
- Quality of explanations
- Correctness of logic

**Test Set**: Use evaluation/results/ test sets

### 2.2 Coding Tasks
**Goal**: Measure model's coding capability

**Metrics**:
- Pass rate on coding tasks
- Code correctness
- Code quality

**Test Set**: Use evaluation/results/ test sets

### 2.3 Multi-File Tasks
**Goal**: Measure model's multi-file handling

**Metrics**:
- Pass rate on multi-file tasks
- Consistency across files
- Dependency handling

**Test Set**: Use evaluation/results/ test sets

### 2.4 Comparison Against Baseline
**Goal**: Compare v15 against previous versions

**Metrics**:
- v15 vs v14 improvement
- v15 vs v13 improvement
- Regression detection

---

## Phase 3: Output Format Validation ⏳ NEXT

### 3.1 Search-Replace Format
**Goal**: Verify outputs match expected format

**Validation**:
- Check format correctness
- Verify file paths
- Validate code syntax

### 3.2 Diff Output
**Goal**: Verify diff format is correct

**Validation**:
- Check diff syntax
- Verify line numbers
- Validate changes

### 3.3 Tool Use
**Goal**: Verify tool calls are correct

**Validation**:
- Check tool names
- Verify parameters
- Validate tool responses

---

## Phase 4: Performance Analysis ⏳ NEXT

### 4.1 Inference Speed
**Goal**: Measure inference performance

**Metrics**:
- Tokens per second
- Latency (first token, full response)
- Throughput

### 4.2 Memory Usage
**Goal**: Measure memory requirements

**Metrics**:
- Peak memory usage
- Memory per request
- Memory efficiency

### 4.3 Bottleneck Analysis
**Goal**: Identify performance bottlenecks

**Analysis**:
- CPU vs GPU utilization
- Memory bandwidth
- I/O bottlenecks

---

## Phase 5: Deployment Preparation ⏳ NEXT

### 5.1 vLLM Deployment
**Goal**: Deploy model to vLLM

**Steps**:
1. Load model in vLLM
2. Configure vLLM settings
3. Test vLLM inference
4. Verify performance

### 5.2 vLLM Testing
**Goal**: Test model in vLLM environment

**Tests**:
- Basic inference
- Batch inference
- Concurrent requests
- Error handling

### 5.3 Documentation
**Goal**: Document deployment process

**Documentation**:
- Deployment steps
- Configuration guide
- Troubleshooting guide
- Performance tuning

---

## Testing Scripts Available

Located in `training/finetuning/`:
- `test_semantic_context_with_task.py` - Test with semantic context
- `test_semantic_rag_e2e.py` - End-to-end RAG testing
- `test_semantic_rag_integration.py` - RAG integration tests
- `benchmark_v14_full.py` - Benchmarking script (can adapt for v15)

---

## Expected Outcomes

### If v15 is Successful
- ✅ All 7 capabilities present and balanced
- ✅ No regression in any capability
- ✅ Improved reasoning capability
- ✅ Better multi-file handling
- ✅ Proper tool use (not obsessed)

### If Issues Found
- 🔧 Identify which capability has regression
- 🔧 Analyze training data for that capability
- 🔧 Consider retraining with adjusted weights
- 🔧 Create v16 with improvements

---

## Files & Locations

| Component | Location |
|-----------|----------|
| Merged Model | `models/v15/motadata-coder-v15-merged/` |
| Training Checkpoints | `training/checkpoints/v15/checkpoint-v15/` |
| Training Scripts | `training/finetuning/` |
| Training Data | `training/finetuning/v15_balanced.jsonl` |
| Training Log | `training/artifacts/training_v15_final.log` |
| Test Scripts | `training/finetuning/test_*.py` |
| Benchmark Scripts | `training/finetuning/benchmark_*.py` |

---

## Status: Ready to Begin Testing

✅ Model trained and merged
✅ All infrastructure in place
✅ Test scripts available
⏳ Ready to start Phase 1: Inference Testing
