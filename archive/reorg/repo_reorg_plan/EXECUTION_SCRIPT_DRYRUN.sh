#!/usr/bin/env bash
# EXECUTION_SCRIPT_DRYRUN.sh
# Prints commands that WOULD run. Executes ONLY if EXECUTE=1 in repo_reorg_plan/config.
# Source: repo_reorg_plan/MOVESET_PLAN.jsonl, config

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$REPO_ROOT/repo_reorg_plan/config"
EXECUTE=0
if [[ -f "$CONFIG" ]]; then
  source "$CONFIG" 2>/dev/null || true
fi

echo "EXECUTE=${EXECUTE}"
if [[ "$EXECUTE" != "1" ]]; then
  echo "[PLAN MODE] Would run the following. Set EXECUTE=1 in repo_reorg_plan/config to execute."
  echo "---"
fi

# Ensure archive topics exist
echo "mkdir -p \"$REPO_ROOT/archive/by_topic/misc_orphans\""
echo "mkdir -p \"$REPO_ROOT/archive/by_topic/governance_history\""
if [[ "$EXECUTE" == "1" ]]; then
  mkdir -p "$REPO_ROOT/archive/by_topic/misc_orphans"
  mkdir -p "$REPO_ROOT/archive/by_topic/governance_history"
fi

# Chat session log (low risk)
echo "git mv \"$REPO_ROOT/chat-017c8ae4-2d4c-4fd4-afc7-a0daf499ef3c.txt\" \"$REPO_ROOT/archive/by_topic/misc_orphans/\""
if [[ "$EXECUTE" == "1" ]]; then
  [[ -f "$REPO_ROOT/chat-017c8ae4-2d4c-4fd4-afc7-a0daf499ef3c.txt" ]] && git mv "$REPO_ROOT/chat-017c8ae4-2d4c-4fd4-afc7-a0daf499ef3c.txt" "$REPO_ROOT/archive/by_topic/misc_orphans/"
fi

# NEEDS_DECISION - only echo; never execute
echo "# NEEDS_DECISION: motadata-coder-a-complete-guide_v1.7.md -> governance/ (high risk)"
echo "# NEEDS_DECISION: GREG_Pre-Review_Attack_Result.md -> governance/ (medium risk)"
echo "# NEEDS_DECISION: Golden_Exemplars_Guide_v1.5.md -> archive/by_topic/governance_history (high risk)"

if [[ "$EXECUTE" != "1" ]]; then
  echo "---"
  echo "Exiting 0 (plan mode). Set EXECUTE=1 to perform moves."
  exit 0
fi
