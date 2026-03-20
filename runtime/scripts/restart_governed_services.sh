#!/usr/bin/env bash
#
# Restart governed services: stop (free ports), brief wait, then start.
# Uses same CONFIG_PATH as start/stop. Deterministic and clean.
#
# Usage:
#   ./runtime/scripts/restart_governed_services.sh
#   CONFIG_PATH=/path/to/demo_stack.env ./runtime/scripts/restart_governed_services.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STOP_SCRIPT="$SCRIPT_DIR/stop_governed_services.sh"
START_SCRIPT="$SCRIPT_DIR/start_governed_services.sh"

# Pass through CONFIG_PATH so stop and start use the same config
export CONFIG_PATH="${CONFIG_PATH:-}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Restart governed services"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Stop (allow 0 exit even if nothing was running)
"$STOP_SCRIPT" || true

echo "[STEP]  Waiting for ports to be released (2s)..."
sleep 2

# Start (must succeed)
"$START_SCRIPT"
