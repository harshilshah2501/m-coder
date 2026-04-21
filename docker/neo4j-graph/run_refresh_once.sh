#!/usr/bin/env bash
set -euo pipefail

JAVA_ROOT="${MOTADATA_JAVA_ROOT:?MOTADATA_JAVA_ROOT is required}"

python /workspace/tools/ast_indexer/ingest_java_graph.py \
  --java-root "$JAVA_ROOT" \
  --log-level INFO \
  --reset