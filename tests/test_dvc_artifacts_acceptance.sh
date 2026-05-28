#!/usr/bin/env bash
# Acceptance tests for DVC artifact topology (local disk).
# Verifies: default remote is localstore, storage path exists, no binaries in git,
# pull succeeds when .dvc files exist. No cloud credentials required.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

DVC_LOCAL_PATH="${DVC_LOCAL_PATH:-${HOME}/m-coder_artifacts/dvc}"

echo "=== DVC Artifact Acceptance Tests (Local Disk) ==="
echo "Repo: $REPO_ROOT"
echo "Storage path: $DVC_LOCAL_PATH"
echo ""

# 1) Default remote is localstore
check_default_remote() {
  echo "[1] Default remote is localstore..."
  if [ ! -d .dvc ] || [ ! -f .dvc/config ]; then
    echo "    SKIP: .dvc/config not found (run: ./scripts/setup_dvc_local.sh)"
    return 0
  fi
  if grep -q 'remote = localstore' .dvc/config 2>/dev/null; then
    echo "    OK: default remote is localstore"
  else
    echo "    FAIL: default remote should be localstore; check .dvc/config"
    return 1
  fi
}

# 2) localstore path exists
check_storage_path() {
  echo "[2] localstore storage path exists..."
  if [ -d "$DVC_LOCAL_PATH" ]; then
    echo "    OK: $DVC_LOCAL_PATH exists"
  else
    echo "    WARN: $DVC_LOCAL_PATH does not exist (run: ./scripts/setup_dvc_local.sh)"
  fi
}

# 3) No large binaries tracked in git
check_git_clean() {
  echo "[3] No large binaries in git..."
  tracked="$(git ls-files | grep -E '\.(safetensors|bin|pt|ckpt)$' | grep -v '.dvc' || true)"
  if [ -n "$tracked" ]; then
    echo "    FAIL: tracked binary files found"
    echo "$tracked"
    return 1
  fi
  echo "    OK: no large binaries in git"
}

# 4) If .dvc files exist, dvc pull succeeds (local - no cloud creds)
check_pull_checkpoints() {
  echo "[4] dvc pull restores checkpoints (if .dvc exists)..."
  RUN_ID=""
  for f in ml/artifacts/checkpoints/*.dvc; do
    [ -f "$f" ] || continue
    RUN_ID=$(basename "$f" .dvc)
    break
  done
  if [ -z "$RUN_ID" ]; then
    echo "    SKIP: no ml/artifacts/checkpoints/*.dvc files"
    return 0
  fi
  DIR="ml/artifacts/checkpoints/$RUN_ID"
  if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
    echo "    OK: $DIR exists and non-empty"
  else
    echo "    RUN: dvc pull $DIR.dvc (local - no cloud creds needed)"
    dvc pull "ml/artifacts/checkpoints/$RUN_ID.dvc" || echo "    WARN: dvc pull failed"
    if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
      echo "    OK: $DIR restored"
    else
      echo "    FAIL: $DIR missing or empty after pull"
      return 1
    fi
  fi
}

# 5) dvc pull datasets (same as checkpoints)
check_pull_datasets() {
  echo "[5] dvc pull restores datasets (if .dvc exists)..."
  FREEZE_ID=""
  for f in ml/artifacts/datasets/*.dvc; do
    [ -f "$f" ] || continue
    FREEZE_ID=$(basename "$f" .dvc)
    break
  done
  if [ -z "$FREEZE_ID" ]; then
    echo "    SKIP: no ml/artifacts/datasets/*.dvc files"
    return 0
  fi
  DIR="ml/artifacts/datasets/$FREEZE_ID"
  if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
    echo "    OK: $DIR exists and non-empty"
  else
    echo "    RUN: dvc pull $DIR.dvc"
    dvc pull "ml/artifacts/datasets/$FREEZE_ID.dvc" || echo "    WARN: dvc pull failed"
    if [ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
      echo "    OK: $DIR restored"
    else
      echo "    FAIL: $DIR missing or empty after pull"
      return 1
    fi
  fi
}

check_default_remote
check_storage_path
check_git_clean
check_pull_checkpoints
check_pull_datasets

echo ""
echo "=== Acceptance tests finished ==="
