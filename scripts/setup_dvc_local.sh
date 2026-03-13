#!/usr/bin/env bash
# One-time DVC + local disk setup for prototype/evaluation.
# Creates canonical storage dir, ensures localstore is default. Idempotent.
# No cloud credentials required.

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# Canonical local DVC storage path (repo-adjacent)
DVC_LOCAL_PATH="${DVC_LOCAL_PATH:-/home/harshil/Harshil-PoCs/m-coder_artifacts/dvc}"

# Create storage directory first (so it exists even before DVC is installed)
mkdir -p "$DVC_LOCAL_PATH"
echo "Storage dir: $DVC_LOCAL_PATH"

if ! command -v dvc &>/dev/null; then
  echo "DVC not found. Install with: pip install dvc or snap install dvc"
  echo "Storage path created. Run this script again after installing DVC."
  exit 1
fi

# Idempotent: init if needed
if [ ! -f .dvc/config ]; then
  dvc init
fi

# Ensure localstore exists and points to canonical path
dvc remote add localstore "$DVC_LOCAL_PATH" 2>/dev/null || dvc remote modify localstore url "$DVC_LOCAL_PATH"

# Ensure localstore is default
dvc remote default localstore

echo ""
echo "--- dvc remote list ---"
dvc remote list

echo ""
echo "--- Final storage path ---"
echo "$DVC_LOCAL_PATH"
ls -la "$DVC_LOCAL_PATH" 2>/dev/null || echo "(empty or new)"
