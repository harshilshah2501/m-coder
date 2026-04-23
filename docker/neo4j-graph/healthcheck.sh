#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="${GRAPH_STATE_FILE:-/state/java_graph_state.env}"
export PYTHONPATH="/workspace"

if [[ ! -f "$STATE_FILE" ]]; then
  echo "state file missing"
  exit 1
fi

if ! grep -q '^LAST_SUCCESS_FINGERPRINT=' "$STATE_FILE"; then
  echo "state file missing fingerprint"
  exit 1
fi

python - <<'PY'
from tools.ast_indexer.query_graph import _driver

with _driver() as driver, driver.session() as session:
    record = session.run(
        "MATCH (state:GraphIngestState {key: $key}) RETURN state.workspaceFingerprint AS fingerprint, state.classRecordCount AS class_count LIMIT 1",
        key="java_ast",
    ).single()
    if record is None or not record.get("fingerprint") or int(record.get("class_count") or 0) <= 0:
        raise SystemExit(1)
PY

exit 0