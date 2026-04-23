#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STACK_DIR="$REPO_ROOT/docker/neo4j-graph"
COMPOSE_FILE="$STACK_DIR/docker-compose.yml"
ENV_FILE="$STACK_DIR/.env"

compose_cmd() {
  if command -v docker-compose >/dev/null 2>&1; then
    printf 'docker-compose'
    return 0
  fi
  if docker compose version >/dev/null 2>&1; then
    printf 'docker compose'
    return 0
  fi
  echo "Neither docker-compose nor docker compose is available." >&2
  exit 1
}

compose() {
  local cmd
  cmd="$(compose_cmd)"
  if [[ "$cmd" == "docker-compose" ]]; then
    docker-compose -f "$COMPOSE_FILE" "$@"
    return 0
  fi
  docker compose -f "$COMPOSE_FILE" "$@"
}

ensure_env() {
  if [[ ! -f "$ENV_FILE" && -f "$STACK_DIR/.env.example" ]]; then
    cp "$STACK_DIR/.env.example" "$ENV_FILE"
    echo "Created $ENV_FILE from example; adjust GRAPH_MOTADATA_ROOT if needed."
  fi
}

cmd_up() {
  ensure_env
  compose up -d neo4j graph-refresh
}

cmd_refresh() {
  ensure_env
  compose run --rm graph-refresh bash /workspace/docker/neo4j-graph/run_refresh_once.sh
}

cmd_status() {
  ensure_env
  compose ps
}

cmd_logs() {
  ensure_env
  compose logs --tail=100 "$@"
}

cmd_down() {
  ensure_env
  compose down
}

case "${1:-}" in
  up) shift; cmd_up "$@" ;;
  refresh) shift; cmd_refresh "$@" ;;
  status) shift; cmd_status "$@" ;;
  logs) shift; cmd_logs "$@" ;;
  down) shift; cmd_down "$@" ;;
  *)
    echo "Usage: $0 {up|refresh|status|logs|down}" >&2
    exit 1
    ;;
esac