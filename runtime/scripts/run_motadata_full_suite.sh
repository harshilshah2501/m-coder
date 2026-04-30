#!/usr/bin/env bash
#
# Full Motadata verification suite runner.
# Produces contract + utility + prompt-batch + pytest outputs, then writes one summary JSON.
#
# Usage:
#   MOTADATA_REPO_ROOT=/path/to/Motadata \
#   ./runtime/scripts/run_motadata_full_suite.sh
#
# Optional:
#   REPORTS_DIR=runtime/eval/reports
#   QUALITY_POLICY=docs/validation/motadata_evidence_quality_policy.v1.json
#   SCENARIOS=docs/validation/motadata_aiops_behavior_scenarios.v1.json
#   UTILITY_SCENARIOS=docs/validation/motadata_developer_utility_scenarios.v1.json
#   TIMEOUT_SEC=900
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

MOTADATA_REPO_ROOT="${MOTADATA_REPO_ROOT:-${MOTADATA_GATE_WORKSPACE_ROOT:-}}"
if [[ -z "${MOTADATA_REPO_ROOT}" ]]; then
  echo "ERROR: set MOTADATA_REPO_ROOT (or MOTADATA_GATE_WORKSPACE_ROOT)." >&2
  exit 2
fi

REPORTS_DIR="${REPORTS_DIR:-runtime/eval/reports}"
QUALITY_POLICY="${QUALITY_POLICY:-docs/validation/motadata_evidence_quality_policy.v1.json}"
SCENARIOS="${SCENARIOS:-docs/validation/motadata_aiops_behavior_scenarios.v1.json}"
UTILITY_SCENARIOS="${UTILITY_SCENARIOS:-docs/validation/motadata_developer_utility_scenarios.v1.json}"
TIMEOUT_SEC="${TIMEOUT_SEC:-900}"

mkdir -p "$REPORTS_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"

CONTRACT_JSON="$REPORTS_DIR/motadata_contract_20_${TS}.json"
PYTEST_TXT="$REPORTS_DIR/motadata_pytest_${TS}.txt"
BATCH_JSON="$REPORTS_DIR/developer_eval_batch_${TS}.json"
BATCH_MD="$REPORTS_DIR/developer_eval_batch_${TS}.md"
SUITE_JSON="$REPORTS_DIR/motadata_full_suite_${TS}.json"

echo "[1/4] Contract 20-scenario gate -> $CONTRACT_JSON"
python3 runtime/scripts/motadata_behavior_verify.py \
  --workspace-root "$MOTADATA_REPO_ROOT" \
  --scenarios "$SCENARIOS" \
  --quality-policy "$QUALITY_POLICY" \
  --scenarios-only \
  --print dev \
  --out "$CONTRACT_JSON"

echo "[2/4] Core pytest battery -> $PYTEST_TXT"
PYTHONPATH=. pytest -q \
  runtime/tests/test_code_intelligence_graph_smoke.py \
  runtime/tests/test_code_intelligence_graph_v1.py \
  runtime/tests/test_graph_traversal_payload.py \
  runtime/tests/test_ask_v1_ingest.py \
  runtime/tests/test_answer_shaping_pass_a.py \
  runtime/tests/test_articulated_answer.py \
  runtime/tests/test_bounded_ask_narrator.py \
  runtime/tests/test_motadata_20_code_scenarios.py | tee "$PYTEST_TXT"

echo "[3/4] Utility + prompt batch reports -> $BATCH_JSON / $BATCH_MD"
python3 runtime/eval/batch_run_developer_eval.py \
  --workspace-root "$MOTADATA_REPO_ROOT" \
  --utility-scenarios "$UTILITY_SCENARIOS" \
  --reports-dir "$REPORTS_DIR" \
  --timeout-sec "$TIMEOUT_SEC"

# batch_run_developer_eval writes timestamped files; choose latest created for this run window.
LATEST_BATCH_JSON="$(ls -1t "$REPORTS_DIR"/developer_eval_batch_*.json 2>/dev/null | head -n 1 || true)"
LATEST_BATCH_MD="$(ls -1t "$REPORTS_DIR"/developer_eval_batch_*.md 2>/dev/null | head -n 1 || true)"
if [[ -n "$LATEST_BATCH_JSON" ]]; then
  cp "$LATEST_BATCH_JSON" "$BATCH_JSON"
fi
if [[ -n "$LATEST_BATCH_MD" ]]; then
  cp "$LATEST_BATCH_MD" "$BATCH_MD"
fi

echo "[4/4] Writing suite summary -> $SUITE_JSON"
python3 - "$CONTRACT_JSON" "$PYTEST_TXT" "$BATCH_JSON" "$BATCH_MD" "$SUITE_JSON" <<'PY'
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

contract_json, pytest_txt, batch_json, batch_md, suite_json = sys.argv[1:]

def load_json(path):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

contract = load_json(contract_json) or {}
batch = load_json(batch_json) or {}
pytest_text = pathlib.Path(pytest_txt).read_text(encoding="utf-8") if pathlib.Path(pytest_txt).exists() else ""

scenario_suite = contract.get("scenario_suite") if isinstance(contract, dict) else {}
contract_all_pass = bool((scenario_suite or {}).get("all_pass")) if isinstance(scenario_suite, dict) else None
graph_state = (scenario_suite or {}).get("graph_preflight", {}).get("state") if isinstance(scenario_suite, dict) else None

utility_suite = batch.get("utility_suite") if isinstance(batch, dict) else None
utility_all_pass = utility_suite.get("all_pass") if isinstance(utility_suite, dict) else None
prompt_batch = batch.get("prompt_batch") if isinstance(batch, dict) else None
prompt_status = prompt_batch.get("status") if isinstance(prompt_batch, dict) else None

pytest_passed = None
pytest_total = None
if pytest_text:
    m = re.search(r"(\d+)\s+passed", pytest_text)
    if m:
        pytest_passed = int(m.group(1))
    m2 = re.search(r"(\d+)\s+(?:passed|failed|error|errors|skipped).*$", pytest_text.strip().splitlines()[-1] if pytest_text.strip().splitlines() else "")
    if m2:
        pytest_total = int(m2.group(1))
    # Conservative pass check:
    pytest_ok = ("failed" not in pytest_text.lower()) and ("error" not in pytest_text.lower())
else:
    pytest_ok = None

overall_all_pass = all(
    x is True
    for x in [contract_all_pass, pytest_ok]
    if x is not None
)
if utility_all_pass is not None:
    overall_all_pass = overall_all_pass and bool(utility_all_pass)

out = {
    "schema_version": "motadata_full_suite.v1",
    "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "overall_all_pass": overall_all_pass,
    "contract": {
        "all_pass": contract_all_pass,
        "graph_preflight_state": graph_state,
        "report_json": contract_json,
    },
    "pytest": {
        "all_pass": pytest_ok,
        "passed_count": pytest_passed,
        "total_count_hint": pytest_total,
        "report_txt": pytest_txt,
    },
    "utility_and_prompt_batch": {
        "utility_all_pass": utility_all_pass,
        "prompt_batch_status": prompt_status,
        "report_json": batch_json if pathlib.Path(batch_json).exists() else None,
        "report_md": batch_md if pathlib.Path(batch_md).exists() else None,
    },
}

pathlib.Path(suite_json).write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
PY

echo "DONE: $SUITE_JSON"
