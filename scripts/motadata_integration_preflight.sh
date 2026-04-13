#!/usr/bin/env bash
# Motadata + m-coder integration: by default SETS UP the local stack (optional SSH tunnel +
# Context Layer via wsl_plugin_mvp_stack.sh up), then prints configuration, a checklist,
# deep validation (check), and optional Ask E2E.
#
# Exit 0 only when checks pass (GREEN). Non-zero on failure (RED).
#
# Usage:
#   ./scripts/motadata_integration_preflight.sh              # setup + verify (needs MOTADATA_ROOT)
#   ./scripts/motadata_integration_preflight.sh --verify-only  # no setup; probe existing services
#   ./scripts/motadata_integration_preflight.sh --quick-only   # fast probes only; no setup, no deep check
#
# Logs: runtime/.run/motadata_preflight_<UTC>.log (tee to stdout)
#
# Environment (inherits wsl_plugin_mvp_stack.sh):
#   MOTADATA_ROOT / MOTADATA_REPO_ROOT  Workspace root for Context Layer (required for default setup)
#   M_CODER_REPO_ROOT     Optional; defaults to parent of scripts/
#   CONTEXT_URL           Default http://127.0.0.1:8091
#   PLAN_GATE_URL         Default http://127.0.0.1:8089
#   VLLM_URL                Optional override; default http://127.0.0.1:${LOCAL_VLLM_PORT}
#   LOCAL_VLLM_PORT         Default 8000; set 0 to skip local vLLM probe
#   ENABLE_SSH_TUNNEL, TUNNEL_TARGET, TUNNEL_USER, TUNNEL_HOST, ...
#   ALLOW_COMMIT_MISMATCH
#   PREFLIGHT_NO_SETUP=1    Same as --verify-only (skip wsl_plugin_mvp_stack.sh up)
#   PREFLIGHT_CONTINUE_ON_QUICK_FAIL  Set to 1 to run deep check even if quick probes fail
#   VERIFY_ASK_E2E, WORKSPACE_ROOT, PREFLIGHT_ASK_QUERY
#
set -euo pipefail

VERIFY_ONLY=0
QUICK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --verify-only|--no-setup) VERIFY_ONLY=1 ;;
    --quick-only) QUICK_ONLY=1 ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Usage: $0 [--verify-only|--no-setup] [--quick-only]" >&2
      exit 1
      ;;
  esac
done
[[ "${PREFLIGHT_NO_SETUP:-0}" == "1" ]] && VERIFY_ONLY=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${M_CODER_REPO_ROOT:-$SCRIPT_DIR/..}" && pwd)"
export M_CODER_REPO_ROOT="$REPO_ROOT"

RUN_DIR="$REPO_ROOT/runtime/.run"
mkdir -p "$RUN_DIR"
CONTEXT_PID_FILE="$RUN_DIR/wsl_context_layer.pid"
TUNNEL_PID_FILE="$RUN_DIR/wsl_plan_gate_tunnel.pid"
CONTEXT_LOG="$RUN_DIR/wsl_context_layer.log"
TUNNEL_LOG="$RUN_DIR/wsl_plan_gate_tunnel.log"
CONTEXT_META_FILE="$RUN_DIR/wsl_context_layer.meta"

CONTEXT_URL="${CONTEXT_URL:-http://127.0.0.1:8091}"
PLAN_GATE_URL="${PLAN_GATE_URL:-http://127.0.0.1:8089}"
MOTADATA_ROOT="${MOTADATA_ROOT:-${MOTADATA_REPO_ROOT:-}}"
export MOTADATA_ROOT

ENABLE_SSH_TUNNEL="${ENABLE_SSH_TUNNEL:-0}"
TUNNEL_USER="${TUNNEL_USER:-}"
TUNNEL_HOST="${TUNNEL_HOST:-}"
TUNNEL_TARGET="${TUNNEL_TARGET:-}"
TUNNEL_SSH_KEY="${TUNNEL_SSH_KEY:-}"
LOCAL_PLAN_GATE_PORT="${LOCAL_PLAN_GATE_PORT:-}"
REMOTE_PLAN_GATE_HOST="${REMOTE_PLAN_GATE_HOST:-127.0.0.1}"
REMOTE_PLAN_GATE_PORT="${REMOTE_PLAN_GATE_PORT:-8089}"
LOCAL_VLLM_PORT="${LOCAL_VLLM_PORT:-8000}"
REMOTE_VLLM_HOST="${REMOTE_VLLM_HOST:-127.0.0.1}"
REMOTE_VLLM_PORT="${REMOTE_VLLM_PORT:-8000}"

if [[ -z "$LOCAL_PLAN_GATE_PORT" ]]; then
  LOCAL_PLAN_GATE_PORT="$(python3 - "$PLAN_GATE_URL" <<'PY'
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1])
port = u.port
if port is None:
    port = 443 if u.scheme == "https" else 80
print(port)
PY
)"
fi

VLLM_URL="${VLLM_URL:-http://127.0.0.1:${LOCAL_VLLM_PORT}}"

LOG_FILE="$RUN_DIR/motadata_preflight_$(date -u +%Y%m%dT%H%M%SZ).log"
touch "$LOG_FILE"

# shellcheck disable=SC2094
exec > >(tee -a "$LOG_FILE") 2>&1

_pf_mktemp() {
  mktemp "$RUN_DIR/preflight_XXXXXX"
}

read_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    cat "$pid_file"
  fi
}

is_pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

build_tunnel_target_display() {
  if [[ -n "$TUNNEL_TARGET" ]]; then
    echo "$TUNNEL_TARGET"
    return
  fi
  if [[ -n "$TUNNEL_USER" && -n "$TUNNEL_HOST" ]]; then
    echo "${TUNNEL_USER}@${TUNNEL_HOST}"
    return
  fi
  echo "<not set>"
}

QUICK_FAILED=0

row_pass() { echo "[PASS] $*"; }
row_fail() { echo "[FAIL] $*"; QUICK_FAILED=1; }
row_skip() { echo "[SKIP] $*"; }
row_warn() { echo "[WARN] $*"; }
row_info() { echo "[INFO] $*"; }

print_banner() {
  echo "═══════════════════════════════════════════════════════════════════"
  echo " Motadata integration — setup + preflight (m-coder)"
  echo "═══════════════════════════════════════════════════════════════════"
  echo "  Log file: $LOG_FILE"
  if [[ "$QUICK_ONLY" == "1" ]]; then
    echo "  Mode: --quick-only (no setup, no deep check)"
  elif [[ "$VERIFY_ONLY" == "1" ]]; then
    echo "  Mode: --verify-only (no setup)"
  else
    echo "  Mode: default (wsl_plugin_mvp_stack.sh up, then checklist + deep validation)"
  fi
  echo ""
}

print_config_section() {
  echo "───────────────────────────────────────────────────────────────────"
  echo " 1) Effective configuration"
  echo "───────────────────────────────────────────────────────────────────"
  echo "  Repository"
  echo "    M_CODER_REPO_ROOT=$REPO_ROOT"
  if command -v git >/dev/null 2>&1 && git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "    git branch:     $(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")"
    echo "    git HEAD:       $(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "?")"
  else
    echo "    git:            (not a git repo or git unavailable)"
  fi
  echo ""
  echo "  URLs & ports (plugin / IDE should match these hosts)"
  echo "    CONTEXT_URL=$CONTEXT_URL"
  echo "    PLAN_GATE_URL=$PLAN_GATE_URL"
  echo "    VLLM_URL (probe)=${VLLM_URL}   (derived from LOCAL_VLLM_PORT=$LOCAL_VLLM_PORT unless VLLM_URL set)"
  echo ""
  echo "  Workspace (Context Layer exports / Ask E2E)"
  echo "    MOTADATA_ROOT=${MOTADATA_ROOT:-<unset>}"
  if [[ -n "${MOTADATA_REPO_ROOT:-}" && "$MOTADATA_REPO_ROOT" != "${MOTADATA_ROOT:-}" ]]; then
    echo "    MOTADATA_REPO_ROOT=$MOTADATA_REPO_ROOT (also set; should match MOTADATA_ROOT)"
  fi
  echo ""
  echo "  SSH tunnel (optional — forwards Plan-Gate + optionally vLLM to localhost)"
  echo "    ENABLE_SSH_TUNNEL=$ENABLE_SSH_TUNNEL"
  echo "    TUNNEL_TARGET / user@host: $(build_tunnel_target_display)"
  echo "    TUNNEL_SSH_KEY=${TUNNEL_SSH_KEY:-<unset>}"
  echo "    LOCAL_PLAN_GATE_PORT=$LOCAL_PLAN_GATE_PORT  (→ ${REMOTE_PLAN_GATE_HOST}:${REMOTE_PLAN_GATE_PORT})"
  echo "    LOCAL_VLLM_PORT=$LOCAL_VLLM_PORT  (→ ${REMOTE_VLLM_HOST}:${REMOTE_VLLM_PORT}; 0 = no vLLM forward)"
  echo "    PID file (tunnel): $TUNNEL_PID_FILE"
  echo "    Tunnel log:        $TUNNEL_LOG"
  echo ""
  echo "  Managed processes (when using wsl_plugin_mvp_stack.sh up)"
  echo "    Context PID file:  $CONTEXT_PID_FILE"
  echo "    Context log:       $CONTEXT_LOG"
  echo "    Context meta:      $CONTEXT_META_FILE"
  echo ""
  echo "  Validation flags"
  echo "    ALLOW_COMMIT_MISMATCH=${ALLOW_COMMIT_MISMATCH:-0}"
  echo "    VERIFY_ASK_E2E=${VERIFY_ASK_E2E:-0}"
  echo ""
  echo "  JetBrains plugin env (set in IDE or env)"
  echo "    MOTADATA_PLAN_GATE_URL=$PLAN_GATE_URL"
  echo "    MOTADATA_CONTEXT_LAYER_URL=$CONTEXT_URL"
  echo ""
}

run_setup_if_enabled() {
  if [[ "$QUICK_ONLY" == "1" ]]; then
    row_info "Setup skipped (--quick-only: no wsl_plugin_mvp_stack.sh up)"
    echo ""
    return 0
  fi
  if [[ "$VERIFY_ONLY" == "1" ]]; then
    row_info "Setup skipped (--verify-only / PREFLIGHT_NO_SETUP=1: only probing existing services)"
    echo ""
    return 0
  fi
  if [[ -z "$MOTADATA_ROOT" ]]; then
    echo "[FAIL] Default run performs setup (managed stack: tunnel if enabled + Context Layer)." >&2
    echo "       Export MOTADATA_ROOT or MOTADATA_REPO_ROOT to your Motadata workspace path on this host," >&2
    echo "       or use --verify-only if Plan-Gate + Context Layer are already running." >&2
    exit 1
  fi
  if [[ ! -d "$MOTADATA_ROOT" ]]; then
    echo "[FAIL] MOTADATA_ROOT is not a directory: $MOTADATA_ROOT" >&2
    exit 1
  fi
  export MOTADATA_ROOT
  echo "───────────────────────────────────────────────────────────────────"
  echo " 0) Setup — managed stack (tunnel if enabled + Context Layer + built-in checks)"
  echo "───────────────────────────────────────────────────────────────────"
  echo "  Running: scripts/wsl_plugin_mvp_stack.sh up"
  echo ""
  bash "$REPO_ROOT/scripts/wsl_plugin_mvp_stack.sh" up
  echo ""
}

checklist_tools() {
  echo "───────────────────────────────────────────────────────────────────"
  echo " 2) Checklist — prerequisites (CLI)"
  echo "───────────────────────────────────────────────────────────────────"
  for c in curl python3 git; do
    if command -v "$c" >/dev/null 2>&1; then
      row_pass "Found: $c ($({ command -v "$c"; }))"
    else
      row_fail "Missing command: $c"
    fi
  done
  echo ""
}

checklist_ssh_tunnel() {
  echo "───────────────────────────────────────────────────────────────────"
  echo " 3) Checklist — SSH tunnel"
  echo "───────────────────────────────────────────────────────────────────"
  if [[ "$ENABLE_SSH_TUNNEL" != "1" ]]; then
    row_skip "SSH tunnel not requested (ENABLE_SSH_TUNNEL=$ENABLE_SSH_TUNNEL). Plan-Gate/vLLM must be reachable at CONTEXT_URL/PLAN_GATE_URL/VLLM_URL as configured."
    echo ""
    return 0
  fi

  local tpid
  tpid="$(read_pid "$TUNNEL_PID_FILE" || true)"
  if [[ -n "$tpid" ]] && is_pid_alive "$tpid"; then
    row_pass "SSH tunnel process alive (PID $tpid, managed by this repo’s launcher). Log: $TUNNEL_LOG"
  else
    row_fail "SSH tunnel expected (ENABLE_SSH_TUNNEL=1) but no live PID in $TUNNEL_PID_FILE (start with: ./scripts/wsl_plugin_mvp_stack.sh up)"
  fi
  echo ""
}

checklist_context_layer() {
  echo "───────────────────────────────────────────────────────────────────"
  echo " 4) Checklist — Context Layer"
  echo "───────────────────────────────────────────────────────────────────"

  local cpid
  cpid="$(read_pid "$CONTEXT_PID_FILE" || true)"
  if [[ -n "$cpid" ]] && is_pid_alive "$cpid"; then
    row_info "Managed Context Layer PID $cpid (from $CONTEXT_PID_FILE)"
  else
    row_info "No managed Context Layer PID (or not started via wsl_plugin_mvp_stack.sh); still probing $CONTEXT_URL"
  fi

  local code body out err
  out="$(_pf_mktemp)"
  err="$(_pf_mktemp)"
  code="$(curl -sS -o "$out" -w "%{http_code}" --max-time 8 "$CONTEXT_URL/healthz" 2>"$err" || true)"
  if [[ "$code" == "200" ]]; then
    body="$(head -c 200 "$out" 2>/dev/null | tr '\n' ' ')"
    row_pass "Context Layer healthz — HTTP $code — $body"
  else
    row_fail "Context Layer healthz — HTTP ${code:-<none>} (URL $CONTEXT_URL/healthz)"
    if [[ -s "$err" ]]; then
      row_info "curl stderr: $(head -c 300 "$err" | tr '\n' ' ')"
    fi
  fi
  rm -f "$out" "$err"

  local ver
  if ver="$(curl -fsS --max-time 10 "$CONTEXT_URL/version" 2>/dev/null)"; then
    row_pass "Context Layer /version — $(echo "$ver" | head -c 400 | tr '\n' ' ')"
  else
    row_fail "Context Layer /version unreachable ($CONTEXT_URL/version)"
  fi
  echo ""
}

checklist_plan_gate() {
  echo "───────────────────────────────────────────────────────────────────"
  echo " 5) Checklist — Plan-Gate"
  echo "───────────────────────────────────────────────────────────────────"

  local code body out err
  out="$(_pf_mktemp)"
  err="$(_pf_mktemp)"
  code="$(curl -sS -o "$out" -w "%{http_code}" --max-time 8 "$PLAN_GATE_URL/healthz" 2>"$err" || true)"
  if [[ "$code" == "200" ]]; then
    body="$(head -c 200 "$out" 2>/dev/null | tr '\n' ' ')"
    row_pass "Plan-Gate healthz — HTTP $code — $body"
  else
    row_fail "Plan-Gate healthz — HTTP ${code:-<none>} (URL $PLAN_GATE_URL/healthz)"
    if [[ -s "$err" ]]; then
      row_info "curl stderr: $(head -c 300 "$err" | tr '\n' ' ')"
    fi
  fi
  rm -f "$out" "$err"

  local ver
  if ver="$(curl -fsS --max-time 10 "$PLAN_GATE_URL/version" 2>/dev/null)"; then
    row_pass "Plan-Gate /version — $(echo "$ver" | head -c 500 | tr '\n' ' ')"
  else
    row_fail "Plan-Gate /version unreachable ($PLAN_GATE_URL/version)"
  fi
  echo ""
}

checklist_vllm() {
  echo "───────────────────────────────────────────────────────────────────"
  echo " 6) Checklist — vLLM (OpenAI-compatible HTTP)"
  echo "───────────────────────────────────────────────────────────────────"
  if [[ "$LOCAL_VLLM_PORT" == "0" ]]; then
    row_skip "LOCAL_VLLM_PORT=0 — no local vLLM forward expected. Plan-Gate may still reach vLLM on the GPU host; this script does not probe remote vLLM."
    echo ""
    return 0
  fi

  local models_url="${VLLM_URL%/}/v1/models"
  local code out err
  out="$(_pf_mktemp)"
  err="$(_pf_mktemp)"
  code="$(curl -sS -o "$out" -w "%{http_code}" --max-time 12 "$models_url" 2>"$err" || true)"
  if [[ "$code" == "200" ]]; then
    row_pass "vLLM GET /v1/models — HTTP $code — $(head -c 180 "$out" | tr '\n' ' ')…"
  else
    row_fail "vLLM GET /v1/models — HTTP ${code:-<none>} ($models_url)"
    if [[ -s "$err" ]]; then
      row_info "curl stderr: $(head -c 300 "$err" | tr '\n' ' ')"
    fi
  fi
  rm -f "$out" "$err"
  echo ""
}

run_deep_validation() {
  echo "───────────────────────────────────────────────────────────────────"
  echo " 7) Deep validation (strict waits, git commit parity, route probes)"
  echo "───────────────────────────────────────────────────────────────────"
  echo "  Running: scripts/wsl_plugin_mvp_stack.sh check"
  echo ""
  bash "$REPO_ROOT/scripts/wsl_plugin_mvp_stack.sh" check
  echo ""
}

run_ask_e2e_optional() {
  if [[ "${VERIFY_ASK_E2E:-0}" != "1" ]]; then
    return 0
  fi
  local wr="${MOTADATA_ROOT:-${WORKSPACE_ROOT:-}}"
  if [[ -z "$wr" ]]; then
    echo "[FAIL] VERIFY_ASK_E2E=1 requires MOTADATA_ROOT or WORKSPACE_ROOT" >&2
    exit 1
  fi
  if [[ ! -d "$wr" ]]; then
    echo "[FAIL] Workspace path does not exist: $wr" >&2
    exit 1
  fi
  export WORKSPACE_ROOT="$wr"
  export QUERY="${PREFLIGHT_ASK_QUERY:-Smoke: list top-level modules in this workspace.}"
  echo "───────────────────────────────────────────────────────────────────"
  echo " 8) Optional Ask E2E (export_evidence + /v1/ask)"
  echo "───────────────────────────────────────────────────────────────────"
  bash "$REPO_ROOT/runtime/scripts/verify_ask_path.sh"
  echo ""
}

print_summary_green() {
  echo "═══════════════════════════════════════════════════════════════════"
  echo " GREEN — setup (if run) + preflight passed"
  echo "═══════════════════════════════════════════════════════════════════"
  echo "  Safe to run JetBrains UI: Motadata → Ask / Explain / Plan, Submit to Runtime."
  echo "  Plugin URLs: MOTADATA_PLAN_GATE_URL=$PLAN_GATE_URL  MOTADATA_CONTEXT_LAYER_URL=$CONTEXT_URL"
  echo "  Full log: $LOG_FILE"
  echo ""
}

main() {
  print_banner
  print_config_section
  run_setup_if_enabled
  checklist_tools
  checklist_ssh_tunnel
  checklist_context_layer
  checklist_plan_gate
  checklist_vllm

  if [[ "${QUICK_FAILED:-0}" -ne 0 && "${PREFLIGHT_CONTINUE_ON_QUICK_FAIL:-0}" != "1" ]]; then
    echo "═══════════════════════════════════════════════════════════════════"
    echo " RED — quick checklist failed (see [FAIL] lines above)."
    echo " Fix connectivity, or run: ./scripts/motadata_integration_preflight.sh (setup + verify)"
    echo " To run deep checks anyway: PREFLIGHT_CONTINUE_ON_QUICK_FAIL=1 $0"
    echo " Log: $LOG_FILE"
    echo "═══════════════════════════════════════════════════════════════════"
    exit 1
  fi

  if [[ "$QUICK_ONLY" == "1" ]]; then
    if [[ "$QUICK_FAILED" -ne 0 ]]; then
      exit 1
    fi
    echo " (--quick-only: skipping wsl_plugin_mvp_stack.sh check)"
    print_summary_green
    exit 0
  fi

  run_deep_validation

  run_ask_e2e_optional

  print_summary_green
}

main
