# DPO Implementation Plan for Motadata Coder V17

**Date:** 2026-01-08  
**Goal:** Add Direct Preference Optimization (DPO) as post-SFT training to fix instruction-following issues

---

## Executive Summary

Your current pipeline is **SFT-only**. DeepSeek invests 10x compute in RL. Adding DPO will:
- Fix hallucinations (e.g., "CorrectionProfileAPI" → "DiscoveryManager")
- Improve instruction adherence
- Reduce mode collapse on common patterns

---

## Phase 1: Generate Preference Data

### 1.1 Data Sources (Already Available)

| Source | Location | Use Case |
|--------|----------|----------|
| Evaluation results | `evaluation/results/*.json` | Failed vs passed examples |
| Model responses | `training/artifacts/results/v16_1_*/responses/` | Actual model outputs |
| Expected diffs | `evaluation/diffs/*.patch` | Ground truth |
| V13 Failure Report | `evaluation/reports/V13_FAILURE_ANALYSIS_REPORT.md` | Hallucination patterns |

### 1.2 Preference Pair Format

```json
{
  "prompt": "Create a new Java file CorrectionProfileAPI.java that...",
  "chosen": "```diff\n--- /dev/null\n+++ b/src/main/java/.../CorrectionProfileAPI.java\n...",
  "rejected": "```diff\n--- a/src/main/java/.../DiscoveryManager.java\n+++ b/..."
}
```

### 1.3 Data Generation Script

Create `datasets/generation/generate_dpo_pairs.py`:

```python
#!/usr/bin/env python3
"""Generate DPO preference pairs from evaluation results."""

import json
from pathlib import Path

EVAL_RESULTS = Path("training/artifacts/results/v16_1_evaluation")
DIFFS_DIR = Path("evaluation/diffs")
OUTPUT_FILE = Path("datasets/v17_dpo_pairs.jsonl")

def generate_pairs():
    pairs = []
    
    # Load evaluation results
    eval_file = EVAL_RESULTS / "v16_1_motadata_tasks_evaluation.json"
    with open(eval_file) as f:
        results = json.load(f)
    
    for result in results.get("results", []):
        task_id = result.get("task_id")
        passed = result.get("passed", False)
        
        # Load expected diff (chosen)
        diff_file = DIFFS_DIR / f"diff_{task_id.split('_', 1)[1]}.patch"
        if not diff_file.exists():
            continue
        
        chosen = diff_file.read_text()
        
        # Load model output (rejected if failed)
        response_file = EVAL_RESULTS.parent / "v16_1_improved_v2/responses" / f"{task_id}.txt"
        if not response_file.exists():
            continue
        
        rejected = response_file.read_text()
        
        # Only use failed examples where model output differs significantly
        if not passed and len(rejected) > 100:
            pairs.append({
                "prompt": result.get("prompt", ""),
                "chosen": chosen,
                "rejected": rejected,
                "task_id": task_id
            })
    
    # Save pairs
    with open(OUTPUT_FILE, 'w') as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")
    
    print(f"Generated {len(pairs)} preference pairs")
    return pairs

if __name__ == "__main__":
    generate_pairs()
```

### 1.4 Target: 500-1000 Preference Pairs

| Category | Source | Estimated Pairs |
|----------|--------|-----------------|
| Failed evaluations | Existing eval results | ~50 |
| Hallucination corrections | V13 failure patterns | ~100 |
| Synthetic rejections | Sample wrong files | ~200 |
| Format violations | Wrong diff format | ~150 |
| **Total** | | **~500** |

---

## Phase 2: DPO Training Script

### 2.1 Core Training Script

Create `training/src/finetuning/train_v17_dpo.py`:

```python
#!/usr/bin/env python3
"""
V17 DPO TRAINING - Post-SFT Preference Optimization
Base: V16.1 SFT Model (Qwen2.5-Coder-14B + LoRA)
Dataset: v17_dpo_pairs.jsonl
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, LoraConfig, get_peft_model
from trl import DPOTrainer, DPOConfig
from datasets import load_dataset

# Configuration
SFT_MODEL_PATH = "/home/harshil/Harshil-PoCs/models/v16_1_merged"
DPO_DATASET = "/home/harshil/Harshil-PoCs/datasets/v17_dpo_pairs.jsonl"
OUTPUT_DIR = "/home/harshil/Harshil-PoCs/models/v17_dpo"

def main():
    # Load SFT model (this becomes the reference model too)
    model = AutoModelForCausalLM.from_pretrained(
        SFT_MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    
    tokenizer = AutoTokenizer.from_pretrained(SFT_MODEL_PATH)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Add LoRA for DPO training
    lora_config = LoraConfig(
        r=8,  # Lower rank for DPO
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    
    # Load preference dataset
    dataset = load_dataset("json", data_files=DPO_DATASET, split="train")
    
    # DPO Config
    dpo_config = DPOConfig(
        output_dir=OUTPUT_DIR,
        beta=0.1,  # KL penalty coefficient
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=5e-7,  # Very low LR for DPO
        bf16=True,
        logging_steps=10,
        save_steps=100,
        max_length=4096,
        max_prompt_length=1024,
    )
    
    # DPO Trainer
    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # Will use implicit reference
        args=dpo_config,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )
    
    trainer.train()
    trainer.save_model(OUTPUT_DIR)

if __name__ == "__main__":
    main()
```

---

## Phase 3: Reward Criteria

### 3.1 What Makes a "Chosen" Response

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Correct file** | 40% | Modifies the file mentioned in instruction |
| **Valid diff format** | 20% | Proper `---`, `+++`, `@@` markers |
| **Compiles** | 20% | Java syntax is valid |
| **No hallucination** | 20% | Uses only existing APIs/classes |

### 3.2 What Makes a "Rejected" Response

| Pattern | Example |
|---------|---------|
| Wrong file | Asked for `CorrectionProfileAPI.java`, modified `DiscoveryManager.java` |
| Mode collapse | Always outputs `Patch8014.java` |
| Repetition loops | Repeating same code blocks |
| Invalid format | Missing diff markers |
| Hallucinated APIs | Using non-existent methods |

### 3.3 Automated Scoring Function

```python
def score_response(prompt: str, response: str, expected: str) -> float:
    """Score a response for preference ranking. Higher = better."""
    score = 0.0

    # 1. File correctness (40%)
    expected_files = extract_files_from_diff(expected)
    response_files = extract_files_from_diff(response)
    file_match = len(expected_files & response_files) / max(len(expected_files), 1)
    score += 0.4 * file_match

    # 2. Diff format validity (20%)
    has_markers = all(m in response for m in ['---', '+++', '@@'])
    score += 0.2 if has_markers else 0.0

    # 3. No repetition (20%)
    lines = response.split('\n')
    unique_ratio = len(set(lines)) / max(len(lines), 1)
    score += 0.2 * min(unique_ratio * 2, 1.0)

    # 4. Semantic similarity (20%)
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, expected, response).ratio()
    score += 0.2 * similarity

    return score
```

---

## Phase 4: Execution Plan

### 4.1 Prerequisites

```bash
# Install TRL (Transformer Reinforcement Learning)
pip install trl>=0.7.0

# Verify PEFT version
pip install peft>=0.6.0
```

### 4.2 Training Timeline

| Step | Duration | GPU Memory |
|------|----------|------------|
| Generate preference pairs | 30 min | CPU only |
| Load SFT model | 5 min | ~30GB |
| DPO training (1 epoch) | 2-3 hours | ~60GB |
| Merge & save | 10 min | ~40GB |

### 4.3 Execution Commands

```bash
# Step 1: Generate preference data
cd /home/harshil/Harshil-PoCs
python datasets/generation/generate_dpo_pairs.py

# Step 2: Run DPO training
python training/src/finetuning/train_v17_dpo.py

# Step 3: Merge LoRA weights
python training/src/finetuning/merge_v17_dpo.py
```

---

## Phase 5: Evaluation

### 5.1 Metrics to Track

| Metric | Before (V16.1) | Target (V17) |
|--------|----------------|--------------|
| Pass@1 | ~30% | >50% |
| File correctness | ~60% | >90% |
| Hallucination rate | ~20% | <5% |
| Instruction adherence | ~70% | >95% |

### 5.2 A/B Comparison Test

```python
# Compare V16.1 vs V17 on same prompts
PROMPTS = [
    "Create CorrectionProfileAPI.java...",
    "Modify DiscoveryManager to add...",
    "Refactor the SSH connection handling..."
]

# Run both models, compare outputs
```

---

## File Structure After Implementation

```
training/
├── src/finetuning/
│   ├── train_v16_1_surgical.py   # Existing SFT
│   └── train_v17_dpo.py          # NEW: DPO training
│
datasets/
├── v16_1_fixed/                  # Existing SFT data
├── v17_dpo_pairs.jsonl           # NEW: Preference pairs
└── generation/
    └── generate_dpo_pairs.py     # NEW: Pair generator
│
models/
├── v16_1_merged/                 # Current SFT model
└── v17_dpo/                      # NEW: DPO-enhanced model
```

---

## Quick Reference: DPO vs SFT

| Aspect | SFT (Current) | DPO (New) |
|--------|---------------|-----------|
| **Data format** | (prompt, response) | (prompt, chosen, rejected) |
| **Training signal** | Next-token prediction | Preference ranking |
| **Compute** | 1x | ~3x |
| **Effect** | Teaches format | Teaches preferences |

---

## Next Steps

1. **Immediate**: Run `generate_dpo_pairs.py` to create preference data
2. **This week**: Train V17 with DPO
3. **Validation**: Run Motadata-Bench comparison
4. **Iterate**: Add more preference pairs based on failures

---

## References

- [DPO Paper](https://arxiv.org/abs/2305.18290) - Direct Preference Optimization
- [TRL Documentation](https://huggingface.co/docs/trl) - DPOTrainer API
- DeepSeek-V3.2 Technical Report - RL training insights

