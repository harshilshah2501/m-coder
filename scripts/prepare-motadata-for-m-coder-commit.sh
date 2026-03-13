#!/usr/bin/env bash
# Temporarily hide Motadata's .git so the m-coder repo can add its FILES (not a gitlink).
# Run this from repo root BEFORE: git add ml/training/src/sources/Motadata
# Then run restore-motadata-git.sh AFTER you've committed.

set -e
MOTADATA_DIR="ml/training/src/sources/Motadata"
BACKUP=".git.motadata.bak"

if [[ ! -d "$MOTADATA_DIR" ]]; then
  echo "Error: $MOTADATA_DIR not found. Run from m-coder repo root." >&2
  exit 1
fi

if [[ -d "$MOTADATA_DIR/.git" ]]; then
  mv "$MOTADATA_DIR/.git" "$MOTADATA_DIR/$BACKUP"
  echo "Motadata .git hidden (saved as $MOTADATA_DIR/$BACKUP). Add and commit in m-coder, then run restore-motadata-git.sh"
else
  echo "Motadata .git already hidden or missing. Restore with restore-motadata-git.sh if needed."
fi
