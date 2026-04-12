#!/usr/bin/env bash
# Run all 8 AIOps MVP scenarios (Context Layer export + Plan-Gate /v1/ask) and write artifacts + summary.
# Usage (from repo root on WSL):
#   export MOTADATA_ROOT=/home/harshil/Projects/Motadata
#   export CONTEXT_URL=http://127.0.0.1:8091
#   export PLAN_GATE_URL=http://127.0.0.1:8089   # or tunneled URL
#   export AIOPS_MVP_LIVE_HTTP_TIMEOUT=600      # export_evidence; default ask timeout too
#   export AIOPS_MVP_ASK_HTTP_TIMEOUT=7200      # optional: longer /v1/ask (tunnel + LLM)
#   export AIOPS_MVP_ASK_RETRIES=3              # optional: retries on connection reset through SSH
#   ./scripts/run_aiops_mvp_scenario_pack.sh
#
# Optional: --fail-fast  --scenario A1  -v / --verbose (timestamps on stderr per HTTP phase)
# Optional: export AIOPS_MVP_VERBOSE=1

set -euo pipefail

MCODER="${M_CODER_ROOT:-}"
if [[ -z "${MCODER}" ]]; then
  MCODER="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
cd "${MCODER}"
export PYTHONPATH="${MCODER}${PYTHONPATH:+:$PYTHONPATH}"

exec python3 "${MCODER}/scripts/aiops_mvp_run_all.py" "$@"
