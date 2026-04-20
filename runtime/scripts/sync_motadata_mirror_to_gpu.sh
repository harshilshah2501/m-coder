#!/usr/bin/env bash
# Sync Motadata workspace from a machine that has git access (e.g. WSL) to a GPU
# server mirror path, then optionally refresh the Neo4j class graph on the GPU.
#
# Required env:
#   MOTADATA_REPO_ROOT   Local absolute path to Motadata checkout (source of truth).
#   GPU_SYNC_HOST        ssh target, e.g. user@gpu-server.example.com
#   GPU_MIRROR_ROOT      Remote absolute directory for the mirror (created if missing).
#
# Optional env:
#   MCODER_REMOTE_ROOT   Path to m-coder on GPU (required when REMOTE_REFRESH=1).
#   MOTADATA_NEO4J_PASSWORD  Required when REMOTE_REFRESH=1 — forwarded to GPU for non-interactive refresh.
#   RSYNC_DELETE         If 1, pass --delete to rsync (default: 1).
#   REMOTE_REFRESH       If 1, SSH to GPU and run neo4j_ask_stack refresh (default: 0).
#   RSYNC_RSH            Passed to rsync -e (default: ssh). Example: ssh -i /path/to/key
#   SSH_OPTS             Extra args after ssh in RSYNC_RSH (e.g. -o StrictHostKeyChecking=no).
#
# Usage:
#   MOTADATA_REPO_ROOT=/path/to/Motadata GPU_SYNC_HOST=user@gpu GPU_MIRROR_ROOT=/data/motadata_mirror \
#     ./runtime/scripts/sync_motadata_mirror_to_gpu.sh
#
# Cron example (every 30 min):
#   */30 * * * * MOTADATA_REPO_ROOT=... GPU_SYNC_HOST=... GPU_MIRROR_ROOT=... \
#     MCODER_REMOTE_ROOT=/root/Harshil-PoCs/m-coder REMOTE_REFRESH=1 \
#     /path/to/m-coder/runtime/scripts/sync_motadata_mirror_to_gpu.sh >>/tmp/motadata_sync.log 2>&1

set -euo pipefail

MOTADATA_REPO_ROOT="${MOTADATA_REPO_ROOT:-}"
GPU_SYNC_HOST="${GPU_SYNC_HOST:-}"
GPU_MIRROR_ROOT="${GPU_MIRROR_ROOT:-}"
MCODER_REMOTE_ROOT="${MCODER_REMOTE_ROOT:-}"
MOTADATA_NEO4J_PASSWORD="${MOTADATA_NEO4J_PASSWORD:-}"
RSYNC_DELETE="${RSYNC_DELETE:-1}"
REMOTE_REFRESH="${REMOTE_REFRESH:-0}"
RSYNC_RSH="${RSYNC_RSH:-ssh}"
SSH_OPTS="${SSH_OPTS:-}"

usage() {
  echo "Usage: MOTADATA_REPO_ROOT=... GPU_SYNC_HOST=user@host GPU_MIRROR_ROOT=/remote/path $0" >&2
  echo "Optional: MCODER_REMOTE_ROOT REMOTE_REFRESH=1 RSYNC_DELETE=0 RSYNC_RSH='ssh -i key'" >&2
  exit 1
}

[[ -n "${MOTADATA_REPO_ROOT}" ]] || usage
[[ -n "${GPU_SYNC_HOST}" ]] || usage
[[ -n "${GPU_MIRROR_ROOT}" ]] || usage

if [[ ! -d "${MOTADATA_REPO_ROOT}" ]]; then
  echo "error: MOTADATA_REPO_ROOT is not a directory: ${MOTADATA_REPO_ROOT}" >&2
  exit 1
fi

DELETE_ARGS=()
if [[ "${RSYNC_DELETE}" == "1" ]]; then
  DELETE_ARGS+=(--delete)
fi

RSYNC_SRC="${MOTADATA_REPO_ROOT%/}/"
RSYNC_DST="${GPU_SYNC_HOST}:${GPU_MIRROR_ROOT}/"

RSYNC_E="${RSYNC_RSH}"
[[ -n "${SSH_OPTS}" ]] && RSYNC_E="${RSYNC_E} ${SSH_OPTS}"

echo "rsync -> ${RSYNC_DST} (delete=${RSYNC_DELETE})"

# shellcheck disable=SC2086
rsync -az "${DELETE_ARGS[@]}" -e "${RSYNC_E}" \
  --exclude '.git/' \
  --exclude '**/target/' \
  --exclude '**/build/' \
  --exclude '**/.idea/' \
  --exclude '**/.gradle/' \
  "${RSYNC_SRC}" "${RSYNC_DST}"

GIT_COMMIT="unknown"
if command -v git >/dev/null 2>&1 && git -C "${MOTADATA_REPO_ROOT}" rev-parse HEAD >/dev/null 2>&1; then
  GIT_COMMIT="$(git -C "${MOTADATA_REPO_ROOT}" rev-parse HEAD)"
fi
SYNCED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
SRC_HOST="$(hostname -s 2>/dev/null || hostname)"

export GIT_COMMIT SYNCED_AT SRC_HOST GPU_MIRROR_ROOT
SNAPSHOT_JSON="$(python3 - <<'PY'
import json, os
print(json.dumps({
    "schema": "motadata_mirror_snapshot.v1",
    "git_commit": os.environ.get("GIT_COMMIT", "unknown"),
    "synced_at_utc": os.environ["SYNCED_AT"],
    "source_host": os.environ.get("SRC_HOST", "unknown"),
    "mirror_root": os.environ["GPU_MIRROR_ROOT"],
}, indent=2))
PY
)"

REMOTE_SNAP="${GPU_MIRROR_ROOT}/motadata_snapshot.json"
# shellcheck disable=SC2086
ssh ${SSH_OPTS} "${GPU_SYNC_HOST}" \
  "mkdir -p $(printf '%q' "${GPU_MIRROR_ROOT}") && cat > $(printf '%q' "${REMOTE_SNAP}")" \
  <<<"${SNAPSHOT_JSON}"

echo "wrote remote ${REMOTE_SNAP} (commit=${GIT_COMMIT})"

if [[ "${REMOTE_REFRESH}" == "1" ]]; then
  if [[ -z "${MCODER_REMOTE_ROOT}" ]]; then
    echo "error: set MCODER_REMOTE_ROOT when REMOTE_REFRESH=1 (absolute path to m-coder on GPU)" >&2
    exit 1
  fi
  if [[ -z "${MOTADATA_NEO4J_PASSWORD}" ]]; then
    echo "error: set MOTADATA_NEO4J_PASSWORD when REMOTE_REFRESH=1 (GPU cannot prompt; Neo4j auth required)" >&2
    exit 1
  fi
  REMOTE_STACK="${MCODER_REMOTE_ROOT%/}/runtime/scripts/neo4j_ask_stack.py"
  # Use absolute script path so a failed cd / wrong cwd cannot run python3 from \$HOME/runtime/scripts/...
  # Forward MOTADATA_NEO4J_PASSWORD so neo4j_ask_stack refresh works non-interactively over SSH.
  REMOTE_REFRESH_CMD="$(
    printf \
      'set -euo pipefail; export MOTADATA_NEO4J_PASSWORD=%q; STACK=%q; ROOT=%q; MIR=%q; test -f "$STACK" || { echo "error: missing on GPU (fix MCODER_REMOTE_ROOT): $STACK" >&2; exit 1; }; test -d "$ROOT" || { echo "error: not a directory on GPU: $ROOT" >&2; exit 1; }; exec python3 "$STACK" --workspace-root "$MIR" refresh' \
      "${MOTADATA_NEO4J_PASSWORD}" "${REMOTE_STACK}" "${MCODER_REMOTE_ROOT}" "${GPU_MIRROR_ROOT}"
  )"
  # shellcheck disable=SC2086
  ssh ${SSH_OPTS} "${GPU_SYNC_HOST}" bash -c "${REMOTE_REFRESH_CMD}"
fi

echo "sync_motadata_mirror_to_gpu: ok"
