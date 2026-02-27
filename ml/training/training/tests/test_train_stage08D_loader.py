"""Acceptance tests for train_stage08D strict dataset loader (no torch required)."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRIPT_DIR = REPO_ROOT / "ml" / "training" / "training"
DATASET_DIR = REPO_ROOT / "ml" / "training" / "datasets" / "sft"
FROZEN = DATASET_DIR / "golden_exemplars_v1_frozen.jsonl"


def _run_loader_standalone(dataset_path: Path, expect_exit: bool = False) -> tuple[int, str]:
    """Run loader logic in subprocess; return (exit_code, stdout+stderr)."""
    code = f'''
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

SCRIPT_DIR = Path(r"{SCRIPT_DIR}")
VALID_PHASES = {{"REF", "CONF", "DES", "MIX", "CODE"}}

def _sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _utc_now_isoz():
    import datetime
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _detect_schema(obj):
    if isinstance(obj.get("instruction"), str) and isinstance(obj.get("response"), dict) and isinstance(obj.get("phase"), str):
        r = obj["response"]
        if all(k in r for k in ("posture", "allow", "block", "validation")):
            return "STAGE7"
    if isinstance(obj.get("input"), str) and isinstance(obj.get("output"), str) and isinstance(obj.get("phase"), str):
        return "LEGACY"
    return None

def _render_stage7_response(resp):
    posture = resp.get("posture", "").strip()
    allow = resp.get("allow", "").strip()
    block = resp.get("block", "").strip()
    validation = resp.get("validation", "").strip()
    for name, val in [("posture", posture), ("allow", allow), ("block", block), ("validation", validation)]:
        if not val:
            raise ValueError(f"Empty: {{name}}")
    return f"POSTURE: {{posture}}\\nALLOW:\\n{{allow}}\\nBLOCK:\\n{{block}}\\nVALIDATION:\\n{{validation}}\\n"

def load_training_dataset(dataset_path):
    if not dataset_path.exists():
        raise SystemExit(f"FATAL: Dataset file not found: {{dataset_path}}")
    records = []
    schema_type = None
    json_error = None
    with open(dataset_path) as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                json_error = (lineno, str(e))
                break
            detected = _detect_schema(obj)
            if detected is None:
                preview = line[:500]
                raise SystemExit(f"\\nFATAL: Unknown schema at line {{lineno}}\\nKeys: {{list(obj.keys())}}\\nExample: {{preview}}\\n")
            if schema_type is None:
                schema_type = detected
            elif schema_type != detected:
                raise SystemExit(f"\\nFATAL: Mixed schema detected at line {{lineno}}\\nExpected: {{schema_type}}, Found: {{detected}}\\n")
            phase = str(obj.get("phase", "")).strip().upper()
            if phase not in VALID_PHASES:
                raise SystemExit(f"\\nFATAL: Invalid phase at line {{lineno}}: '{{phase}}'\\n")
            if detected == "STAGE7":
                input_text = obj["instruction"].strip()
                output_text = _render_stage7_response(obj["response"])
            else:
                input_text = obj["input"].strip()
                output_text = obj["output"].strip()
                if not input_text or not output_text:
                    raise SystemExit(f"\\nFATAL: Empty input/output at line {{lineno}}\\n")
            records.append({{"input": input_text, "output": output_text, "phase": phase, "base_id": obj.get("base_id") or obj.get("sample_id")}})
    if json_error:
        lineno, msg = json_error
        raise SystemExit(f"\\nFATAL: JSON decode error at line {{lineno}}: {{msg}}\\n")
    if not records:
        raise SystemExit("FATAL: No valid records loaded.")
    rows_per_phase = Counter(r["phase"] for r in records)
    bases_per_phase = defaultdict(set)
    for r in records:
        if r["base_id"]:
            bases_per_phase[r["phase"]].add(r["base_id"])
    total_bases = len(set(r["base_id"] for r in records if r["base_id"]))
    print(f"[DATASET LOADED] path={{dataset_path}} schema={{schema_type}} rows={{len(records)}} bases={{total_bases}} rows_per_phase={{dict(rows_per_phase)}}")
    audit_path = SCRIPT_DIR / "logs" / "stage08D_training_input_audit.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit = {{
        "dataset_path": str(dataset_path),
        "dataset_sha256": _sha256_file(dataset_path),
        "schema_type": schema_type,
        "total_rows": len(records),
        "total_bases": total_bases,
        "rows_per_phase": dict(rows_per_phase),
        "bases_per_phase": {{k: len(v) for k, v in bases_per_phase.items()}},
        "created_at_utc": _utc_now_isoz(),
    }}
    with open(audit_path, "w") as f:
        json.dump(audit, f, indent=2)
    return records

p = Path(r"{str(dataset_path).replace(chr(92), chr(92)+chr(92))}")
try:
    recs = load_training_dataset(p)
    print("OK", len(recs))
except SystemExit as e:
    print("EXIT:", e.code if e.code else 1, str(e))
    sys.exit(e.code if isinstance(e.code, int) and e.code else 1)
'''
    r = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return r.returncode, r.stdout + r.stderr


def test_frozen_stage7_loads_schema_and_100_rows():
    """1) Running training with frozen Stage-7 dataset: schema=STAGE7, 100 rows."""
    assert FROZEN.exists(), f"Frozen dataset not found: {FROZEN}"
    code, out = _run_loader_standalone(FROZEN)
    assert code == 0, f"Loader failed: {out}"
    assert "schema=STAGE7" in out, f"Expected schema=STAGE7, got: {out}"
    assert "rows=100" in out, f"Expected rows=100, got: {out}"
    assert "OK 100" in out, f"Expected OK 100, got: {out}"


def test_audit_file_written():
    """4) stage08D_training_input_audit.json must be written."""
    _run_loader_standalone(FROZEN)
    audit_path = SCRIPT_DIR / "logs" / "stage08D_training_input_audit.json"
    assert audit_path.exists(), f"Audit file not found: {audit_path}"
    data = json.loads(audit_path.read_text())
    assert data["schema_type"] == "STAGE7"
    assert data["total_rows"] == 100
    assert "dataset_sha256" in data


def test_mixed_schema_aborts():
    """2) If dataset contains mixed schemas -> abort immediately."""
    tmp = Path(__file__).resolve().parent / "_tmp_mixed.jsonl"
    # Line 1: STAGE7-like (minimal), Line 2: LEGACY
    tmp.write_text(
        '{"instruction":"x","response":{"posture":"A","allow":"a","block":"b","validation":"v"},"phase":"REF","base_id":"b1"}\n'
        '{"input":"y","output":"z","phase":"REF","base_id":"b2"}\n'
    )
    try:
        code, out = _run_loader_standalone(tmp)
        assert code != 0, f"Expected abort on mixed schema, got exit 0: {out}"
        assert "Mixed schema" in out or "FATAL" in out
    finally:
        tmp.unlink(missing_ok=True)


def test_invalid_phase_aborts():
    """3) If phase invalid -> abort immediately."""
    tmp = Path(__file__).resolve().parent / "_tmp_invalid_phase.jsonl"
    tmp.write_text(
        '{"instruction":"x","response":{"posture":"A","allow":"a","block":"b","validation":"v"},"phase":"INVALID","base_id":"b1"}\n'
    )
    try:
        code, out = _run_loader_standalone(tmp)
        assert code != 0, f"Expected abort on invalid phase, got exit 0: {out}"
        assert "Invalid phase" in out or "FATAL" in out
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    test_frozen_stage7_loads_schema_and_100_rows()
    test_audit_file_written()
    test_mixed_schema_aborts()
    test_invalid_phase_aborts()
    print("All acceptance tests passed.")
