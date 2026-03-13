#!/usr/bin/env bash
set -euo pipefail

# Run the CONF→DES drift pipeline end-to-end from the repo root.
#
# Steps:
#   1) list-run-ids
#   2) extract-traces
#   3) cluster
#   4) build-review-candidates
#   5) (manual) edit conf_drift_candidates_reviewed.jsonl with .correction entries
#   6) build-corrections-from-reviewed
#   7) merge-dataset
#   8) update-stage8-certificate
#   9) write-audit-report

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PY_CMD="python3 -m ml.training.sft.stage7.tools.conf_drift_pipeline"

echo "[run_conf_drift_pipeline] 1) list-run-ids"
$PY_CMD list-run-ids

echo "[run_conf_drift_pipeline] 2) extract-traces"
$PY_CMD extract-traces

# Fail fast if any drift run_ids were missing from traces
if [[ -s "ml/training/sft/stage7/missing_run_ids.txt" ]]; then
  echo "[run_conf_drift_pipeline] ERROR: missing_run_ids.txt is non-empty. Investigate before proceeding." >&2
  echo "  File: ml/training/sft/stage7/missing_run_ids.txt" >&2
  exit 1
fi

echo "[run_conf_drift_pipeline] 3) cluster"
$PY_CMD cluster

echo "[run_conf_drift_pipeline] 4) build-review-candidates"
$PY_CMD build-review-candidates

echo
echo "======================================================================"
echo "MANUAL STEP REQUIRED:"
echo "  - Open ml/training/sft/stage7/conf_drift_candidates_for_review.jsonl"
echo "  - Copy selected records into:"
echo "      ml/training/sft/stage7/conf_drift_candidates_reviewed.jsonl"
echo "  - Add a .correction object per record with posture/allow/block/validation."
echo "======================================================================"
echo

echo "[run_conf_drift_pipeline] 5) build-corrections-from-reviewed"
$PY_CMD build-corrections-from-reviewed

echo "[run_conf_drift_pipeline] 6) merge-dataset"
$PY_CMD merge-dataset

echo "[run_conf_drift_pipeline] 7) update-stage8-certificate"
$PY_CMD update-stage8-certificate

echo "[run_conf_drift_pipeline] 8) write-audit-report"
$PY_CMD write-audit-report

echo "[run_conf_drift_pipeline] DONE."
echo "Audit report written to: ml/training/sft/stage7/CONF_DES_DRIFT_AUDIT_v1.md"

