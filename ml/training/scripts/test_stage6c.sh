#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PY="$REPO_ROOT/ml/training/pipeline/stage6/.venv/bin/python"

export PYTHONPATH="$REPO_ROOT/ml/training/pipeline:$REPO_ROOT/ml/training"

"$PY" -m pytest -q "$REPO_ROOT/ml/training/pipeline/stage6/stage6c/tests"