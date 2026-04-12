#!/usr/bin/env bash
# Offline check: frozen Phase-1 plugin truth proof matrix (S1–S8, exact_match).
# Does not require Gradle / IntelliJ test sandbox.
set -euo pipefail
M_CODER_ROOT="${M_CODER_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
export M_CODER_ROOT
python3 - "$M_CODER_ROOT" <<'PY'
import json, pathlib, sys

root = pathlib.Path(sys.argv[1])
path = root / "docs/validation/artifacts/plugin_phase1_truth_proof/proof_matrix.json"
if not path.is_file():
    sys.stderr.write(f"FAIL: missing {path}\n")
    sys.exit(1)
rows = json.loads(path.read_text(encoding="utf-8"))
if not isinstance(rows, list) or len(rows) != 8:
    sys.stderr.write(f"FAIL: expected 8 scenarios, got {len(rows) if isinstance(rows, list) else type(rows)}\n")
    sys.exit(1)
ids = {r.get("scenario") for r in rows}
want = {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"}
if ids != want:
    sys.stderr.write(f"FAIL: scenario ids {ids} != {want}\n")
    sys.exit(1)
for r in rows:
    sc = r.get("scenario")
    ex = r.get("exact_match")
    if ex is not True:
        sys.stderr.write(f"FAIL: {sc} exact_match must be true, got {ex!r}\n")
        sys.exit(1)
print("PASS: plugin Phase-1 proof_matrix.json frozen contract (8 scenarios, exact_match true)")
PY
