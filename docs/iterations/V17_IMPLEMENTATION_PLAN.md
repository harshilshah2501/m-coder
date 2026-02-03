# V17 Implementation Plan

**Date**: 2026-01-05  
**Status**: 🚀 IN PROGRESS  
**Goal**: Add question-answering capability while maintaining code generation excellence

---

## 🎯 Executive Summary

V16 achieved **100% pass rate on code generation** but has a critical gap: **it cannot answer questions about code**. The model defaults to generating code even when asked "What does X do?" or "How does Y work?".

**V17 Goal**: Create a model that can BOTH:
1. ✅ Generate code (maintain V16's 100% pass rate)
2. ✅ Answer questions about code (NEW capability)

---

## 📊 Current State (V16)

### Strengths
- ✅ 100% capability pass rate (7/7 tests)
- ✅ 25.8% lower validation loss vs V15
- ✅ Excellent code generation
- ✅ 3,020 training examples

### Critical Gap
- ❌ **NO question-answering training data** (0 examples)
- ❌ **Defaults to code generation** for all queries
- ❌ **Cannot explain code** or answer "What/How/Why" questions
- ❌ **No evaluation for Q&A capability**

---

## 🔬 Phase 1: Base Model Evaluation

**Goal**: Determine if we should switch from Qwen2.5-Coder-7B-Instruct to Qwen2.5-14B-Instruct

### Models to Compare

| Model | Size | Specialization | Pros | Cons |
|-------|------|----------------|------|------|
| **Qwen2.5-Coder-7B-Instruct** | 7.6B | Code generation | Fast, specialized | Code bias, weak Q&A |
| **Qwen2.5-14B-Instruct** | 14B | General + Code | Better Q&A, reasoning | Slower, larger |

### Evaluation Tasks

#### 1. Question-Answering (50 questions)
- "What does the LogPatternCacheStore class do?"
- "How does the authentication flow work?"
- "Why is the database connection pooled?"
- "Explain the purpose of the retry mechanism"
- "What are the key methods in UserService?"

#### 2. Code Generation (50 tasks)
- Generate SEARCH-REPLACE blocks
- Create new files
- Refactor code
- Fix bugs
- Add features

### Success Metrics
- **Q&A Accuracy**: % of correct, non-code answers
- **Code Generation Pass Rate**: % of working code
- **Latency**: Average response time
- **Quality Score**: 1-5 rating

### Decision Criteria
- If Qwen2.5-14B-Instruct has **>30% better Q&A** with **<20% worse code gen**: SWITCH
- Otherwise: STAY with Qwen2.5-Coder-7B-Instruct

---

## 📝 Phase 2: Q&A Dataset Creation

**Goal**: Create 500-800 question-answering training examples

### Q&A Categories (Target: 600 examples)

#### Category 1: "What does X do?" (200 examples)
```json
{
  "messages": [
    {"role": "system", "content": "You are a code analysis assistant. Answer questions based on the provided code context."},
    {"role": "user", "content": "What does the LogPatternCacheStore class do?\n\nContext:\n[code snippet]"},
    {"role": "assistant", "content": "The LogPatternCacheStore class is responsible for caching log patterns in memory. It provides methods to:\n1. Store log patterns by ID\n2. Retrieve cached patterns\n3. Invalidate cache entries\n\nKey methods:\n- getPattern(id): Returns cached pattern\n- storePattern(id, pattern): Stores pattern in cache\n- invalidate(id): Removes pattern from cache"}
  ],
  "metadata": {"category": "question_answering_what"}
}
```

#### Category 2: "How does Y work?" (200 examples)
Focus on explaining mechanisms, flows, and processes.

#### Category 3: "Why is Z implemented this way?" (100 examples)
Focus on design decisions and rationale.

#### Category 4: "I don't have enough context" (100 examples)
Train model to admit when it lacks information.

### Dataset Generation Strategy
1. **Extract from existing codebase** (300 examples)
   - Use Motadata codebase
   - Generate Q&A pairs from real code

2. **Synthetic generation** (200 examples)
   - Use GPT-4 to generate Q&A pairs
   - Validate for quality

3. **Manual curation** (100 examples)
   - High-quality examples
   - Edge cases

---

## ⚖️ Phase 3: Dataset Balancing

**Goal**: Balance V17 dataset for optimal performance

### Target Composition (3,600 examples)

| Category | V16 Count | V17 Target | Change |
|----------|-----------|------------|--------|
| **Code Generation** | 3,020 | 1,440 (40%) | Reuse existing |
| **Question Answering** | 0 | 1,080 (30%) | NEW |
| **Mixed (Q&A + Code)** | 0 | 1,080 (30%) | NEW |
| **TOTAL** | 3,020 | 3,600 | +580 |

### Mixed Examples
Conversations that involve BOTH answering questions AND generating code:
```
User: "What does the authentication flow do? Can you add rate limiting?"
Assistant: [Explains auth flow] + [Generates rate limiting code]
```

---

## 🚀 Phase 4: V17 Training

**Configuration**:
- Base Model: TBD (Phase 1 decision)
- Dataset: 3,600 examples (balanced)
- Method: Full bfloat16 LoRA (same as V16)
- Epochs: 5
- Batch Size: 16
- Learning Rate: 2e-4

**Expected Training Time**: ~100 minutes

---

## ✅ Phase 5: V17 Evaluation

### Evaluation Suite

#### 1. Code Generation Tests (V16 suite)
- Maintain 100% pass rate
- No regression from V16

#### 2. Question-Answering Tests (NEW)
- 50 Q&A questions
- Target: 80%+ accuracy
- No code generation for questions

#### 3. Multi-turn Conversations (NEW)
- 20 conversation threads
- Target: 70%+ coherence

#### 4. "I Don't Know" Tests (NEW)
- 10 insufficient context scenarios
- Target: 90%+ correct refusal

### Success Criteria
- ✅ Code generation: 100% pass (maintain V16)
- ✅ Question answering: 80%+ pass
- ✅ Multi-turn: 70%+ pass
- ✅ "I don't know": 90%+ pass
- ✅ Latency: <6s average

---

## 📅 Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Base Model Eval | 2 days | 🔄 IN PROGRESS |
| Phase 2: Q&A Dataset | 3 days | ⏳ PENDING |
| Phase 3: Dataset Balance | 1 day | ⏳ PENDING |
| Phase 4: Training | 1 day | ⏳ PENDING |
| Phase 5: Evaluation | 1 day | ⏳ PENDING |
| **TOTAL** | **8 days** | |

---

**Next Step**: Start Phase 1 - Base Model Evaluation

