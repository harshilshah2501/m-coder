# LLM Code Assistant Evaluation — Quick Reference Card

## Essential Metrics at a Glance

### Tier 1: Must-Have Metrics

| Metric | Definition | Target | How to Measure |
|--------|-----------|--------|----------------|
| **Pass@1** | Code passes all unit tests on first try | ≥ 0.65 | Run test suite on generated code |
| **Compilation Rate** | Generated code compiles without errors | ≥ 0.90 | Use tree-sitter parser + compiler |
| **User Acceptance Rate (UAR)** | % of suggestions developer keeps | ≥ 0.30 | Track accepts vs. rejects in IDE |
| **Latency (P95)** | Time to show suggestion | ≤ 1.2s | Log timestamp request → display |

### Tier 2: Production Quality Metrics

| Metric | Definition | Target | Why It Matters |
|--------|-----------|--------|----------------|
| **Hallucination Rate** | % suggesting non-existent APIs | ≤ 0.05 | Compiler errors = wasted time |
| **Feature Completeness** | Multi-file edits (API + Router + DB) | ≥ 0.80 | Production readiness |
| **CodeBLEU** | Semantic code similarity (not string match) | ≥ 0.72 | Evaluates real code quality |
| **Time-to-Ship** | Developer edits after acceptance | ≤ 90s | True productivity metric |

### Tier 3: Optional (Advanced)

| Metric | Definition | Target | Use Case |
|--------|-----------|--------|----------|
| **Cyclomatic Complexity Δ** | Over-engineered solutions | Δ ≤ +2 | Avoid bloated generated code |
| **Linter Pass Rate** | Follows style guide (eslint, pylint, spotbugs) | ≥ 0.90 | Code review friction |
| **Mean Reciprocal Rank (MRR)** | Codebase search quality (workspace queries) | ≥ 0.70 | For "explain this code" features |

---

## Task Types → Metrics Mapping

```
TASK                    PRIMARY METRIC      SECONDARY              VALIDATION
────────────────────────────────────────────────────────────────────────────
Code Generation         pass@1              Syntax%, CodeBLEU      Run test suite
Bug Fixing              Fix Rate (no new)   Syntax%, Linter Pass   Static analyzer
Doc Generation          Format%, Coverage   Syntax%                Parse docstring
Test Generation         Compile%, pass@1    Syntax%                Execute test
Workspace Query         MRR, Keywords       Latency                Manual review
────────────────────────────────────────────────────────────────────────────
```

---

## Test Dataset Composition (Recommended)

```
Type                        Count       Source                  Difficulty
─────────────────────────────────────────────────────────────────────────
Code Generation (Multi-File) 40-50     Git commits touching 3+ Easy→Hard
Bug Fixing (Real Errors)      20-30     Static analyzer reports Medium
RCA / Debugging                10-15     Jira tickets + logs      Hard
Code Review / Refactor         20-30     PR diffs from team       Medium
Test Generation               15-20     Uncovered methods        Hard
────────────────────────────────────────────────────────────────────────
Total:                        100-150
```

---

## Quick Evaluation Checklist

### Before Deployment

- [ ] **Pass@1 ≥ 0.65** on your domain-specific test set
- [ ] **Hallucination rate ≤ 5%** (unresolved references)
- [ ] **Syntax correctness ≥ 90%** (parses without errors)
- [ ] **P95 latency ≤ 1.2s** (no flow-breaking delays)
- [ ] **Feature completion ≥ 80%** (multi-file edits touch all required files)
- [ ] **CodeBLEU ≥ 0.72** (semantic quality, not just match)

### During Beta Testing (10-15 developers, 2-3 weeks)

- [ ] **UAR (User Acceptance Rate) ≥ 0.25** (otherwise users ignore it)
- [ ] **No compiler errors in >95%** of accepted suggestions
- [ ] **Feedback: "Helpful" ≥ 70%** (NPS or thumbs-up ratio)
- [ ] **Time-to-Productivity < 2 weeks** for new team members

### Production Monitoring (Weekly)

- [ ] **UAR trending stable or improving**
- [ ] **Hallucination rate creeping up?** → Retrain on failures
- [ ] **Latency increasing?** → Check vLLM queue depth
- [ ] **Feature completion degrading?** → Add more multi-file samples to training

---

## Tools & Framework Setup

### Recommended Stack

```
Component              Tool                Why
─────────────────────────────────────────────────────────────
Evaluation Harness     DeepEval            Open-source, pytest integration
IDE Plugin             Continue.dev        Works IntelliJ + VS Code
Model Serving          vLLM                10x+ throughput vs. standard
Dataset Management     Hugging Face Hub    Version control for datasets
Monitoring             Wandb or Prometheus Track metrics over time
─────────────────────────────────────────────────────────────
```

### 5-Minute Quick Start

```bash
# 1. Setup evaluation
pip install deepeval

# 2. Serve your model
vllm serve ./lora_model --port 8000

# 3. Install IDE plugin
# Continue.dev: https://www.continue.dev
# Configure .continuerc.json to point to localhost:8000

# 4. Run tests
python evaluate_model.py --dataset motadata_100.jsonl

# 5. View dashboard
# Results in console + export to JSON for dashboarding
```

---

## Common Pitfalls & Fixes

| Problem | Symptom | Root Cause | Fix |
|---------|---------|-----------|-----|
| **Hallucination** | Suggests non-existent methods | Missing RAG | Add semantic search over codebase |
| **Low UAR** | <20% acceptance | Suggestions too slow or wrong | Add behavior-aware filtering; tune thresholds |
| **Slow Latency** | >2s response time | Model too large or queue backed up | Use quantization (4-bit); reduce batch size |
| **Feature Incomplete** | Multi-file edits only touch 1 file | Single-file training | Add dataset of multi-file commits |
| **Style Mismatch** | Generated code fails linter | Not fine-tuned on your codebase | Add linter-passing examples to training |

---

## Metrics Dashboard Template (Weekly)

```
WEEK OF: 2026-01-13
═══════════════════════════════════════════════════════════

Correctness
  Pass@1 (code gen):           65.2%  ↑ +1.2% from week before
  Compilation rate:            91.8%  ↑ +0.5%
  Test execution pass:         72.1%  → flat
  Hallucination rate:           3.2%  ↓ -0.8% (good!)

User Experience
  User Acceptance Rate:        28.5%  ↑ +2.1% (behavior filtering helps)
  Latency P95:                989ms  ↓ -50ms (vLLM optimization)
  Feature Completion:          79.3%  → flat
  Developer Satisfaction:       4.2/5  ↑ +0.3pts (NPS)

Production
  Cost per suggestion:        $0.0012  ↓ -35% (fewer calls)
  Uptime:                     99.87%  ✓
  Avg Edit Time Post-Accept:    82s   ↓ -8s (shorter fixes)

Observations
  - Behavior filtering working: streaks of rejections suppress future calls
  - Top failure: "Forgot to update DBConstants" (8 cases)
    → Action: Add 10 more multi-file training samples
  - New developer using 3.2x more suggestions (learning curve normal)
```

---

## References & Recommended Reading

**Foundational Papers**
- "HumanEval: Hand-Crafted Evaluation Benchmark for Code Generation" (OpenAI, 2021)
- "Copilot Evaluation Harness" (Microsoft, 2024) — 5 task framework
- "Pre-Filtering via Developer Behavioral Telemetry" (ITMO, 2025) — UAR improvement

**Benchmarks**
- MERA Code (11 tasks, 8 languages): https://mera.a-ai.ru/en/code
- CodeXGLUE (14 tasks, leaderboard): https://microsoft.github.io/CodeXGLUE/

**Tools & Community**
- Continue.dev: Open-source IDE assistant framework
- DeepEval: Python testing library for LLMs
- vLLM: High-throughput LLM serving

---

**Last Updated**: January 6, 2026
**For**: Motadata Finetuned LLM PoC Evaluation
**Next Review**: After first 2-week beta test cycle
