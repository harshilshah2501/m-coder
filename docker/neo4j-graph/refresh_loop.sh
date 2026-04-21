#!/usr/bin/env bash
set -euo pipefail

JAVA_ROOT="${MOTADATA_JAVA_ROOT:?MOTADATA_JAVA_ROOT is required}"
STATE_FILE="${GRAPH_STATE_FILE:-/state/java_graph_state.env}"
INTERVAL_SEC="${GRAPH_REFRESH_INTERVAL_SEC:-900}"
FORCE_RESET="${GRAPH_REFRESH_FORCE_RESET:-1}"

mkdir -p "$(dirname "$STATE_FILE")"

log() {
  printf '[graph-refresh] %s\n' "$*"
}

compute_fingerprint() {
  find "$JAVA_ROOT" -type f -name '*.java' ! -path '*/target/*' -printf '%P|%s|%T@\n' \
    | LC_ALL=C sort \
    | sha256sum \
    | awk '{print $1}'
}

load_state() {
  if [[ -f "$STATE_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$STATE_FILE"
  fi
}

save_state() {
  cat > "$STATE_FILE" <<EOF
LAST_SUCCESS_FINGERPRINT=$1
LAST_SUCCESS_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
}

run_ingest() {
  local args=()
  if [[ "$FORCE_RESET" == "1" ]]; then
    args+=(--reset)
  fi
  python /workspace/tools/ast_indexer/ingest_java_graph.py \
    --java-root "$JAVA_ROOT" \
    --log-level INFO \
    "${args[@]}"
}

wait_for_java_root() {
  while [[ ! -d "$JAVA_ROOT" ]]; do
    log "waiting for Java root: $JAVA_ROOT"
    sleep 5
  done
}

main() {
  wait_for_java_root
  while true; do
    load_state
    current_fingerprint="$(compute_fingerprint)"
    if [[ "${LAST_SUCCESS_FINGERPRINT:-}" != "$current_fingerprint" ]]; then
      log "change detected; refreshing graph"
      run_ingest
      save_state "$current_fingerprint"
      log "refresh complete"
    else
      log "no source change detected; graph is current"
    fi
    sleep "$INTERVAL_SEC"
  done
}

main "$@"