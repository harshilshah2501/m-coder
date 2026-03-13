#!/usr/bin/env bash
set -euo pipefail

# prepare_exemplars.sh
# ---------------------
# Build-time script to mirror Golden Exemplars from governance into the ML
# training build directory.
#
# Source of truth (authoring location):
#   governance/golden-exemplars/Phases/**
#
# Mirror consumed by training and evaluation:
#   ml/training/_build/exemplars/**
#
# This script is intentionally simple at first; it can be extended with
# checksum/manifest generation and CI hooks as the workflow matures.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_DIR="${REPO_ROOT}/governance/golden-exemplars/Phases"
DEST_DIR="${REPO_ROOT}/ml/training/_build/exemplars"

echo "[prepare_exemplars] Source: ${SRC_DIR}"
echo "[prepare_exemplars] Destination: ${DEST_DIR}"

if [[ ! -d "${SRC_DIR}" ]]; then
  echo "[prepare_exemplars] ERROR: Source directory does not exist." >&2
  exit 1
fi

rm -rf "${DEST_DIR}"
mkdir -p "${DEST_DIR}"

cp -R "${SRC_DIR}/" "${DEST_DIR}/"

echo "[prepare_exemplars] Mirror updated successfully."

