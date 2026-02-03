# V15 Dataset - Analysis and Recommendations

## Executive Summary

After comprehensive analysis, we've identified 3 critical questions that need decisions before finalizing the dataset for fine-tuning.

---

## Question 1: Do we need TRUE "direct generation" examples?

### Current State
- **Category**: `code_edits` (renamed from `direct_generation`)
- **Count**: 800 examples (30.8%)
- **Semantics**: Generate diffs from task description WITHOUT showing full file context

### Analysis
```
User Prompt: "Given a file and task description, generate the precise unified diff"
Assistant: Generates diff directly (no file context shown in prompt)
```

This is **different** from:
- `single_file`: Shows full file context in prompt
- `file_creation`: Creates new files from scratch

### Recommendation
✅ **KEEP** `code_edits` category - it's a valid use case for:
- Generating edits when file context is too large
- Testing model's ability to generate diffs from task descriptions alone
- Real-world scenario: "Fix bug X in file Y"

### Alternative: Add TRUE generation examples
If we want examples of "generate code from scratch" (not edits):
- Add category: `code_generation` (generate functions/classes from description)
- Example: "Write a function to calculate Fibonacci" → complete function code
- This would be different from `file_creation` (which creates full files)

**Decision needed**: Keep as-is OR add new `code_generation` category?

---

## Question 2: Should we add copyright headers to file_creation examples?

### Current State
- **With copyright**: 18/150 (12%)
- **Without copyright**: 132/150 (88%)

### Analysis
The dataset was created with instruction: "Do not include copyright headers"
This is visible in `tool_use` prompts:
```
Follow these guidelines:
1. Use relative file paths.
2. Do not include copyright headers.  ← EXPLICIT INSTRUCTION
3. Output tool calls as valid JSON...
```

### Options

#### Option A: Add copyright headers to dataset (RECOMMENDED)
**Pros**:
- Model learns to include headers automatically
- Matches real Motadata codebase
- Reduces manual work for developers

**Cons**:
- Need to regenerate 132 examples
- Increases dataset size slightly

**Implementation**:
```python
MOTADATA_COPYRIGHT = """/*
 * Copyright (c) {year} Mindarray Systems Pvt. Ltd.
 * All rights reserved.
 */
"""

def add_copyright_header(code: str, file_path: str) -> str:
    if file_path.endswith('.java'):
        return MOTADATA_COPYRIGHT.format(year=2024) + "\n" + code
    return code
```

#### Option B: Keep as-is, add headers via agent/IDE
**Pros**:
- No dataset changes needed
- Faster to production

**Cons**:
- Model won't learn to add headers
- Requires post-processing

#### Option C: Make it configurable
**Pros**:
- Model learns both styles
- Flexible for different use cases

**Cons**:
- More complex training

**Decision needed**: Which option to implement?

---

## Question 3: Industry-standard dataset evaluation methodology

### Pre-Fine-tuning Validation Checklist

#### 1. Data Quality Checks ✅

**Format Consistency**:
```bash
# Check all examples parse correctly
python validate_dataset.py --check-json

# Verify format consistency per category
python validate_dataset.py --check-formats

# Detect outliers (length, complexity)
python validate_dataset.py --detect-outliers
```

**Content Quality**:
- [ ] No duplicate examples
- [ ] No corrupted/truncated examples
- [ ] Balanced category distribution
- [ ] Appropriate difficulty distribution

#### 2. Statistical Analysis ✅

**Metrics to compute**:
```python
# Token distribution
- Mean tokens per example
- Median tokens per example
- 95th percentile (for context window planning)

# Category balance
- Examples per category
- Token distribution per category

# Complexity metrics
- Average file size
- Average number of edits per example
- Cyclomatic complexity (for code examples)
```

**Implementation**:
```bash
python analyze_dataset.py --compute-stats
```

#### 3. Holdout Set Creation ✅

**Industry Standard**: 80/10/10 split
- **Training**: 80% (2,079 examples)
- **Validation**: 10% (260 examples)
- **Test**: 10% (260 examples)

**Stratified Sampling**:
```python
# Ensure each category is represented in all splits
from sklearn.model_selection import train_test_split

# First split: train vs (val+test)
train, temp = train_test_split(
    dataset, 
    test_size=0.2, 
    stratify=dataset['category'],
    random_state=42
)

# Second split: val vs test
val, test = train_test_split(
    temp,
    test_size=0.5,
    stratify=temp['category'],
    random_state=42
)
```

#### 4. Baseline Evaluation ✅

**Before fine-tuning**, evaluate base model on test set:
```bash
# Evaluate base model (e.g., CodeLlama, DeepSeek)
python evaluate.py \
    --model deepseek-coder-33b \
    --dataset datasets/v15_test.jsonl \
    --output baseline_results.json
```

**Metrics**:
- **Exact Match**: % of examples with exact output match
- **BLEU Score**: Text similarity (0-100)
- **CodeBLEU**: Code-specific BLEU variant
- **Edit Distance**: Levenshtein distance
- **Compilation Success**: % of generated code that compiles
- **Test Pass Rate**: % that passes unit tests (if available)

#### 5. Data Leakage Check ✅

```python
# Check for overlap between train/val/test
def check_leakage(train, val, test):
    train_hashes = {hash(ex['messages'][-1]['content']) for ex in train}
    val_hashes = {hash(ex['messages'][-1]['content']) for ex in val}
    test_hashes = {hash(ex['messages'][-1]['content']) for ex in test}
    
    assert len(train_hashes & val_hashes) == 0, "Train/Val leakage!"
    assert len(train_hashes & test_hashes) == 0, "Train/Test leakage!"
    assert len(val_hashes & test_hashes) == 0, "Val/Test leakage!"
```

#### 6. Diversity Analysis ✅

**Check dataset diversity**:
```python
# File type diversity
file_extensions = extract_file_extensions(dataset)
print(f"File types: {Counter(file_extensions)}")

# Task diversity
task_types = extract_task_types(dataset)
print(f"Task types: {Counter(task_types)}")

# Code pattern diversity
patterns = extract_code_patterns(dataset)
print(f"Unique patterns: {len(patterns)}")
```

### Recommended Tools

1. **HuggingFace Datasets Library**:
```bash
pip install datasets
```

2. **CodeBLEU**:
```bash
pip install codebleu
```

3. **Custom Validation Script**:
```bash
python training/src/evaluation/validate_dataset.py
```

---

## Action Items

### Immediate (Before Fine-tuning)
1. [ ] **Decision**: Keep `code_edits` or add `code_generation` category?
2. [ ] **Decision**: Add copyright headers to dataset or handle in agent?
3. [ ] **Implement**: Dataset validation script
4. [ ] **Implement**: Train/val/test split (stratified)
5. [ ] **Run**: Baseline evaluation on test set
6. [ ] **Document**: Baseline metrics for comparison

### Nice-to-have
1. [ ] Add diversity metrics
2. [ ] Add complexity analysis
3. [ ] Create dataset card (HuggingFace format)
4. [ ] Version control for datasets

---

## Recommendations Summary

| Question | Recommendation | Priority |
|----------|---------------|----------|
| 1. Direct generation | Keep `code_edits`, optionally add `code_generation` | Medium |
| 2. Copyright headers | Add to dataset (Option A) | High |
| 3. Evaluation methodology | Implement full validation pipeline | Critical |


