# Motadata Coder - Project Summary

**Last Updated:** December 16, 2025

## Current Status

### Production Deployment
- **Model:** motadata-coder-iter9 (Qwen2.5-Coder-7B-Instruct base)
- **Training:** Full precision bfloat16, NO quantization
- **Deployment:** vLLM on H100 PCIe 80GB
- **Endpoints:**
  - vLLM: `http://localhost:8000` (OpenAI-compatible API)
  - RAG API: `http://localhost:8081` (with Qdrant + Neo4j)
- **Performance:**
  - Standard: 6/10 pass (60%), 3.30/5 avg score
  - Agentic: 4/5 pass (80%), 4.40/5 avg score
  - Tool obsession: 0%
  - Repetition: 10%

### System Architecture
```
┌─────────────────┐
│  User Request   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  RAG API (port 8081)            │
│  - Query understanding          │
│  - Tool selection               │
│  - Context retrieval            │
└────────┬────────────────────────┘
         │
         ├─────► Qdrant (vector search)
         ├─────► Neo4j (graph queries)
         │
         ▼
┌─────────────────────────────────┐
│  vLLM (port 8000)               │
│  - motadata-coder-iter9         │
│  - Full precision bfloat16      │
│  - Context window: 32K tokens   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Final Response │
└─────────────────┘
```

## Training Evolution

### Dataset Composition History

| Iteration | Total | Agentic % | Direct % | Multi-file % | Code Review % | Graph % |
|-----------|-------|-----------|----------|--------------|---------------|---------|
| Iter6 | ~10k | Unknown | Unknown | Unknown | 0% | 0% |
| Iter7 | ~12k | **93%** | 7% | 4% | 0% | 0% |
| Iter8 | 15.6k | **79.5%** | 16% | 4.4% | 0% | 0% |
| Iter9 | 12.7k | **50.4%** | **38%** | 5.4% | **18.1%** | **6.3%** |

**Key Learning:** Dataset balance is critical. Over-representation of agentic examples (>70%) causes tool obsession.

### Performance Trajectory

| Iteration | Training Loss | Standard Pass | Agentic Pass | Tool Obsession | Status |
|-----------|---------------|---------------|--------------|----------------|--------|
| Iter6 | N/A | 60% (2.95/5) | N/A | 0% | ✅ Baseline |
| Iter7 | N/A | 50% (3.20/5) | 20% (1.80/5) | **40%** | ⚠️ Imbalanced |
| Iter8 | 0.4061 | 40% (2.40/5) | 60% (3.00/5) | **60%** | ⚠️ Still imbalanced |
| Iter9 (4-bit) | 0.2854 | **0% (1.00/5)** | N/A | 0% | ❌ **CORRUPTED** |
| Iter9 (Full) | 0.2847 | **60% (3.30/5)** | **80% (4.40/5)** | **0%** | ✅ **PRODUCTION** |

### Critical Discovery: 4-bit Corruption

**Timeline:**
1. **Training (4-bit):** Completed successfully, loss 0.2854
2. **Merge (4-bit→16-bit):** Warning about "different generations"
3. **Deployment:** Model loaded, no errors
4. **Testing:** 
   - Simple query: "What is 2+2?" 
   - Response: `{baselte` (gibberish)
   - Full evaluation: 0/10 pass, 80% repetition loops
5. **Analysis:** 4-bit→16-bit conversion corrupted weights
6. **Solution:** Retrain in full precision (bfloat16 throughout)
7. **Result:** 60% standard, 80% agentic, perfect coherence

**Root Cause:**
- 4-bit quantization maps weights to lookup tables
- LoRA training happens in quantized space
- Merge dequantizes back to 16-bit
- Numerical errors accumulate across 7B parameters × 28 layers
- Result: Catastrophic weight corruption

**Why We Used 4-bit:**
- Habit from GPU-constrained environments (16GB consumer GPUs)
- Didn't analyze H100's capacity (80GB available)
- Full precision only needs ~60GB (17GB observed)

**Lesson:** Match training precision to deployment precision. Never mix quantization levels.

## Technical Specifications

### Model Architecture
- **Base:** Qwen/Qwen2.5-Coder-7B-Instruct
- **Parameters:** 7.66B total, 40M trainable (LoRA)
- **LoRA Config:**
  - Rank (r): 16
  - Alpha: 16
  - Dropout: 0
  - Target modules: All attention + MLP layers
- **Precision:** bfloat16 (full precision, no quantization)
- **Context:** 8,192 tokens training, 32,768 tokens inference

### Training Configuration
```python
# Successful full precision config
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
    max_seq_length=8192,
    dtype=torch.bfloat16,
    load_in_4bit=False,  # ✅ Critical: Full precision
)

# Training args
TrainingArguments(
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,  # Effective batch: 8
    warmup_steps=10,
    num_train_epochs=2,
    learning_rate=2e-4,
    fp16=False,
    bf16=True,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
)
```

### Hardware Requirements
- **GPU:** H100 PCIe 80GB (or equivalent)
- **Training:**
  - Memory: 17GB GPU (21% utilization)
  - Time: 43 minutes for 2 epochs
  - Storage: 15GB (merged model)
- **Inference:**
  - Memory: 42GB GPU (52% utilization)
  - Speed: ~50 tokens/second
  - Concurrency: 4-8 requests (depends on prompt length)

## Evaluation Framework

### Standard Tests (10 total)
**Categories:**
- **TYPE_A_KNOWLEDGE (3):** Direct factual questions about codebase
  - Current: 100% pass, 4.33/5 avg
  - Example: "Explain EventBus architecture"
  
- **TYPE_B_MULTIFILE (2):** Multi-file implementation planning
  - Current: 0% pass, 1.50/5 avg ⚠️
  - Example: "Create full REST API feature"
  
- **RCA_DEBUGGING (2):** Root cause analysis from error logs
  - Current: 100% pass, 4.00/5 avg
  - Example: "Debug NullPointerException in Discovery"
  
- **CODE_REVIEW (2):** Code quality analysis
  - Current: 0% pass, 2.00/5 avg ⚠️
  - Example: "Review ConfigStore implementation"
  
- **DIRECT_REASONING (1):** General reasoning
  - Current: 100% pass, 5.00/5 avg
  - Example: "Analyze memory leak patterns"

### Agentic Tests (5 total)
**Tool-based Tasks:**
- Find specific methods in codebase (✅ 5/5)
- Find class definitions (✅ 5/5)
- Query callers via graph (✅ 5/5)
- Explore method dependencies (✅ 5/5)
- Get context for error analysis (❌ 2/5 - answers directly instead of using tools)

**Available Tools:**
1. `find_similar_methods()` - Semantic search in Qdrant
2. `get_class_info()` - Retrieve class definition
3. `query_callers()` - Neo4j graph query for callers
4. `query_callees()` - Neo4j graph query for callees
5. `get_context_for_method()` - Full method implementation

### Scoring System
- **5/5:** Perfect answer, comprehensive, accurate
- **4/5:** Good answer, minor omissions
- **3/5:** Acceptable, some inaccuracies or gaps
- **2/5:** Weak answer, major gaps or errors
- **1/5:** Failed, wrong approach or gibberish

**Pass threshold:** ≥3/5

**Failure modes:**
- `TOOL_OBSESSION`: Used tools when direct answer expected
- `REPETITION_LOOP`: Output contains repeated patterns
- `MINIMAL_RESPONSE`: Too short or empty
- `NO_TOOL_CALLS_OR_RAG`: Should use tools but didn't

## Known Issues & Future Work

### High Priority
1. **Multi-file Performance (0% → 50-70%)**
   - Current: Only 5.4% of dataset (691 examples)
   - Target: 15-20% of dataset (~2,000-3,000 examples)
   - Impact: Enable complex feature implementation

2. **Code Review Performance (0% → 60-80%)**
   - Current: 18.1% of dataset (new capability)
   - Target: 25-30% of dataset (~3,500-4,500 examples)
   - Impact: Production-grade code analysis

3. **AG5 Tool Use Fix (2/5 → 4-5/5)**
   - Current: Model answers directly when tools expected
   - Solution: Add examples requiring mandatory retrieval
   - Impact: More reliable RAG usage

### Medium Priority
1. **Repetition Penalty:** Add `repetition_penalty=1.2` to generation config
2. **Graph Query Expansion:** 6.3% → 10-15% of dataset
3. **Generation Tuning:** Experiment with temperature 0.05 vs 0.1

### Low Priority
1. Fine-tune other hyperparameters (top_p, max_tokens)
2. Explore larger base models (14B, 30B)
3. Implement DPO/RLHF for preference learning

## File Organization

### Key Documentation
- 📘 **[ITERATION_9_JOURNAL.md](docs/ITERATION_9_JOURNAL.md)** - Detailed 16-part chronicle of Iter9 (4-bit corruption discovery, analysis, resolution)
- 📊 **[ITER8_AND_ITER9_RESULTS.md](evaluation/ITER8_AND_ITER9_RESULTS.md)** - Comparative performance analysis across iterations
- 🏗️ **[ARCHITECTURE.md](rag-system/ARCHITECTURE.md)** - System design and component interactions
- 🚀 **[README.md](README.md)** - Quick start and overview

### Training Artifacts
```
Finetuning-Iter9/
├── datasets/
│   ├── iter9_train.jsonl (96MB, 12,056 examples)
│   └── iter9_test.jsonl (5MB, 635 examples)
├── outputs-iter9-fullprecision/
│   └── lora_model/ (170MB LoRA weights)
├── scripts/
│   └── merge_iter9_fullprecision.py
├── train_iter9_fullprecision.py (current)
├── train_iter9.py (original 4-bit, deprecated)
└── training_fullprecision.log (training metrics)
```

### Backups
```
model-backups/
├── README.md (backup documentation)
├── motadata-coder-iter6-backup/ (15GB baseline)
└── motadata-coder-iter9-backup/ (15GB current, to be created)
```

### Evaluation Results
```
evaluation/
├── evaluate_finetuned_model.py (standard test suite)
├── evaluate_agentic.py (tool use test suite)
├── iter9_fullprecision_standard.log (current results)
├── iter9_fullprecision_agentic.log (current results)
├── iter9_standard.log (CORRUPTED 4-bit results - 0% pass)
└── evaluation_report_*.json (historical results)
```

## Development Workflow

### Adding New Training Data
1. Create examples in JSONL format with chat templates
2. Balance categories (target: 50% agentic, 50% direct)
3. Validate format: `jq . < dataset.jsonl | head`
4. Check for duplicates: `sort dataset.jsonl | uniq -d`
5. Add to dataset composition tracking

### Training New Iteration
```bash
# 1. Prepare environment
cd /home/harshil/Harshil-PoCs/Finetuning-Iter10
source ../Finetuning/venv/bin/activate

# 2. Create training script (copy from Iter9 full precision)
cp ../Finetuning-Iter9/train_iter9_fullprecision.py train_iter10.py
# Edit: update dataset paths, output dir

# 3. Run training in screen
screen -dmS iter10 python train_iter10.py

# 4. Monitor progress
tail -f training.log

# 5. After completion, merge
python scripts/merge_iter10.py

# 6. Deploy to test
sudo systemctl stop motadata-coder
# Update service to point to new model
sudo systemctl start motadata-coder

# 7. Validate (CRITICAL - catch corruption early)
curl -X POST http://localhost:8000/v1/chat/completions \
  -d '{"model":"motadata-coder","messages":[{"role":"user","content":"What is 2+2?"}]}'
# MUST get coherent response, NOT gibberish

# 8. Run full evaluation
cd ../RAG-Datastore/evaluation
python3 evaluate_finetuned_model.py | tee iter10_standard.log
python3 evaluate_agentic.py | tee iter10_agentic.log

# 9. If successful, backup
rsync -av /home/harshil/Harshil-PoCs/motadata-coder-iter10/ \
          /home/harshil/Harshil-PoCs/model-backups/motadata-coder-iter10-backup/
```

### Deployment Checklist
- [ ] Backup current production model
- [ ] Train new iteration (full precision only)
- [ ] Merge without quantization conversion
- [ ] Run simple coherence test ("What is 2+2?")
- [ ] Run full evaluation suite (standard + agentic)
- [ ] Compare results with previous iteration
- [ ] Document findings in ITERATION_X_JOURNAL.md
- [ ] Update README.md and summary files
- [ ] Create backup of new model
- [ ] Deploy to production if improvements seen
- [ ] Monitor for 24 hours before removing old model

## Quick Reference Commands

### Health Checks
```bash
# Check all services
sudo systemctl status motadata-orchestrator

# Check individual services
curl http://localhost:8000/v1/models  # vLLM
curl http://localhost:8081/health     # RAG API
curl http://localhost:6333/health     # Qdrant
curl http://localhost:7474/           # Neo4j browser

# GPU usage
nvidia-smi

# Disk space
df -h /
```

### Testing Model
```bash
# Simple test (detect corruption)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "motadata-coder",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "max_tokens": 50
  }'

# Full evaluation
cd /home/harshil/Harshil-PoCs/RAG-Datastore/evaluation
python3 evaluate_finetuned_model.py
python3 evaluate_agentic.py
```

### Logs
```bash
# vLLM logs
sudo journalctl -u motadata-coder -f

# RAG API logs
sudo journalctl -u motadata-rag -f

# Training logs
tail -f /home/harshil/Harshil-PoCs/Finetuning-Iter9/training_fullprecision.log
```

## Success Metrics

### Current (Iter9 Full Precision)
- ✅ Standard: 60% pass, 3.30/5 avg
- ✅ Agentic: 80% pass, 4.40/5 avg
- ✅ Tool obsession: 0%
- ✅ Repetition: 10%
- ⚠️ Multi-file: 0%
- ⚠️ Code review: 0%

### Target (Iter10)
- Standard: >70% pass, >3.5/5 avg
- Agentic: >85% pass, >4.5/5 avg
- Tool obsession: <5%
- Repetition: <5%
- Multi-file: >50%
- Code review: >60%

## Lessons Learned

### Critical Rules (Never Break)
1. **Never use 4-bit quantization** - Causes catastrophic corruption on H100
2. **Always match training and deployment precision** - No conversion during merge
3. **Always backup before experiments** - Saves hours of debugging
4. **Always test simple queries first** - Catches corruption immediately
5. **Balance dataset carefully** - Over-representation causes mode collapse

### Best Practices
1. **Full precision on H100:** Uses only 21% of capacity, no downsides
2. **50/50 agentic/direct split:** Prevents tool obsession
3. **2 epoch training:** Optimal convergence for 12k dataset
4. **LoRA r=16:** Sweet spot for 7B models
5. **Validation before evaluation:** Simple test saves evaluation time

### Common Pitfalls
1. Ignoring merge warnings → Corrupted model
2. Over-representing one category → Mode collapse
3. Skipping simple tests → Wasted evaluation time
4. Not backing up → No recovery path
5. Copying settings from smaller GPUs → Unnecessary quantization

---

**Project Status:** ✅ Production Ready  
**Next Milestone:** Iter10 with improved multi-file and code review  
**Contact:** Harshil + AI Assistant  
**Last Model Training:** December 16, 2025
