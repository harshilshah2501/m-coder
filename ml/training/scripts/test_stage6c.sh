#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$REPO_ROOT/ml/training/pipeline/stage6a/.venv/bin/python"

export PYTHONPATH="$REPO_ROOT/ml/training/pipeline"

"$PY" -m pytest -q "$REPO_ROOT/ml/training/pipeline/stage6/stage6c/tests" "$REPO_ROOT/ml/training/pipeline/phase6c/tests"