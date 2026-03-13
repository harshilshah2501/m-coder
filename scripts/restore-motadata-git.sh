#!/usr/bin/env bash
# Restore Motadata's .git after committing to m-coder so it remains a separate repo locally.

set -e
MOTADATA_DIR="ml/training/src/sources/Motadata"
BACKUP=".git.motadata.bak"

if [[ ! -d "$MOTADATA_DIR" ]]; then
  echo "Error: $MOTADATA_DIR not found. Run from m-coder repo root." >&2
  exit 1
fi

if [[ -d "$MOTADATA_DIR/$BACKUP" ]]; then
  mv "$MOTADATA_DIR/$BACKUP" "$MOTADATA_DIR/.git"
  echo "Motadata .git restored. You can use git inside $MOTADATA_DIR again."
else
  echo "No $BACKUP found in $MOTADATA_DIR. Nothing to restore."
fi
