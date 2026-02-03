# Semantic Context Optimization - Trade-offs Analysis

## Changes Made

| Parameter | Before | After | Reduction |
|-----------|--------|-------|-----------|
| `rag_top_k` | 5 | 2 | 60% |
| `MAX_TOKENS_PER_FILE` | 2000 | 800 | 60% |
| `MAX_TOTAL_CONTEXT_TOKENS` | 20000 | 8000 | 60% |
| `max_tokens` (generation) | 1024 | 2048 | +100% ✅ |
| `MAX_METHOD_LINES` | unlimited | 50 | N/A |
| `MAX_FIELDS` | 20 | 5 | 75% |
| `MAX_IMPORTS` | 10 | 5 | 50% |

---

## Risk Assessment

### ⚠️ HIGH RISK Changes

**1. RAG top_k: 5 → 2 (60% reduction)**
- **Risk**: May miss relevant context from related classes
- **Impact**: If the task requires understanding 3-5 related classes, we'll only see 2
- **Mitigation**: The 2 most relevant results should still be highly pertinent (semantic search is good at ranking)

**2. MAX_FIELDS: 20 → 5 (75% reduction)**
- **Risk**: May miss important class fields needed for the modification
- **Impact**: If a method uses field #6-20, model won't see them
- **Mitigation**: Most methods only use 2-3 fields; 5 should cover common cases

### ⚙️ MEDIUM RISK Changes

**3. MAX_METHOD_LINES: unlimited → 50**
- **Risk**: Long methods will be truncated
- **Impact**: Model may not see the full logic flow
- **Mitigation**: 
  - We keep signature + first 25 lines + last 25 lines
  - Most methods are < 50 lines
  - Target method gets full 50 lines, context methods get 25 lines

**4. MAX_TOKENS_PER_FILE: 2000 → 800 (60% reduction)**
- **Risk**: Large files will be heavily truncated
- **Impact**: May lose important context from large classes
- **Mitigation**: 800 tokens ≈ 60 lines, enough for most class contexts

### ✅ LOW RISK Changes

**5. MAX_IMPORTS: 10 → 5**
- **Risk**: Minimal - imports are mostly for reference
- **Impact**: Model may not know all available libraries
- **Mitigation**: Most tasks only need 2-3 key imports

**6. max_tokens (generation): 1024 → 2048 (+100%)**
- **Risk**: NONE - this is a positive change!
- **Impact**: Model can generate longer, more complete diffs
- **Benefit**: Reduces truncation errors

---

## Expected Impact on Accuracy

### Positive Impacts ✅

1. **More generation tokens** (1024 → 2048)
   - Can generate complete multi-file diffs
   - Reduces "diff truncated" errors
   - **Expected improvement: +20-30% on multi-file tasks**

2. **Better token budget balance**
   - Before: 75% context, 25% generation (BAD)
   - After: 50% context, 50% generation (GOOD)
   - **Expected improvement: +30-40% on all tasks**

3. **Focused context**
   - Top 2 results are usually the most relevant
   - Less noise from marginally relevant results
   - **Expected improvement: +5-10% on precision**

### Negative Impacts ⚠️

1. **Missing related classes** (top_k: 5 → 2)
   - Complex refactorings may lack full context
   - **Expected degradation: -10-15% on complex multi-class tasks**

2. **Truncated long methods**
   - Methods > 50 lines will be incomplete
   - **Expected degradation: -5-10% on tasks with very long methods**

3. **Limited field visibility** (20 → 5)
   - May miss rarely-used fields
   - **Expected degradation: -5% on field-heavy modifications**

---

## Net Expected Outcome

### Baseline (Before Optimization)
- **Pass Rate**: 20% (2/10)
- **Main Issue**: 60% of tasks failed due to token limit
- **Secondary Issue**: 40% generated output but had malformed diffs

### Predicted (After Optimization)
- **Pass Rate**: 50-70% (5-7/10)
- **Reasoning**:
  - Fix token limit errors: +40% (6 tasks now work)
  - Better generation quality: +10-20% (fewer truncated diffs)
  - Lost context accuracy: -10-20% (some tasks may be less accurate)

### **Net Gain: +30-50% pass rate improvement**

---

## Recommendations

### If accuracy drops below 50%:

**Option 1: Adaptive Context (Smart)**
```python
# Measure query complexity and adjust context dynamically
if is_simple_task(query):
    top_k = 1  # Single-file modification
elif is_medium_task(query):
    top_k = 2  # Current setting
else:
    top_k = 3  # Complex multi-class refactoring
```

**Option 2: Hierarchical Context (Better)**
```python
# Layer 1: Minimal context (fast, always works)
# Layer 2: Medium context (current setting)
# Layer 3: Full context (only if tokens allow)

available_tokens = 16384 - estimated_input - 2048
if available_tokens > 10000:
    use_full_context()  # top_k=5
elif available_tokens > 5000:
    use_medium_context()  # top_k=2 (current)
else:
    use_minimal_context()  # top_k=1
```

**Option 3: Context Compression (Advanced)**
```python
# Remove comments, minify whitespace, use signatures
compressed_context = compress_code(raw_context)
# Can fit 2x more context in same token budget
```

### If accuracy is acceptable (50-70%):

**Keep current settings** and focus on:
1. Improving diff parsing (handle edge cases)
2. Better method name extraction from queries
3. Smarter field selection (use AST to find used fields)

---

## Monitoring Plan

After running the optimized benchmark, check:

1. **Token limit errors**: Should be 0% (down from 60%)
2. **Diff truncation errors**: Should be < 20% (down from 40%)
3. **Pass rate**: Target 50-70% (up from 20%)
4. **Context quality**: Review failed tasks to see if missing context was the issue

---

## Rollback Plan

If pass rate < 40%, revert these changes:
```bash
# In rag_api.py:
rag_top_k = 3  # Compromise between 2 and 5
MAX_TOTAL_CONTEXT_TOKENS = 10000  # Compromise between 8K and 20K

# In semantic_context_extractor.py:
MAX_FIELDS = 10  # Compromise between 5 and 20
MAX_METHOD_LINES = 75  # Compromise between 50 and unlimited
```

This gives us 62.5% of original context (vs 40% now) while still fitting in token budget.

