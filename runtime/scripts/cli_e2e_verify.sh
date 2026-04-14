#!/usr/bin/env bash
#
# CLI end-to-end smoke: Context Layer POST /v1/export_evidence → Plan-Gate POST /v1/ask
# (same path as evidence-first IDE flow, without the plugin).
#
# Prerequisites (from repo root):
#   ./runtime/scripts/run_local_stack.sh start-plan-gate
#   ./runtime/scripts/run_local_stack.sh start-context
#   ./runtime/scripts/run_local_stack.sh health
#
# Usage:
#   QUERY='How does plan-gate routing work?' \
#   WORKSPACE_ROOT=/abs/path/to/indexed/workspace \
#   bash runtime/scripts/cli_e2e_verify.sh
#
# Defaults:
#   WORKSPACE_ROOT — absolute path to this m-coder checkout (detected from script location)
#   QUERY — short repo question if unset
#   CONTEXT_URL / PLAN_GATE_URL — same as verify_ask_path.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export WORKSPACE_ROOT="${WORKSPACE_ROOT:-$REPO_ROOT}"
export QUERY="${QUERY:-What is the purpose of the runtime/plan_gate_service package?}"
export CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
export PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"

echo "═══════════════════════════════════════════════════════════════"
echo "  CLI E2E: export_evidence → POST /v1/ask"
echo "═══════════════════════════════════════════════════════════════"
echo "  WORKSPACE_ROOT=$WORKSPACE_ROOT"
echo "  QUERY=$QUERY"
echo "  CONTEXT_URL=$CONTEXT_URL"
echo "  PLAN_GATE_URL=$PLAN_GATE_URL"
echo ""

bash "$SCRIPT_DIR/verify_ask_path.sh"
