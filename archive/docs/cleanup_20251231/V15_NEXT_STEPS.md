# V15 Model - Next Steps (December 31, 2025)

## Current Status

✅ **Training Completed** (Dec 31, 2025)
✅ **Model Merged** (Dec 30, 2025)
⏳ **Testing & Evaluation** - IN PROGRESS

---

## Phase 1: Adapter Merging ✅ COMPLETED

### What Was Done
- Merged LoRA adapters from checkpoint-1236 with base model
- Output: `models/v15/motadata-coder-v15-merged/`
- Merge script: `training/finetuning/merge_v15_model.py`

### Verification
```bash
ls -lah ~/Harshil-PoCs/models/v15/motadata-coder-v15-merged/
```

---

## Phase 2: Testing & Evaluation ⏳ NEXT

### 2.1 Inference Testing
**Goal**: Verify model can generate outputs correctly

**Steps**:
1. Load merged model from `models/v15/motadata-coder-v15-merged/`
2. Test on sample prompts from each capability:
   - Tool use
   - Direct generation
   - Single-file edits
   - Multi-file edits
   - Code review
   - File creation
   - Refactoring

**Expected Output**: Valid search-replace format or tool calls

### 2.2 Benchmark Testing
**Goal**: Compare v15 against v14 and v13

**Metrics to Track**:
- Pass rate on reasoning tasks
- Pass rate on coding tasks
- Pass rate on multi-file tasks
- Output format correctness
- Inference speed

**Test Dataset**: Use evaluation/results/ test sets

### 2.3 Diff Format Validation
**Goal**: Ensure outputs match expected diff format

**Validation**:
- Check search-replace format correctness
- Verify file paths are valid
- Validate code syntax
- Check for hallucinations

---

## Phase 3: Comparison & Analysis

### Compare Against v14
- v14 had regression in direct generation (30.8% → lower)
- v15 should restore this capability
- Check if tool use is balanced (not obsessed)

### Compare Against v13
- v13 was baseline
- v15 should improve on all metrics
- Check for any regressions

---

## Files Ready for Testing

| File | Purpose | Location |
|------|---------|----------|
| Merged Model | v15 model ready for inference | `models/v15/motadata-coder-v15-merged/` |
| Training Script | Reference for training config | `training/finetuning/train_v15_balanced.py` |
| Dataset | Training data used | `training/finetuning/v15_balanced.jsonl` |
| Merge Script | How model was merged | `training/finetuning/merge_v15_model.py` |

---

## Testing Scripts Available

Located in `training/finetuning/`:
- `test_semantic_context_with_task.py` - Test with semantic context
- `test_semantic_rag_e2e.py` - End-to-end RAG testing
- `test_semantic_rag_integration.py` - RAG integration tests
- `benchmark_v14_full.py` - Benchmarking script

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

## Timeline

- **Dec 31**: Training completed, model merged
- **Dec 31**: Begin testing & evaluation
- **Jan 1**: Complete benchmarking
- **Jan 2**: Analysis & decision on v15 quality

---

## Commands to Run

### 1. Verify Merged Model
```bash
ls -lah ~/Harshil-PoCs/models/v15/motadata-coder-v15-merged/
```

### 2. Test Inference
```bash
cd ~/Harshil-PoCs
python3 -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_path = 'models/v15/motadata-coder-v15-merged/'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, device_map='auto')
print('✅ Model loaded successfully')
"
```

### 3. Run Benchmarks
```bash
cd ~/Harshil-PoCs/training/finetuning
python3 benchmark_v14_full.py  # Adapt for v15
```

---

## Notes

- Model is ready for production testing
- All training artifacts preserved for reproducibility
- Database files (Qdrant, Neo4j) are in `rag-system/data/`
- Virtual environments available in `venv/`

---

## Status: Ready for Testing Phase

✅ Training complete
✅ Model merged
⏳ Awaiting evaluation
