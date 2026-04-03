#!/usr/bin/env bash
# Run all 8 AIOps MVP scenarios (Context Layer export + Plan-Gate /v1/ask) and write artifacts + summary.
# Usage (from repo root on WSL):
#   export MOTADATA_ROOT=/home/harshil/Projects/Motadata
#   export CONTEXT_URL=http://127.0.0.1:8091
#   export PLAN_GATE_URL=http://127.0.0.1:8089   # or tunneled URL
#   export AIOPS_MVP_LIVE_HTTP_TIMEOUT=600      # optional
#   ./scripts/run_aiops_mvp_scenario_pack.sh
#
# Optional: ./scripts/run_aiops_mvp_scenario_pack.sh --fail-fast
# Optional: ./scripts/run_aiops_mvp_scenario_pack.sh --scenario A1

set -euo pipefail

MCODER="${M_CODER_ROOT:-}"
if [[ -z "${MCODER}" ]]; then
  MCODER="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
cd "${MCODER}"
export PYTHONPATH="${MCODER}${PYTHONPATH:+:$PYTHONPATH}"

exec python3 "${MCODER}/scripts/aiops_mvp_run_all.py" "$@"
