# P0 — Ask narration audit (one-shot checklist)

Use this **before** investing in retrieval (P1). Goal: know whether the gap is **narration** vs **thin evidence**.

## Steps

1. Run Ask with full JSON output (e.g. `mcoder prompt "…" --json` or `curl` to Plan-Gate `/v1/ask` after Context Layer export).
2. Record **`metadata.ask_narration_source`**:
   - `governed_vllm` — bounded vLLM narrator produced text (check Plan-Gate env: `MCODER_GOVERNED_ASK_NARRATOR`, `MOTADATA_EXPLAIN_VLLM_URL`).
   - `deterministic_unified` / `deterministic_legacy` — fell back to composed prose.
3. Skim **`metadata.reasoning_context`**: if typed nodes / flow steps / inheritance exist, retrieval is **not obviously empty**; prioritize **P2/P3** for tone.
4. Only if **`evidence_bundle`** lacks relevant files/snippets for the question, treat **P1** as triggered.

## Exit

One paragraph in your runbook: narrator source, fallback reason (timeout, validation, env off), and whether bundles looked thin.

See also: [BACKLOG_NARRATION_CIG_HOSTING.md](BACKLOG_NARRATION_CIG_HOSTING.md), [PASS_A_B_C_SETUP_VERIFICATION.md](PASS_A_B_C_SETUP_VERIFICATION.md).
