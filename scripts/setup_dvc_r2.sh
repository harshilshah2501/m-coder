#!/usr/bin/env bash
# One-time DVC + R2 setup. Run from repo root after installing DVC (pip install 'dvc[s3]' or snap install dvc).
# Does not store secrets; set AWS_* env vars (see docs/DVC_R2_SETUP.md).

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if ! command -v dvc &>/dev/null; then
  echo "DVC not found. Install with: pip install 'dvc[s3]' or snap install dvc"
  exit 1
fi

# Idempotent: init if needed, add default remote if missing
if [ ! -f .dvc/config ]; then
  dvc init
fi
if ! dvc config core.remote 2>/dev/null | grep -q r2; then
  dvc remote add -d r2 s3://motadataed/dvc
fi
# Endpoint: set via env AWS_ENDPOINT_URL or run:
#   dvc remote modify r2 endpointurl "https://<ACCOUNT_ID>.r2.cloudflarestorage.com"
echo "Done. Set endpoint if needed: dvc remote modify r2 endpointurl 'https://<ACCOUNT_ID>.r2.cloudflarestorage.com'"
echo "Or set AWS_ENDPOINT_URL. See docs/DVC_R2_SETUP.md"
