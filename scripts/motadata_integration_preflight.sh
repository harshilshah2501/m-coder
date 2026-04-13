#!/usr/bin/env bash
# Motadata + m-coder integration preflight: prerequisites, health/version/commit parity,
# endpoint compatibility, and optional evidence-first Ask E2E smoke.
#
# Exit 0 only when checks pass (GREEN). Non-zero on any failure (RED).
#
# Usage:
#   ./scripts/motadata_integration_preflight.sh
#   VERIFY_ASK_E2E=1 MOTADATA_ROOT=/path/to/Motadata ./scripts/motadata_integration_preflight.sh
#
# Environment (inherits wsl_plugin_mvp_stack.sh):
#   M_CODER_REPO_ROOT     Optional; defaults to parent of scripts/
#   CONTEXT_URL           Default http://127.0.0.1:8091
#   PLAN_GATE_URL         Default http://127.0.0.1:8089
#   ALLOW_COMMIT_MISMATCH Set to 1 to warn instead of fail on git_commit drift
#
# Optional Ask E2E (after stack check succeeds):
#   VERIFY_ASK_E2E        Set to 1 to run runtime/scripts/verify_ask_path.sh
#   MOTADATA_ROOT or WORKSPACE_ROOT  Linux path for Context Layer exports (required if VERIFY_ASK_E2E=1)
#   PREFLIGHT_ASK_QUERY   Optional; default short smoke question
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${M_CODER_REPO_ROOT:-$SCRIPT_DIR/..}" && pwd)"
export M_CODER_REPO_ROOT="$REPO_ROOT"

CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"

echo "═══════════════════════════════════════════════════════════════════"
echo " Motadata integration preflight (m-coder)"
echo "═══════════════════════════════════════════════════════════════════"
echo "  M_CODER_REPO_ROOT=$REPO_ROOT"
echo "  CONTEXT_URL=$CONTEXT_URL"
echo "  PLAN_GATE_URL=$PLAN_GATE_URL"
if [[ -n "${MOTADATA_ROOT:-}" ]]; then
  echo "  MOTADATA_ROOT=$MOTADATA_ROOT"
fi
echo ""

bash "$REPO_ROOT/scripts/wsl_plugin_mvp_stack.sh" check

if [[ "${VERIFY_ASK_E2E:-0}" == "1" ]]; then
  wr="${MOTADATA_ROOT:-${WORKSPACE_ROOT:-}}"
  if [[ -z "$wr" ]]; then
    echo "[FAIL] VERIFY_ASK_E2E=1 requires MOTADATA_ROOT or WORKSPACE_ROOT" >&2
    exit 1
  fi
  if [[ ! -d "$wr" ]]; then
    echo "[FAIL] Workspace path does not exist: $wr" >&2
    exit 1
  fi
  export WORKSPACE_ROOT="$wr"
  export QUERY="${PREFLIGHT_ASK_QUERY:-Smoke: list top-level modules in this workspace.}"
  echo ""
  echo "Running optional Ask E2E (export_evidence + /v1/ask)…"
  bash "$REPO_ROOT/runtime/scripts/verify_ask_path.sh"
fi

echo ""
echo "GREEN — preflight passed. Safe to exercise JetBrains UI: Motadata → Ask / Explain / Plan, Submit to Runtime."
echo "  Plugin env: MOTADATA_PLAN_GATE_URL=$PLAN_GATE_URL  MOTADATA_CONTEXT_LAYER_URL=$CONTEXT_URL"
exit 0
