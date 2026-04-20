# Motadata verification — simple path (start here)

If the docs feel like a maze, use **only this page** until you know which branch you need. Everything else is optional depth.

---

## Pick one

| You want | Do this | Deeper detail (only if stuck) |
|----------|---------|--------------------------------|
| **A — Automated regression** (pinned tests, CI-style pass/fail) | [§ A — One verifier command](#a--automated-checks-scenario-suite) | [MCODER_USER_SCENARIOS_GUIDE.md](MCODER_USER_SCENARIOS_GUIDE.md) |
| **B — Any question over HTTP** (your own query text, no scenario JSON) | [§ B — Manual Ask (curl)](#b--manual-ask-your-own-query) | [docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md §6.3.1](docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md#canonical-manual-ask-v1) (single maintained `run_v1_ask` block) |
| **C — First-time setup, ports, services, tunnels** | [§ C — Setup](#c--first-time-setup) | Same production guide §2–4 |

**Rule of thumb:** Scenario files pin **fixed** questions + **fixed** expectations. Your **own** wording uses **§ B** (or the verifier **without** `--scenarios-only` and with `--query`, see § A.2).

---

## A — Automated checks (scenario suite)

**Prerequisites:** Context Layer + Plan-Gate (+ vLLM for model-backed paths) running; `MOTADATA_REPO_ROOT` points at your Motadata tree.

From the **m-coder repo root**:

```bash
export M_CODER_ROOT="$(pwd)"
export PYTHONPATH="$M_CODER_ROOT"
export MOTADATA_REPO_ROOT="/path/to/your/Motadata"   # required

# Full pinned suite, human-readable stdout
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --scenarios docs/validation/motadata_aiops_behavior_scenarios.v1.json \
  --quality-policy docs/validation/motadata_evidence_quality_policy.v1.json \
  --scenarios-only \
  --print plain \
  --out runtime/.run/motadata_behavior_validation.json
```

Exit code **0** = all scenarios passed. JSON report: `runtime/.run/motadata_behavior_validation.json`.

### A.2 Same stack, but **your** Ask + Debug strings (smoke, not pinned scenarios)

Omits `--scenarios-only`; uses `--query` / `--debug-query` for the smoke pipeline only:

```bash
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  --query "Your natural language question about the repo" \
  --debug-query "Your EXPLAIN_DEBUG prompt" \
  --print concise
```

---

## B — Manual Ask (your own query)

**Prerequisites:** `WORKSPACE_ROOT` = Motadata path, `CONTEXT_URL`, `PLAN_GATE_URL` reachable (defaults often `http://127.0.0.1:8091` and `http://127.0.0.1:8089`). Set `TOP_K` (e.g. `8`).

**Single source of truth:** copy the **`run_v1_ask`** shell function from **[docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md §6.3.1](docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md#canonical-manual-ask-v1)** into your shell (do not maintain a second copy in this file).

```bash
export WORKSPACE_ROOT="${MOTADATA_REPO_ROOT:?set Motadata path}"
export CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
export PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
export TOP_K="${TOP_K:-8}"
# Then paste run_v1_ask from the production guide §6.3.1 and run:
# run_v1_ask "Your question about the repo" /tmp/ask_out.json
```

**Debug / EXPLAIN_DEBUG** uses the same export step, then `POST /v1/ask` with `task_type`, `selected_file`, and `client_context` — full shape is in the production guide §6 Option B; do not guess fields.

---

## C — First-time setup

1. Open **[docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md](docs/guides/MOTADATA_AIOPS_PRODUCTION_VERIFICATION_GUIDE.md)** from the top and follow **§2–4** (services, URLs, workspace env).
2. When things run, come back to **§ A** or **§ B** above.

---

## Optional: read the verifier output

**[docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md](docs/demo/MOTADATA_BEHAVIOR_VERIFY_OUTPUT_GUIDE.md)** — what `all_pass`, smoke vs scenarios, and `--print dev` mean.

---

## If you need the full map

**[docs/NAVIGATION_HUB.md](docs/NAVIGATION_HUB.md)** — indexed links for every other doc (use only after the simple path above).
