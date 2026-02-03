# Baseline Evaluation Results — Pre-Fine-Tuning

**Model**: Qwen2.5-Coder-7B-Instruct  
**Evaluation Date**: November 2025  
**Purpose**: Establish baseline metrics for measuring improvement from QLORA fine-tuning  
**Test Suite**: 12 coding tasks (deterministic evaluation, temperature=0, seed=42)

---

## Executive Summary

This document captures the **pre-fine-tuning baseline performance** of Qwen2.5-Coder-7B-Instruct on 12 coding tasks using a deterministic 5-metric scoring framework. These metrics serve as the "before" state against which post-fine-tuning improvements will be measured.

---

## Evaluation Metrics

### 5-Metric Framework

| Metric | Definition | Baseline Score |
|--------|-----------|-----------------|
| **Code Quality/Linter** | Syntactic correctness, adherence to style standards | 0.90 |
| **Logic** | Correctness of algorithm and control flow | 0.541 |
| **Entity Extraction** | Accuracy of identifying and using required entities/classes | 0.40 |
| **Hallucination** | Freedom from fabricated APIs/classes (1.00 = zero hallucinations) | 1.00 |
| **Format Strictness** | Adherence to required output format (SEARCH/REPLACE blocks) | 0.69 |

---

## Overall Baseline Performance

| Metric | Value |
|--------|-------|
| **Weighted Score** | 6.94/10 |
| **Average Inference Time/Task** | 12.56s |
| **Determinism Validated** | ✅ Run2=Run3 identical (reproducible) |

---

## Test Suite Details

### Coverage
- **Total Tasks**: 12 coding tasks
- **Task Categories**: Diverse coding scenarios (code edits, refactoring, pattern matching, etc.)
- **Dataset Domains**: Multiple dataset domains represented

### Deterministic Evaluation Configuration
```
Temperature: 0 (no sampling)
Seed: 42 (reproducible)
Framework: Hardware-aware quantization (4-bit/8-bit/FP16 support)
```

### Reproducibility Validation
- **Run 2**: Identical results to Run 3
- **Consistency**: 100% (deterministic config)
- **Implication**: Model outputs are reproducible; variation comes only from training/inference setup

---

## Interpretation

### Strengths
- ✅ **Code Quality (0.90)**: Model generates syntactically correct, style-compliant code
- ✅ **Hallucination (1.00)**: Zero hallucinated APIs in test set (model does not invent non-existent classes)
- ✅ **Format (0.69)**: Generally follows required SEARCH/REPLACE format

### Gaps
- ⚠️ **Logic (0.541)**: Algorithm correctness needs improvement (~54% accuracy)
- ⚠️ **Entity Extraction (0.40)**: Limited ability to identify and use required entities (~40% accuracy)

---

## Post-Fine-Tuning Targets

These baseline metrics establish the starting point for measuring improvement from fine-tuning with golden exemplars:

| Metric | Baseline | Target | Improvement Goal |
|--------|----------|--------|------------------|
| Logic | 0.541 | >0.70 | +13-16% |
| Entity Extraction | 0.40 | >0.70 | +30-33% |
| Hallucination | 1.00 | ≥0.95 | Maintain |
| Overall Accuracy | ~54% | >70% | +16-20% |

---

## Context: Model Selection

This model (Qwen2.5-Coder-7B-Instruct) was selected over alternatives (DeepSeek-Coder-6.7B, CodeLlama-7B) because:

1. **Best Code Quality**: 0.90 linter score (vs 0.30-0.60 for alternatives)
2. **Best Speed**: 12.56s/task (vs 27.43-27.50s for alternatives)
3. **Zero Hallucinations**: 1.00 hallucination score (tied with alternatives)
4. **Weighted Winner**: 6.94/10 overall score (best-in-class)

---

## Usage in Q3 OKR Assessment

This baseline is cited as evidence for Objective 3 (Fine-tuning & Prototype) to document:
- The starting performance before any fine-tuning iteration
- The 5-metric evaluation framework that will be used to measure improvement
- Deterministic reproducibility of evaluation methodology
- Clear post-training targets for golden exemplar-based SFT training

---

**Document Status**: ✅ Complete  
**Last Updated**: January 23, 2026  
**Scope**: Q3 2025 OKR self-assessment evidence
