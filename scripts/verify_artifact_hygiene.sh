#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MAX_BYTES="${ARTIFACT_MAX_TRACKED_BYTES:-10485760}"

echo "[artifact-hygiene] repo=$ROOT"
echo "[artifact-hygiene] max_tracked_bytes=$MAX_BYTES"

forbidden_regex='(^ml/training/generated/)|(^|/)suite_traces.*\.jsonl$|(^|/)stage6c_ledger.*\.jsonl$|\.safetensors$|\.bin$|\.pt$|\.ckpt$|\.npz$'

tracked_forbidden="$(git ls-files | rg -n "$forbidden_regex" || true)"
if [[ -n "$tracked_forbidden" ]]; then
  echo "[artifact-hygiene] FAIL: forbidden tracked files detected"
  echo "$tracked_forbidden"
  exit 2
fi

oversized=0
while IFS= read -r -d '' f; do
  size="$(stat -c%s "$f")"
  if (( size > MAX_BYTES )); then
    echo "[artifact-hygiene] FAIL: oversized tracked file: ${size} bytes  $f"
    oversized=1
  fi
done < <(git ls-files -z)

if (( oversized == 1 )); then
  exit 3
fi

echo "[artifact-hygiene] OK"
