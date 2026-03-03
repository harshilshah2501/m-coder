You are GitHub Copilot in plan-only mode.

Goal
Produce a strict execution plan to achieve a legitimate non-dummy Stage-6C pass and then Stage-7 freeze, without changing gate thresholds or bypassing collapse logic.

Constraints
- No code edits in this phase.
- No threshold relaxations.
- No metric bypasses.
- Use the existing Stage-6C and Stage-7 entrypoints.
- Prefer deterministic, reproducible runs.

Environment Assumptions
- ROOT=/home/harshil/Harshil-PoCs/m-coder
- MODEL=/home/harshil/models/Qwen2.5-14B-Instruct
- LoRA checkpoint available from Stage-08D
- Active Python environment contains stage6 package and vLLM

Phase A — Preflight Validation
1. Confirm entrypoints exist:
   - stage6c-run-suite
   - stage6c-freeze
2. Confirm model artifacts and LoRA path exist.
3. Confirm GPU availability and no stale vLLM engines consuming memory.
4. Confirm config paths:
   - canonical suite config
   - gating config (constitution-only profile)

Phase B — Canonical Non-Dummy Run (with LoRA)
1. Export deterministic runtime vars:
   - STAGE6C_DEBUG=1
   - STAGE6C_EAGER=1
   - STAGE6C_LORA_PATH=<lora_checkpoint_path>
2. Run Stage-6C suite with real adapter:
   - model=qwen25_14b
   - model path set to local Qwen2.5-14B-Instruct
   - fixed seeds for reproducibility
3. Write outputs to a fresh OUT directory.

Phase C — Legitimacy & Evidence Checks
1. Validate output artifacts exist:
   - OUT/stage6c_ledger.jsonl
   - OUT/suite_traces.jsonl
2. Verify traces show real generation behavior (non-dummy characteristics).
3. Verify constitution wrapper presence and system-role formatting in traces.
4. Aggregate collapse counts and severities from ledger.

Phase D — Pass/Fail Decision
1. PASS only if non-dummy evidence is present and collapse policy goals are met (targeting T-BYPASS=0 and S3=0).
2. If FAIL:
   - Keep gates unchanged.
   - Record dominant collapse types and likely root causes.
   - Plan next model/prompt/data iteration without code-level gate edits.

Phase E — Stage-7 Freeze (only after pass)
1. Execute freeze command using Stage-6C ledger from PASS run.
2. Produce immutable freeze artifacts and manifest.
3. Verify freeze outputs are complete and reference the exact run lineage.

Phase F — Handoff Package
Provide a concise report containing:
- Commands executed.
- Environment values used.
- Artifact paths.
- Collapse summary table.
- Pass/fail decision and rationale.
- Freeze status (executed or blocked by failed pass).

Suggested Command Block
ROOT=/home/harshil/Harshil-PoCs/m-coder
CFG="$ROOT/ml/training/pipeline/stage6/stage6c/config"
MODEL=/home/harshil/models/Qwen2.5-14B-Instruct
LORA=/home/harshil/Harshil-PoCs/m-coder/ml/training/pipeline/stage08/checkpoints/phase08D/checkpoint-38
SEEDS="101,202,303"
OUT="$ROOT/ml/training/generated/stage6c_runs/canonical_non_dummy_$(date +%Y%m%d_%H%M%S)"

STAGE6C_DEBUG=1 STAGE6C_EAGER=1 STAGE6C_LORA_PATH="$LORA" \
stage6c-run-suite \
  --config "$CFG/canonical_config.yaml" \
  --model qwen25_14b \
  --model-path "$MODEL" \
  --seeds "$SEEDS" \
  --out "$OUT"

jq -r '.collapse_type // "none"' "$OUT/stage6c_ledger.jsonl" | sort | uniq -c | sort -nr
jq -r '.severity // "NA"' "$OUT/stage6c_ledger.jsonl" | sort | uniq -c | sort -nr

Stop Conditions
- Stop immediately if adapter is not real/non-dummy.
- Stop immediately if required artifacts are missing.
- Do not proceed to freeze unless Stage-6C pass criteria are satisfied.

Risk Notes
- Environment drift between .venv locations can invalidate runs.
- Stale GPU processes can cause false OOM/failures.
- Older artifacts may contain placeholder traces; always validate against fresh OUT directory.

Expected Diff List (if implementation phase is requested next)
- ml/training/pipeline/stage6/stage6c/model/qwen25_14b.py
- ml/training/pipeline/stage6/stage6c/injections/profiles.py
- ml/training/pipeline/stage6/stage6c/injections/wrapper.py
- ml/training/pipeline/stage6/stage6c/config/gating_config.yaml
- (optional ops-only) ml/training/pipeline/stage08/base_model symlink