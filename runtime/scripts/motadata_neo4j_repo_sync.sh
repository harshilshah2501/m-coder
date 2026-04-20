#!/usr/bin/env bash
# GPU server: align Motadata checkout with remote, then refresh Neo4j class graph.
#
# Recommended: same git remote on WSL and GPU; this script runs `git pull --ff-only`
# on the GPU clone so drift vs WSL is bounded by push/pull discipline (or CI).
#
# Usage:
#   chmod +x runtime/scripts/motadata_neo4j_repo_sync.sh
#   MOTADATA_REPO_ROOT=/home/harshil/Projects/Motadata \
#   MCODER_ROOT=/home/harshil/Harshil-PoCs/m-coder \
#   ./runtime/scripts/motadata_neo4j_repo_sync.sh
#
# Environment:
#   MOTADATA_REPO_ROOT   Motadata workspace root on this host (default below)
#   MCODER_ROOT          m-coder repo root (default: parent of runtime/scripts)
#   SYNC_MODE            git | none  (default: git)
#   REFRESH_GRAPH        1 | 0       (default: 1) run neo4j_ask_stack refresh after sync
#   SOURCE_ENV_FILE      optional: source before refresh (default: $MCODER_ROOT/runtime/.run/neo4j_ask.env)
#
set -euo pipefail

MOTADATA_REPO_ROOT="${MOTADATA_REPO_ROOT:-/home/harshil/Projects/Motadata}"
SYNC_MODE="${SYNC_MODE:-git}"
REFRESH_GRAPH="${REFRESH_GRAPH:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCODER_ROOT="${MCODER_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
SOURCE_ENV_FILE="${SOURCE_ENV_FILE:-${MCODER_ROOT}/runtime/.run/neo4j_ask.env}"

log() { echo "[motadata-neo4j-sync] $*"; }

if [[ ! -d "${MOTADATA_REPO_ROOT}" ]]; then
  log "ERROR: MOTADATA_REPO_ROOT is not a directory: ${MOTADATA_REPO_ROOT}"
  exit 1
fi

case "${SYNC_MODE}" in
  git)
    if [[ ! -d "${MOTADATA_REPO_ROOT}/.git" ]]; then
      log "ERROR: not a git repository: ${MOTADATA_REPO_ROOT}"
      exit 1
    fi
    log "git pull --ff-only in ${MOTADATA_REPO_ROOT}"
    git -C "${MOTADATA_REPO_ROOT}" pull --ff-only
    ;;
  none)
    log "SYNC_MODE=none — skipping repository sync"
    ;;
  *)
    log "ERROR: unknown SYNC_MODE=${SYNC_MODE} (use git or none)"
    exit 1
    ;;
esac

if [[ "${REFRESH_GRAPH}" != "1" ]]; then
  log "REFRESH_GRAPH=0 — skipping Neo4j graph refresh"
  log "done"
  exit 0
fi

if [[ -f "${SOURCE_ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${SOURCE_ENV_FILE}"
else
  log "WARN: ${SOURCE_ENV_FILE} missing — ensure MOTADATA_NEO4J_* are set in environment"
fi

if [[ -z "${MOTADATA_NEO4J_PASSWORD:-}" ]]; then
  log "ERROR: MOTADATA_NEO4J_PASSWORD unset. Run neo4j_ask_stack.py bootstrap once, or export password."
  exit 1
fi

log "refresh Neo4j class graph (workspace-root=${MOTADATA_REPO_ROOT})"
python3 "${MCODER_ROOT}/runtime/scripts/neo4j_ask_stack.py" \
  --workspace-root "${MOTADATA_REPO_ROOT}" \
  refresh

log "done"
exit 0
