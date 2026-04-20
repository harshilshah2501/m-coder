# Governed Model Swap + SFT Adapter Regeneration Playbook

This playbook evaluates practical model swap options for the current Plan-Gate + vLLM stack and defines a governed SFT adapter regeneration path.

## Non-negotiable constraints

- Runtime governance remains unchanged: `PLAN_ONLY` and runtime boundary checks are authoritative.
- Explain/Debug model must be reachable via vLLM OpenAI-compatible endpoints.
- Any candidate must keep deterministic verifier behavior acceptable on existing scenario contracts.
- Assist remains advisory unless shadow metrics prove safe promotion.

## Current stack constraints (from runtime scripts)

- vLLM launcher expects a local base model path in `VLLM_BASE_MODEL`.
- Optional LoRA path is supported via `ADAPTER_PATH` and `--enable-lora`.
- Served model name is bound through `VLLM_SERVED_MODEL_NAME` and consumed by Plan-Gate.
- Readiness checks are strict on `/v1/models` and model-name presence.

## Model swap options

### Option A (lowest risk): keep Qwen2.5-Coder-14B base, regenerate adapter

- Best compatibility with current prompts, template assumptions, and existing training assets.
- Fastest path to improvement for Ask explanation quality and class-relationship precision.
- Recommended as immediate production candidate.

### Option B (medium risk): move to newer coder MoE model with manageable active params

- Potentially better reasoning and instruction-following.
- Requires prompt-shape revalidation and JSON-output stability checks in Explain/Debug.
- Use only after shadow A/B demonstrates no governance regressions.

### Option C (high risk): frontier large MoE model

- Highest ceiling, highest operational cost and tuning complexity.
- Greater risk of formatting drift, latency inflation, and unstable structured output.
- Treat as research branch, not immediate production swap.

## Recommendation

1. Execute Option A now (adapter regeneration on current 14B base).
2. Run Option B in shadow-only A/B after Option A baseline is stable.
3. Defer Option C until Option B clears safety and usefulness gates.

## Governed SFT adapter regeneration plan

## 1) Build training slices from governed traces

- Include only events with no hard violations.
- Prioritize `gold` and selected `silver` reward rows.
- Keep separate splits for Ask, Explain/Debug, and refusal-quality behavior.
- Use `runtime/scripts/build_governed_sft_dataset.py` to extract JSONL events with deterministic reward labels.

Example:

```bash
python3 runtime/scripts/build_governed_sft_dataset.py \
  --inputs "docs/validation/artifacts/assist_layer_v2_eval/assist_v2_batch_*.json" \
  --out /tmp/governed_sft_events.jsonl \
  --summary-out /tmp/governed_sft_events.summary.json
```

Interpretation note:

- If summary shows all rows as `banned` due `missing_ask_path`, those artifacts are not suitable for SFT pool.
- Feed Ask v1 artifacts (with `evidence_first_meta.ask_path`) to produce eligible `gold/silver` rows.

## 2) Data shaping rules

- Preserve explicit evidence-quality labels and posture metadata.
- Include "insufficient/no-match honesty" exemplars to prevent false-strong answers.
- Add targeted class-relationship examples (base/extends/implements/API-family queries).
- Include manual-query style prompts (not only full-file SEARCH/REPLACE formats).

## 3) Train adapter

- Keep LoRA/PEFT training on the same base model first.
- Keep sequence length and formatting objectives aligned with runtime request/response shapes.
- Save checkpoints and training metadata under a new versioned run folder.

## 4) Offline acceptance gates (must pass before serving)

- Structured output validity for Explain/Debug JSON contract.
- No increase in hallucination-like false-strong responses under WEAK/INSUFFICIENT evidence.
- Reward-score deltas non-negative on curated Ask query set.

## 5) Shadow serving and A/B verification

- Serve baseline and candidate on separate `VLLM_SERVED_MODEL_NAME` values.
- Compare using:
  - behavior verifier scenarios,
  - manual Ask query suite,
  - governed reward outputs.
- Promote only if candidate is equal-or-better on safety and clearly better on usefulness.

## 6) Rollback guardrail

- Keep previous adapter path immutable and launchable via env switch.
- Rollback trigger: any hard-violation regression or major degradation in scenario pass set.

## Minimal execution checklist

- Prepare candidate adapter artifact and config snapshot.
- Start candidate with `runtime/scripts/governed_services.sh` in isolated branch/session.
- Run:
  - `runtime/scripts/motadata_behavior_verify.py` on full scenario pack,
  - `runtime/scripts/motadata_query_cli.py --with-reward` on manual query set.
- Record baseline-vs-candidate deltas and decide promote/rollback.

