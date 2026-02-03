# Phase 2 – Technical Audit & Integration Plan
**Date:** 2026-01-09  
**Objective:** Prepare the codebase for DPO/GRPO integration and outline concrete implementation steps.

## Snapshot of Current Stack
- **Base Model:** Qwen2.5-Coder-14B (dense). SFT: v16_1 (working baseline). v16_2 broken. v17 not trained.
- **Training Infra:** H100; torch 2.9.1, transformers 4.57.3, peft 0.18.0, trl 0.26.2 (DPO-ready).
- **Serving:** vLLM via systemd orchestrator; version-agnostic name `motadata-coder` via env `VLLM_MODEL_NAME`.
- **RAG:** Qdrant (Jina embeddings) + Neo4j hybrid search; prompts built in `rag/src/orchestrator/agents/coder_agent.py`.

## Training Pipeline Findings
- **SFT Script (v16_2):** `training/src/finetuning/train_v16_2.py` — LoRA r=16, LR 2e-5, 3 epochs, max_len 4096, gradient checkpointing. Clean dataset but only SEARCH/REPLACE format; no create-file/simple instructions.
- **Merge Script (legacy):** `training/src/finetuning/merge_model.py` (unsloth merge path differs from current SFT flow).
- **DPO Script (ready):** `training/src/finetuning/train_v17_dpo.py` — uses v16_1 merged as base, DPO beta=0.1, LR=5e-7, LoRA r=8.
- **Preference Generator (scaffold):** `datasets/generation/generate_dpo_pairs.py` — needs verification logic and synthetic examples.

## RAG & Prompting Findings
- `rag/src/orchestrator/agents/coder_agent.py` builds prompts with patterns/examples but assumes model already knows to use them. Training never reinforced context usage, causing v16_2 to ignore RAG.
- `rag/src/api/rag_api.py` passes version-agnostic model name and sets conservative decoding defaults; infra is sound.

## Evaluation Findings
- `evaluation/comprehensive_model_evaluation.py` categorizes samples and renders HTML; missing:
  - Compilation checks
  - Test execution
  - Hallucination detection (non-existent APIs/files)
  - Context-usage scoring
  - Instruction-following suite (simple create-file/pattern-follow tasks)

## Critical Gaps
1) **Base checkpoint:** Need confirmed v16_1 merged model. If absent, retrain/merge v16_1.
2) **Preference data:** No v17_dpo_pairs.jsonl yet; generator lacks verification and synthetic tasks.
3) **Verification loop:** No compile/test gating to label chosen vs rejected.
4) **Context usage:** Training data does not teach using RAG context; prompts are fine, but model not reinforced.

## Integration Points (Files)
- **DPO training:** `training/src/finetuning/train_v17_dpo.py`
- **Preference generation:** `datasets/generation/generate_dpo_pairs.py`
- **SFT baseline (if needed):** `training/src/finetuning/train_v16_2.py` (adapt for v16_1)
- **RAG prompt path:** `rag/src/orchestrator/agents/coder_agent.py`
- **Evaluation harness:** `evaluation/comprehensive_model_evaluation.py`
- **Deployment config:** `rag/scripts/orchestrator_unified.sh` (update MODEL_PATH when new model ready)

## Week-by-Week Implementation Plan

### Week 1: Prep & Data
- Verify or recreate v16_1 merged checkpoint.
- Complete `generate_dpo_pairs.py`:
  - Add compilation verifier (javac) and optional test runner.
  - Extract failures from v16_2 evals; build chosen/rejected pairs.
  - Add 200–300 synthetic, verifiable tasks (hard to solve, easy to verify).
- Target: 500–1,000 preference pairs; 90/10 train/val split.

### Week 2: Train
- Run DPO with `train_v17_dpo.py` on v16_1 base.
- Monitor loss; save checkpoints each epoch; merged output `models/v18_dpo` (name TBD).
- Optional: quantize for deployment after evaluation.

### Week 3: Evaluate
- Enhance evaluation script to include:
  - Compile/test checks
  - Hallucination detection
  - Context-usage scoring (% of retrieved snippets referenced)
  - Instruction-following suite (100 cases: create-file, pattern-follow, multi-step)
- Run A/B vs v16_1 baseline; measure Pass@1, hallucination, instruction following, latency.

### Week 4: Decide & Deploy
- Go/No-Go based on targets: instruction following ≥70%, Pass@1 ≥50–70% (compile), hallucination ≤10%.
- If Go: update orchestrator MODEL_PATH, smoke test, and run canary.
- If No-Go: iterate with more pairs or adjust beta/LR.

## Immediate Action Items
- Confirm presence of `models/v16_1_merged/`; if missing, retrain/merge v16_1.
- Implement verification in `generate_dpo_pairs.py` and produce initial 300–500 pairs.
- Add compilation/test checks to `evaluation/comprehensive_model_evaluation.py`.
- Plan DPO run (20–30 GPU-hours on H100; ~$40–60 at $2/hr).

## Risks & Mitigations
- **No improvement after DPO:** Start with small beta=0.1, low LR; try 2nd run with more pairs.
- **Data noise:** Use compiler/test gates to label pairs; spot-check samples.
- **Latency increase:** Benchmark vs v16_1 before deployment; quantize if needed.
- **Context still ignored:** Add explicit prompts with retrieved context in preference pairs.

## Expected Outcomes
- Instruction following lifts from 0% (v16_2) to 70%+.
- Pass@1 (compile) improves from ~20–30% to 50–70%+.
- Hallucination drops to ≤10%.
- Maintains compatibility with existing RAG/orchestrator; minimal infra change.

---

# Detailed Addendum (Phase 2)

## File-by-File Audit Notes
- **training/src/finetuning/train_v16_2.py**: LoRA r=16, LR=2e-5, 3 epochs, max_len=4096; dataset assumes SEARCH/REPLACE only; no create-file/simple prompts; good H100 settings (bf16, grad ckpt).
- **training/src/finetuning/train_v17_dpo.py**: Ready for DPO; beta=0.1, LR=5e-7, LoRA r=8; base=v16_1_merged; uses TRL DPOTrainer.
- **datasets/generation/generate_dpo_pairs.py**: Scaffolding only; missing verification (compile/tests), missing synthetic task generator.
- **rag/src/orchestrator/agents/coder_agent.py**: Prompts include patterns/examples, but model never trained to use context; good place to log context usage during eval.
- **evaluation/comprehensive_model_evaluation.py**: Renders HTML; lacks compile/test checks, hallucination detection, context-usage scoring, instruction-following cases.

## DPO Data Specification (to implement)
- **Schema:**
  ```json
  {
    "prompt": "<user instruction + embedded RAG context snippets>",
    "chosen": "model output that compiles/passes tests/follows format",
    "rejected": "output that fails compile/tests or hallucinates"
  }
  ```
- **Context examples:** Include retrieved snippets (top-3) inline; add explicit instruction: "Use provided snippets; do not invent classes."
- **Verification gates:**
  - `javac` on generated file(s); mark success/failure.
  - Optional: minimal unit test runner (where available) for pass/fail.
  - Hallucination check: unresolved imports/classes → rejected.

## Synthetic Task Plan (hard to solve, easy to verify)
- **Templates:**
  - Create new API following pattern file X; must compile.
  - Modify method to add logging/validation; compile-only check.
  - Small bugfix with provided failing test (optional).
- **Counts:** Add 200–300 synthetic tasks to seed preference pairs; auto-verify via compile/tests.
- **Balance:** Mix create-file (new), pattern-follow, small edit; include context snippets.

## Evaluation Upgrades (implementation targets)
- **Compilation check:** For each output, write file, run `javac`; capture errors.
- **Test execution (if available):** Run minimal tests; record pass/fail.
- **Hallucination detection:** Parse compiler errors for unresolved symbols; flag rate.
- **Context-usage scoring:** Count how many retrieved snippet identifiers appear in output; target ≥80%.
- **Instruction-following suite:** 100 cases: create-file, pattern-follow, multi-step instructions; manual + automated assertions where possible.

## Week-by-Week with Acceptance Criteria
- **Week 1 (Prep/Data):**
  - v16_1 checkpoint confirmed or recreated.
  - `generate_dpo_pairs.py` produces ≥500 pairs with compile gate; ≤5% invalid lines.
  - Synthetic tasks ≥200 with compile success ≥80%.
- **Week 2 (Train):**
  - DPO run completes without OOM; loss curve stable/descending.
  - Checkpoints saved per epoch; final merged adapter stored.
- **Week 3 (Evaluate):**
  - Compile rate and Pass@1 reported; hallucination rate computed; context-usage % computed.
  - Instruction-following suite executed (100 cases) with score.
- **Week 4 (Deploy/Decide):**
  - Go if: instruction ≥70%, Pass@1 ≥50–70%, hallucination ≤10%, no latency regression >20% P95.

## Commands & Paths (for clarity)
- **Generate prefs:** `python datasets/generation/generate_dpo_pairs.py`
- **Train DPO:** `python training/src/finetuning/train_v17_dpo.py`
- **Evaluate:** `python evaluation/comprehensive_model_evaluation.py` (after adding compile/test hooks)
- **Deployment config:** `rag/scripts/orchestrator_unified.sh` → update MODEL_PATH to new merged model, keep `VLLM_MODEL_NAME=motadata-coder`.

## Risks with Triggers/Contingencies
- **DPO plateau or worse:** Trigger: loss not improving after 30% steps. Contingency: add more pairs; adjust beta 0.05–0.2; lower LR.
- **Data noise:** Trigger: >10% pairs fail compile gate. Contingency: tighten generator filters; manual spot-check sample.
- **Context still ignored:** Trigger: context-usage <60% after DPO. Contingency: add explicit context-copy tasks; increase weight of context-heavy prefs.
- **Latency regression:** Trigger: P95 > +20% vs v16_1. Contingency: reduce max tokens; enable quantization for deploy.

## Resource/Cost Check
- **Training:** 20–30 H100 hours (~$40–$60 @ $2/hr).
- **Data/verification:** CPU-bound; minor GPU.
- **Storage:** ~30GB for checkpoints/merged model.
