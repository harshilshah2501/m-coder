#!/usr/bin/env bash
#
# Build mcoder-suite wheel, prune older concrete wheels under dist/, and refresh
# dist/mcoder_suite-latest-py3-none-any.whl (stable path for pip on WSL).
#
# Prerequisites: pip install build (in the active env or venv).
#
# Usage:
#   bash build_wheel.sh
#
# Env:
#   MCODER_SUITE_WHEEL_KEEP  number of newest versioned wheels to retain (default 1)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p dist
python3 -m build --wheel -o dist
bash "$SCRIPT_DIR/link_mcoder_suite_latest.sh" --keep "${MCODER_SUITE_WHEEL_KEEP:-1}" "$SCRIPT_DIR/dist"
