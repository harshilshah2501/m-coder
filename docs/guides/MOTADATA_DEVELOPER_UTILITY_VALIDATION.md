# Motadata developer utility validation

This document describes the **developer utility** validation track: whether **Ask**, **Debug**, and **Plan** outputs are *useful* on Motadata-shaped tasks, beyond transport and contract correctness. It assumes the same **Layer-5 → Layer-3** path as production verification (evidence from Context Layer, decisions from Plan-Gate); see `docs/ARCHITECTURE_4_LAYER.md`.

## How this differs from production / contract verification

| Track | Proves | Primary guide / artifact |
| ----- | ------ | ------------------------- |
| **Contract / system** | Healthy services, expected routes, response shapes, governance fields, repeatability | [MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md) (manual `curl` Ask v1: [§6.3.1](MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md#canonical-manual-ask-v1)) |
| **Developer utility** | Heuristic checks on groundedness, honesty on weak evidence, explain structure, plan/decision cues, and **multi-step** Ask/Debug/Plan scenarios | This guide + [motadata_developer_utility_scenarios.v1.json](../validation/motadata_developer_utility_scenarios.v1.json) |

Contract verification can pass while answers are vague or misleading; utility checks are an **additional** signal, not a replacement for human review.

## Scenario tiers

### Core (v1 baseline)

The original four scenarios cover anchored ask, broad ask honesty, anchored debug, and bounded plan.

### Extended / complex (same file)

Additional scenarios stress **multi-hop Ask**, **planning-style Ask** (still `PLAN_ONLY`), **second debug anchor** (APIServer + mail config), and **second plan** (phased rollout + rollback language). They are intended for **better evaluation** of narration and grounding before tightening gates.

| id | capability | What it stresses |
|----|------------|------------------|
| `ask_structural_api_base_class` | ask | Structural / inheritance wording (`AbstractAPI`) |
| `ask_architecture_api_entrypoints` | ask | Multi-component architecture (APIServer → handlers) |
| `ask_discovery_notification_handlers` | ask | Discovery / list-style answers (notifications) |
| `ask_planning_refactor_alert_pipeline` | ask | Planning-framed question; allows WEAK evidence + honesty |
| `debug_apiserver_route_registration` | debug | Route / `start()` failure modes with **APIServer.java** anchor |
| `debug_mail_tls_config_path` | debug | Mail **MailServerConfiguration.java** lifecycle / staleness |
| `plan_phased_rollout_rollback_alert_enrichment` | plan | Rollout / rollback / validation vocabulary in `/v0/plan` response |

**Paths** in JSON use example roots (`/home/harshil/Projects/Motadata`). Override with `--workspace-root` when running the verifier so evidence resolves against your checkout.

## What is *not* claimed

- **Stage 3 loop** (or any multi-step product agent) end-to-end usefulness on real traffic is **not** treated as closed by this track.
- Utility assertions are **approximate**: they use text matching, path overlap, and simple counts. Tune scenarios when the model or retrieval stack shifts.
- **Plan** scenarios depend on Plan-Gate `/v0/plan` behavior; stubs may return sparse JSON—failures often mean **tighten prompts/stub**, not only retrieval.

## Scenario file and verifier

- Scenarios: [docs/validation/motadata_developer_utility_scenarios.v1.json](../validation/motadata_developer_utility_scenarios.v1.json)
- Verifier: `runtime/scripts/motadata_behavior_verify.py`
- JSON report key: `developer_utility_suite` (alongside `scenario_suite` for contract scenarios).

### Utility-only (behavior verify)

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/path/to/Motadata" \
  --utility-scenarios docs/validation/motadata_developer_utility_scenarios.v1.json \
  --scenarios-only \
  --print dev \
  --out runtime/.run/motadata_behavior_validation.json
```

### One-shot batch: utility suite + prompt batch + reports

Runs **(1)** the full developer utility suite (all Ask / Debug / Plan scenarios above) and **(2)** the fast `mcoder prompt` four-query batch from [run_mcoder_prompt_batch.py](../../runtime/eval/run_mcoder_prompt_batch.py). Writes a **merged JSON** and a **Markdown summary** under `runtime/eval/reports/`.

```bash
export MOTADATA_GATE_WORKSPACE_ROOT="/path/to/Motadata"
# Optional if not localhost defaults:
# export MCODER_CONTEXT_URL=http://127.0.0.1:8091
# export MCODER_PLAN_GATE_URL=http://127.0.0.1:8089

python3 runtime/eval/batch_run_developer_eval.py \
  --workspace-root "$MOTADATA_GATE_WORKSPACE_ROOT" \
  --timeout-sec 600
```

Options:

| Flag | Meaning |
|------|---------|
| `--skip-prompt-batch` | Only run `motadata_behavior_verify` utility scenarios (no `mcoder` CLI batch). |
| `--utility-scenarios PATH` | Alternate scenario JSON (default: `docs/validation/motadata_developer_utility_scenarios.v1.json`). |
| `--reports-dir DIR` | Output directory (default: `runtime/eval/reports/`). |

**Artifacts produced** (timestamp in filename):

- `runtime/eval/reports/behavior_verify_utility_<UTC>.json` — raw `--out` from behavior verify.
- `runtime/eval/reports/developer_eval_batch_<UTC>.json` — merged report (verify subprocess + optional prompt batch + summary).
- `runtime/eval/reports/developer_eval_batch_<UTC>.md` — human-readable pass/fail summary by capability.
- `runtime/eval/mcoder_prompt_batch_report.json` — overwritten each prompt-batch run (when not skipped).

The prompt batch requires `workspace/.mcoder/venv/bin/mcoder` installed for that workspace; if missing, the batch continues and records **skipped** in the merged JSON.

### Contract + utility (full smoke)

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "/path/to/Motadata" \
  --repeat 2 \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --utility-scenarios docs/validation/motadata_developer_utility_scenarios.v1.json \
  --print dev
```

## Evaluation / narration backlog

For golden prompts, rubrics, and banned diagnostic phrasing in user-visible prose, see [BACKLOG_NARRATION_CIG_HOSTING.md](BACKLOG_NARRATION_CIG_HOSTING.md) and [P0_ASK_NARRATION_AUDIT.md](P0_ASK_NARRATION_AUDIT.md). Utility batch reports complement—not replace—that narration QA.

## Keeping the suite maintainable

- Prefer **anchored** questions and **explicit** file paths in Debug scenarios so failures are diagnosable.
- Keep the suite **small number of high-signal** rows; add new scenarios when you discover recurring regression patterns.
- After changing Plan-Gate or Context Layer contracts, re-run the **batch** and archive `developer_eval_batch_*.json` for comparison.
