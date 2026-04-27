#!/usr/bin/env bash
#
# Production-grade WSL bootstrap orchestrator for m-coder + Motadata validation.
# Runs end-to-end:
#   1) Validate environment and required tools
#   2) Check current git branch
#   3) Pull latest m-coder branch
#   4) Start/restart MVP stack (Context Layer + optional tunnel)
#   5) Run integration preflight verification
#   6) Build authority code index for Motadata workspace
#
# Usage:
#   bash scripts/mcoder_wsl_e2e_bootstrap.sh \
#     --repo-root /root/Harshil-PoCs/m-coder \
#     --motadata-root /root/Harshil-PoCs/Motadata \
#     --branch mcoder-cli-ux-contract-v1-audit \
#     --verbose
#
# Defaults:
#   --repo-root: auto-detected from this script location
#   --motadata-root: from MOTADATA_ROOT or MOTADATA_REPO_ROOT env
#   --branch: current checked-out branch
#   pull strategy: --ff-only
#
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
DEFAULT_REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

REPO_ROOT="$DEFAULT_REPO_ROOT"
MOTADATA_ROOT="${MOTADATA_ROOT:-${MOTADATA_REPO_ROOT:-}}"
EXPECTED_BRANCH=""
PULL_STRATEGY="ff-only"  # ff-only | rebase | merge
ALLOW_DIRTY=0
SKIP_PULL=0
SKIP_STACK_UP=0
SKIP_PREFLIGHT=0
SKIP_AUTHORITY_INDEX=0
DRY_RUN=0
VERBOSE=0
FORCE_RESTART_STACK=1

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE=""
STEP_NO=0

usage() {
  cat <<'EOF'
Usage: scripts/mcoder_wsl_e2e_bootstrap.sh [options]

Options:
  --repo-root <path>          m-coder repo root (default: auto-detected)
  --motadata-root <path>      Motadata workspace root (required unless env provided)
  --branch <name>             Expected git branch (default: current branch)
  --pull-strategy <mode>      ff-only | rebase | merge (default: ff-only)
  --allow-dirty               Allow pull even when working tree is dirty
  --skip-pull                 Skip git fetch/pull
  --skip-stack-up             Skip stack start/restart
  --skip-preflight            Skip integration preflight verification
  --skip-authority-index      Skip authority code index build
  --no-force-restart          Use stack up (not restart) when bringing stack up
  --dry-run                   Print commands without executing
  --verbose                   Enable shell trace output
  --help                      Show this help

Environment:
  MOTADATA_ROOT / MOTADATA_REPO_ROOT
  CONTEXT_URL, PLAN_GATE_URL, ENABLE_SSH_TUNNEL, TUNNEL_TARGET, ...
  (passed through to the underlying stack/preflight scripts)
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo-root) REPO_ROOT="${2:-}"; shift 2 ;;
      --motadata-root) MOTADATA_ROOT="${2:-}"; shift 2 ;;
      --branch) EXPECTED_BRANCH="${2:-}"; shift 2 ;;
      --pull-strategy) PULL_STRATEGY="${2:-}"; shift 2 ;;
      --allow-dirty) ALLOW_DIRTY=1; shift ;;
      --skip-pull) SKIP_PULL=1; shift ;;
      --skip-stack-up) SKIP_STACK_UP=1; shift ;;
      --skip-preflight) SKIP_PREFLIGHT=1; shift ;;
      --skip-authority-index) SKIP_AUTHORITY_INDEX=1; shift ;;
      --no-force-restart) FORCE_RESTART_STACK=0; shift ;;
      --dry-run) DRY_RUN=1; shift ;;
      --verbose) VERBOSE=1; shift ;;
      --help|-h) usage; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
    esac
  done
}

init_logging() {
  mkdir -p "$REPO_ROOT/runtime/.run"
  LOG_FILE="$REPO_ROOT/runtime/.run/mcoder_wsl_e2e_bootstrap_${RUN_ID}.log"
  touch "$LOG_FILE"
  # shellcheck disable=SC2094
  exec > >(tee -a "$LOG_FILE") 2>&1
  if [[ "$VERBOSE" -eq 1 ]]; then
    set -x
  fi
}

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
info() { echo "[$(ts)] [INFO] $*"; }
ok() { echo "[$(ts)] [OK]   $*"; }
warn() { echo "[$(ts)] [WARN] $*"; }
fail() { echo "[$(ts)] [FAIL] $*" >&2; exit 1; }

step() {
  STEP_NO=$((STEP_NO + 1))
  echo ""
  echo "================================================================================"
  echo "STEP ${STEP_NO}: $*"
  echo "================================================================================"
}

run_cmd() {
  local cmd="$*"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DRY-RUN] $cmd"
    return 0
  fi
  eval "$cmd"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

validate_inputs() {
  step "Validate inputs and prerequisites"
  require_cmd git
  require_cmd bash
  require_cmd curl
  require_cmd python3

  [[ -d "$REPO_ROOT" ]] || fail "repo root does not exist: $REPO_ROOT"
  git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a git repo: $REPO_ROOT"

  if [[ -z "$MOTADATA_ROOT" ]]; then
    fail "motadata root is required (use --motadata-root or MOTADATA_ROOT env)"
  fi
  [[ -d "$MOTADATA_ROOT" ]] || fail "motadata root does not exist: $MOTADATA_ROOT"

  case "$PULL_STRATEGY" in
    ff-only|rebase|merge) ;;
    *) fail "invalid --pull-strategy '$PULL_STRATEGY' (use ff-only|rebase|merge)" ;;
  esac

  ok "Inputs validated"
}

check_branch() {
  step "Check current git branch"
  local current_branch
  current_branch="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
  local head_sha
  head_sha="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
  info "Current branch: $current_branch"
  info "Current commit: $head_sha"

  if [[ -n "$EXPECTED_BRANCH" && "$current_branch" != "$EXPECTED_BRANCH" ]]; then
    fail "current branch '$current_branch' != expected '$EXPECTED_BRANCH'"
  fi
  if [[ -z "$EXPECTED_BRANCH" ]]; then
    EXPECTED_BRANCH="$current_branch"
  fi
  ok "Branch check passed ($EXPECTED_BRANCH)"
}

check_clean_tree_if_needed() {
  step "Check git working tree state"
  local porcelain
  porcelain="$(git -C "$REPO_ROOT" status --porcelain)"
  if [[ -n "$porcelain" ]]; then
    if [[ "$ALLOW_DIRTY" -eq 1 ]]; then
      warn "Working tree is dirty; continuing because --allow-dirty is set"
    else
      fail "working tree is dirty; commit/stash first or rerun with --allow-dirty"
    fi
  else
    ok "Working tree is clean"
  fi
}

pull_branch() {
  [[ "$SKIP_PULL" -eq 1 ]] && { warn "Skipping pull (--skip-pull)"; return 0; }

  step "Fetch and pull latest branch state"
  run_cmd "git -C \"$REPO_ROOT\" fetch --prune origin"
  run_cmd "git -C \"$REPO_ROOT\" checkout \"$EXPECTED_BRANCH\""

  case "$PULL_STRATEGY" in
    ff-only) run_cmd "git -C \"$REPO_ROOT\" pull --ff-only origin \"$EXPECTED_BRANCH\"" ;;
    rebase) run_cmd "git -C \"$REPO_ROOT\" pull --rebase origin \"$EXPECTED_BRANCH\"" ;;
    merge) run_cmd "git -C \"$REPO_ROOT\" pull origin \"$EXPECTED_BRANCH\"" ;;
  esac

  local post_sha
  post_sha="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
  ok "Pull complete at commit $post_sha"
}

bring_up_stack() {
  [[ "$SKIP_STACK_UP" -eq 1 ]] && { warn "Skipping stack start (--skip-stack-up)"; return 0; }

  step "Start/restart MVP stack (context + tunnel + compatibility checks)"
  export M_CODER_REPO_ROOT="$REPO_ROOT"
  export MOTADATA_ROOT
  local stack_cmd="up"
  if [[ "$FORCE_RESTART_STACK" -eq 1 ]]; then
    stack_cmd="restart"
  fi
  run_cmd "bash \"$REPO_ROOT/scripts/wsl_plugin_mvp_stack.sh\" \"$stack_cmd\""
  ok "Stack command succeeded: $stack_cmd"
}

run_preflight() {
  [[ "$SKIP_PREFLIGHT" -eq 1 ]] && { warn "Skipping preflight (--skip-preflight)"; return 0; }

  step "Run integration preflight verification"
  export M_CODER_REPO_ROOT="$REPO_ROOT"
  export MOTADATA_ROOT
  run_cmd "bash \"$REPO_ROOT/scripts/motadata_integration_preflight.sh\" --verify-only"
  ok "Integration preflight passed"
}

build_authority_index() {
  [[ "$SKIP_AUTHORITY_INDEX" -eq 1 ]] && { warn "Skipping authority index build (--skip-authority-index)"; return 0; }

  step "Build authority code index for Motadata workspace"
  run_cmd "PYTHONPATH=\"$REPO_ROOT\" python3 \"$REPO_ROOT/runtime/scripts/build_authority_code_index.py\" --workspace-root \"$MOTADATA_ROOT\""
  ok "Authority code index build completed"
}

print_summary() {
  echo ""
  echo "################################################################################"
  echo "# Bootstrap completed successfully"
  echo "################################################################################"
  echo "repo_root:       $REPO_ROOT"
  echo "motadata_root:   $MOTADATA_ROOT"
  echo "branch:          $EXPECTED_BRANCH"
  echo "pull_strategy:   $PULL_STRATEGY"
  echo "log_file:        $LOG_FILE"
  echo ""
}

main() {
  parse_args "$@"
  init_logging
  info "Starting mcoder WSL end-to-end bootstrap"
  validate_inputs
  check_branch
  check_clean_tree_if_needed
  pull_branch
  bring_up_stack
  run_preflight
  build_authority_index
  print_summary
}

main "$@"
