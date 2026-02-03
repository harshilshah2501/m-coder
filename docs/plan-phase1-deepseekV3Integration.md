# Phase 1 – DeepSeek-V3 Integration Research Findings
**Date:** 2026-01-09  
**Scope:** Should we integrate, augment, or replace the current Motadata-Coder architecture using DeepSeek-V3 techniques?  
**Baseline:** v16_1 (Qwen2.5-Coder-14B SFT) is the working reference; v16_2 and v17 are failed/abandoned attempts.

## Executive Summary
- **Recommendation:** Integrate DeepSeek-V3 training techniques (DPO/GRPO + synthetic tasks) on the existing dense 14B model. Skip MoE and sparse attention due to short-context workloads.
- **Why:** The primary failure in v16_2 is zero RL budget and training format mismatch, not base model capacity. DeepSeek’s main wins come from RL + synthetic, verifiable tasks.
- **Targets:** ≥50% usable coding output, ≥70% instruction following, Pass@1 ≥70% (compilation), hallucination ≤5%.

## DeepSeek-V3 Technical Highlights
- **Sparse Attention (DSA):** Two-stage indexer (FP8, d/16, k=2048). 3–6x speedup for >32K context; not useful for 8K code tasks. Skip.
- **RL Investment:** ~10% of total compute (GRPO); 5 stability fixes (unbiased KL, off-policy masking, MoE routing consistency, sampling mask preservation, specialist distillation). Closed 15–20% gap to frontier models.
- **Synthetic Agent Training:** 1,827 synthetic envs + 24,667 GitHub repos → 85K tasks. “Hard to solve, easy to verify.” Strong transfer to real tasks.
- **Limitations:** Token-inefficient (7–23% more tokens), smaller knowledge breadth vs GPT-5/Gemini, text-only, long-horizon agent gap.

## Current State & Failures
- **v15 (7B):** Working but limited; SEARCH/REPLACE edits only; no create-file; 20% compile, 0% feature completeness.
- **v16_1 (14B):** SFT only, added Q&A; not fully evaluated; likely same instruction-following issues.
- **v16_2 (14B):** **Broken** — 0% instruction following, ignores RAG, contradicts own reasoning. Root cause: training exclusively on SEARCH/REPLACE with full file context; never saw “create new file” or simple instructions.
- **v17 dataset:** 100% real Motadata code (2,411 ex). Training abandoned after v16_2 failure; pivot to DPO planned.

## Industry Best Practices & Case Studies
- **Wiz (1B Llama 3.2):** 86% precision, 82% recall for secrets detection → small models work with high-quality data.
- **Together AI + Morph Labs (Mistral 7B):** RAG fine-tuning teaches the model to use retrieved context; +16–19% vs Claude/GPT-4o.
- **Tabnine Enterprise:** Self-hosted Qwen/Llama for IDE assistance; validates on-prem/Qwen viability.
- **Evaluation (MS Copilot harness):** Real repos 3–5x harder than HumanEval; Pass@1, compile@k, UAR, latency crucial.

## Decision Framework (Integration vs Augmentation vs Replacement)
- **Integration (score 80/100):** Add DPO/GRPO + synthetic verified tasks on current dense 14B. Low risk, fast, infra-compatible.
- **Augmentation (81/100):** Add lightweight experts/router later. Higher complexity; good medium-term.
- **Replacement (43/100):** Adopting DeepSeek-V3 671B is infeasible on single H100; high risk; loses fine-tuning.
- **Conclusion:** Integrate now; consider augmentation later if needed.

## Root Causes Identified
1) Zero RL budget (pure SFT) → no instruction following/generalization.
2) Training format mismatch (SEARCH/REPLACE only; no create-file/simple instructions).
3) No verification loop (no chosen vs rejected signals; no compilation/test checks).
4) RAG usage not trained (context retrieved but ignored).
5) Task distribution mismatch (edits trained, creation requested).

## Success Metrics
- **Primary:** Coding output ratio ≥50%; instruction following ≥90%; Pass@1 (compilation) ≥70%; hallucination ≤5%.
- **Secondary:** Context utilization ≥80%; multi-file correctness ≥60%; user acceptance ≥30%; P95 latency <1.5s.

## Recommended Path (from Phase 1)
- Apply DPO/GRPO with 500–1,000 preference pairs (from failures + synthetic).
- Add synthetic, verifiable tasks (compile/test-based) following “hard to solve, easy to verify.”
- Teach context usage explicitly in training prompts.
- Skip DSA and MoE for now (short contexts, single H100 constraint).
- Maintain v16_1 as rollback baseline.

## Artifacts to Produce in Later Phases
- Preference dataset (chosen/rejected) with verification signals.
- Enhanced evaluation: compilation, tests, hallucination detection, context-usage scoring, instruction-following suite.
- DPO-trained model (v18 candidate) and A/B vs v16_1.

---

# Deep Dive Addendum (Phase 1)

## DeepSeek-V3 Technical Breakdown
- **DSA math (why we skip):** Indexer O(L^2·d_I) with d_I=d/16, FP8, k=2048 → helps only when L≫32K. Our workloads are ~4–8K; overhead would slow us down.
- **GRPO (what to copy):** Group-relative rewards, KL penalty with unbiased importance sampling, off-policy masking, MoE routing consistency, sampling mask preservation, specialist distillation. Net effect: stable RL with 10x more post-training compute than typical OSS.
- **Synthetic pipeline:** “Hard to solve, easy to verify” tasks; 1.8K synthetic envs + 24K real repos; auto-graded (tests/constraints). This is directly portable: compile/tests as verifier for Motadata tasks.
- **Limitations to remember:** Token inefficiency (7–23% more tokens), knowledge breadth smaller than GPT-5/Gemini (mitigate with RAG), text-only, long-horizon agent gap (~46% on TerminalBench vs 54% Gemini).

## Comparison Matrix (DeepSeek-V3 vs Motadata-Coder)
| Area | DeepSeek-V3 | Motadata-Coder | Action |
|------|-------------|----------------|--------|
| Arch | MoE + DSA, 128K ctx | Dense 14B, 8K ctx | Keep dense; no DSA needed |
| Training | SFT + GRPO (10% compute) | SFT only (0% RL) | Add DPO/GRPO |
| Data | 85K tasks (synthetic + real, verified) | ~3K tasks, no synthetic, no verification | Add synthetic + verification |
| Preference | Yes (relative rewards) | None | Generate chosen/rejected pairs |
| Inference req | 400GB VRAM for full MoE | 28GB fits H100 | Keep dense |
| Token eff. | 7–23% more tokens | Baseline | Acceptable; cost per token fine on self-hosted |

## KPIs with Measurement
- **Instruction following:** ≥90%; measured on 100 scripted tasks (create-file, pattern-follow, multi-step). Pass if output matches intent and format.
- **Pass@1 (compile):** ≥70%; run javac + minimal tests on evaluation set.
- **Hallucination:** ≤5%; unresolved imports/classes in compiled output.
- **Coding output ratio:** ≥50%; fraction of responses containing usable code blocks that compile or match pattern rules.
- **Context utilization:** ≥80%; % of RAG snippets referenced (string match / structural match).

## Risks & Mitigations (Phase 1 conclusions)
- **RL instability:** Start with beta=0.1, LR=5e-7, small batch; checkpoint often.
- **Data noise in prefs:** Gate with compile/tests; sample audit 50 pairs.
- **Latency from longer outputs:** Keep max_new_tokens reasonable (e.g., 512–1024 for code edits); measure P95.
- **Token inefficiency:** Accept for cost; enforce shorter generation via stop tokens and max tokens in orchestration.

## Resource & Timeline Estimates
- **Data generation:** 2–3 days to produce 500–1,000 preference pairs (reuse failures + synth tasks).
- **Training (DPO):** 20–30 H100 hours (~$40–$60 at $2/hr).
- **Evaluation:** 1–2 days to run enhanced harness + manual spot-checks.

## What to Integrate vs Skip
- **Integrate now:** DPO/GRPO-style preference learning; synthetic verifiable tasks; context-usage examples; specialist distillation-lite (code-focused samples as “specialist” signal).
- **Defer/skip:** DSA, MoE, 128K context, multi-modal. These add complexity without benefit for our 8K code workloads on a single H100.
