#!/usr/bin/env python3
"""
Stage-08D Split Enforcement — Hard Assertions Before Training

Validates deterministic base-level split with structural coverage invariants.
Aborts if any invariant fails. Does NOT start training.
"""
from pathlib import Path
import json
import sys
import hashlib
from collections import Counter, defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
try:
    from ._path_utils import get_canonical_sft_dataset_dir
except ImportError:
    from _path_utils import get_canonical_sft_dataset_dir

VALID_PHASES = {"REF", "CONF", "DES", "MIX", "CODE"}

# Stage-08D: Validation must contain at minimum (at BASE level)
BALANCED_VAL_SPEC = {"REF": 1, "CONF": 2, "DES": 1, "MIX": 1, "CODE": 1}
REQUIRED_KEYS_LEGACY = ("input", "output", "phase")
REQUIRED_KEYS_STAGE7 = ("instruction", "response", "phase")


def discover_dataset_dir():
    local = SCRIPT_DIR / "dataset"
    if local.exists():
        jsonl_files = list(local.glob("*.jsonl"))
        if jsonl_files:
            return local
    canonical = get_canonical_sft_dataset_dir()
    if canonical.exists():
        jsonl_files = list(canonical.glob("*.jsonl"))
        if jsonl_files:
            return canonical
    return SCRIPT_DIR / "dataset"


def load_jsonl_records(dataset_dir, dataset_file=None):
    """Load JSONL with strict enforcement. Fails with sys.exit(1) if any parse error."""
    records = []
    json_decode_errors = []
    missing_required_keys = []
    invalid_phase = []
    missing_base_id = []
    if dataset_file:
        paths = [dataset_dir / dataset_file] if (dataset_dir / dataset_file).exists() else []
    else:
        paths = sorted(dataset_dir.glob("*.jsonl"))
    for path in paths:
        if not path.exists():
            continue
        with open(path) as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    json_decode_errors.append((path.name, line_num, str(e)))
                    continue
                has_legacy = all(k in obj for k in REQUIRED_KEYS_LEGACY)
                has_stage7 = all(k in obj for k in REQUIRED_KEYS_STAGE7)
                if not (has_legacy or has_stage7):
                    missing = [k for k in REQUIRED_KEYS_STAGE7 if k not in obj]
                    if not missing:
                        missing = [k for k in REQUIRED_KEYS_LEGACY if k not in obj]
                    missing_required_keys.append((path.name, line_num, missing))
                    continue
                phase = str(obj.get("phase", "")).strip().upper()
                if phase not in VALID_PHASES:
                    invalid_phase.append((path.name, line_num, phase, obj))
                    continue
                bid = obj.get("base_id") or obj.get("sample_id")
                if not bid or (isinstance(bid, str) and not bid.strip()):
                    missing_base_id.append((path.name, line_num))
                    continue
                records.append(obj)
    errs = [
        ("json_decode_errors", json_decode_errors),
        ("missing_required_keys", missing_required_keys),
        ("invalid_phase", invalid_phase),
        ("missing_base_id", missing_base_id),
    ]
    total_errors = sum(len(v) for _, v in errs)
    if total_errors > 0:
        lines = [
            "Stage-08D Split Enforcement — JSONL PARSE FAILED",
            "=" * 70,
            "",
            f"Total parse errors: {total_errors}",
        ]
        for name, items in errs:
            if items:
                lines.append(f"\n{name}: {len(items)}")
                for item in items[:5]:  # First 5 examples
                    lines.append(f"  {item}")
                if len(items) > 5:
                    lines.append(f"  ... and {len(items) - 5} more")
        if invalid_phase:
            ex = invalid_phase[0]
            lines.append(f"\nExample invalid_phase record (line {ex[1]}): {json.dumps({k: (v[:80] + '...' if isinstance(v, str) and len(v) > 80 else v) for k, v in ex[3].items()}, default=str)[:500]}")
        lines.append("\nSPLIT VALIDATION FAILED")
        error_text = "\n".join(lines)
        print(error_text, file=sys.stderr)
        out = SCRIPT_DIR / "logs" / "phase08D_split_stats_enforced.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            f.write(error_text)
        sys.exit(1)
    return records


def _base_id_and_phase(rec):
    """Extract base_id and phase. Raises if base_id empty or phase invalid."""
    base_id = rec.get("base_id") or rec.get("sample_id") or ""
    if not base_id or (isinstance(base_id, str) and not base_id.strip()):
        raise ValueError(f"Record missing base_id/sample_id: {json.dumps({k: str(v)[:100] for k, v in rec.items()}, default=str)[:200]}")
    phase = str(rec.get("phase", "")).strip().upper()
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase '{phase}' not in {VALID_PHASES}; record keys: {list(rec.keys())}")
    return base_id, phase


def balanced_base_split_phase08D(records):
    """Deterministic split ensuring validation contains at least: 1 REF, 2 CONF, 1 DES, 1 MIX, 1 CODE.
    Train must also have >0 rows for each phase.
    All variants of each base stay together."""
    base_to_phase = {}
    base_to_indices = {}
    for i, r in enumerate(records):
        bid, phase = _base_id_and_phase(r)
        base_to_phase[bid] = phase
        base_to_indices.setdefault(bid, []).append(i)
    
    bases_by_phase = {}
    for bid, phase in base_to_phase.items():
        bases_by_phase.setdefault(phase, []).append(bid)
    for phase in bases_by_phase:
        bases_by_phase[phase].sort()
    
    # Check feasibility: Can we satisfy both val minimums AND train >0 for all phases?
    feasibility_errors = []
    for phase in VALID_PHASES:
        total_bases = len(bases_by_phase.get(phase, []))
        val_min = BALANCED_VAL_SPEC.get(phase, 0)
        train_min = 1  # Train must have at least 1 base
        if total_bases < val_min + train_min:
            feasibility_errors.append(
                f"{phase}: {total_bases} total bases, need {val_min} for val + {train_min} for train = {val_min + train_min} minimum"
            )
    
    if feasibility_errors:
        error_msg = [
            "FATAL: Dataset does not have enough bases to satisfy split requirements:",
        ]
        for err in feasibility_errors:
            error_msg.append(f"  {err}")
        error_msg.extend([
            "",
            "Cannot satisfy both:",
            "  - Validation minimums (≥1 REF, ≥2 CONF, ≥1 DES, ≥1 MIX, ≥1 CODE)",
            "  - Train must have >0 rows for all phases",
            "",
            "SPLIT VALIDATION FAILED",
        ])
        error_text = "\n".join(error_msg)
        print(error_text, file=sys.stderr)
        # Write failure to log file
        out = SCRIPT_DIR / "logs" / "phase08D_split_stats_enforced.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            f.write("Stage-08D Split Enforcement — FAILED\n")
            f.write("=" * 70 + "\n\n")
            f.write(error_text)
        sys.exit(1)
    
    # Select validation bases (minimum required)
    val_bases = set()
    for phase, count in BALANCED_VAL_SPEC.items():
        bases = bases_by_phase.get(phase, [])
        for b in bases[:count]:
            val_bases.add(b)
    
    # Ensure train has at least one base per phase
    train_bases_by_phase = {}
    for phase in VALID_PHASES:
        bases = bases_by_phase.get(phase, [])
        val_count = BALANCED_VAL_SPEC.get(phase, 0)
        # Take bases starting after the validation ones
        train_bases = bases[val_count:]
        if train_bases:
            train_bases_by_phase[phase] = train_bases[0]  # At least one for train
    
    # Add train bases to ensure coverage
    for phase, base_id in train_bases_by_phase.items():
        if base_id not in val_bases:
            # Already handled by slicing above, but ensure it's not in val
            pass
    
    base_ids = sorted(base_to_indices.keys())
    train_records = [records[i] for b in base_ids for i in sorted(base_to_indices[b]) if b not in val_bases]
    val_records = [records[i] for b in base_ids for i in sorted(base_to_indices[b]) if b in val_bases]

    # Enforce BALANCED_VAL_SPEC at BASE level (from val_records)
    val_bases_by_phase = defaultdict(set)
    for r in val_records:
        bid, phase = _base_id_and_phase(r)
        val_bases_by_phase[phase].add(bid)
    for phase in BALANCED_VAL_SPEC:
        n = len(val_bases_by_phase[phase])
        req = BALANCED_VAL_SPEC[phase]
        if n < req:
            error_msg = (
                f"FATAL: Val base-level minimum not met for {phase}: "
                f"got {n} bases, need >= {req}"
            )
            print(error_msg, file=sys.stderr)
            write_failure_log([error_msg])
            sys.exit(1)

    phases_before = [str(r.get("phase", "")).strip().upper() for r in records]
    return train_records, val_records, phases_before, base_to_indices, val_bases


def _compute_file_sha256(path):
    """Return SHA256 hex digest of file bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_split_manifest(
    dataset_path,
    dataset_sha256,
    total_rows,
    total_bases,
    train_rows,
    val_rows,
    train_bases,
    val_bases,
    bases_per_phase_train,
    bases_per_phase_val,
    rows_per_phase_train,
    rows_per_phase_val,
):
    """Write machine-readable split manifest for audit."""
    manifest = {
        "dataset_path": str(dataset_path),
        "dataset_sha256": dataset_sha256,
        "total_rows": total_rows,
        "total_bases": total_bases,
        "train_rows": train_rows,
        "val_rows": val_rows,
        "train_bases": sorted(train_bases),
        "val_bases": sorted(val_bases),
        "bases_per_phase_train": dict(bases_per_phase_train),
        "bases_per_phase_val": dict(bases_per_phase_val),
        "rows_per_phase_train": dict(rows_per_phase_train),
        "rows_per_phase_val": dict(rows_per_phase_val),
    }
    out = SCRIPT_DIR / "logs" / "stage08D_split_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)
    return out


def write_failure_log(error_lines):
    """Write failure message to log file."""
    out = SCRIPT_DIR / "logs" / "phase08D_split_stats_enforced.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write("Stage-08D Split Enforcement — FAILED\n")
        f.write("=" * 70 + "\n\n")
        f.write("\n".join(error_lines))
        f.write("\n\nSPLIT VALIDATION FAILED\n")


def assert_train_coverage(train_records):
    """Assert 1: Train must have >0 rows for each phase."""
    train_phases = [str(r.get("phase", "")).strip().upper() for r in train_records]
    train_c = Counter(train_phases)
    failures = []
    for phase in VALID_PHASES:
        if train_c.get(phase, 0) == 0:
            failures.append(phase)
    if failures:
        error_lines = [f"FATAL: Train split missing phase {phase}" for phase in failures]
        for line in error_lines:
            print(line, file=sys.stderr)
        write_failure_log(error_lines)
        return False
    return True


def assert_val_coverage(val_records):
    """Assert 2: Validation must have >0 rows for each phase."""
    val_phases = [str(r.get("phase", "")).strip().upper() for r in val_records]
    val_c = Counter(val_phases)
    failures = []
    for phase in VALID_PHASES:
        if val_c.get(phase, 0) == 0:
            failures.append(phase)
    if failures:
        error_lines = [f"FATAL: Validation split missing phase {phase}" for phase in failures]
        for line in error_lines:
            print(line, file=sys.stderr)
        write_failure_log(error_lines)
        return False
    return True


def assert_base_level_integrity(train_records, val_records, base_to_indices):
    """Assert 3: All rows with same base_id must be in same split (no leakage)."""
    train_base_ids = set()
    val_base_ids = set()
    
    for r in train_records:
        bid = r.get("base_id") or r.get("sample_id", "")
        if bid:
            train_base_ids.add(bid)
    
    for r in val_records:
        bid = r.get("base_id") or r.get("sample_id", "")
        if bid:
            val_base_ids.add(bid)
    
    leakage = train_base_ids & val_base_ids
    if leakage:
        error_lines = [f"FATAL: Base-level split violation for {bid}" for bid in leakage]
        for line in error_lines:
            print(line, file=sys.stderr)
        write_failure_log(error_lines)
        return False
    return True


def write_split_stats_enforced(train_records, val_records, phases_before, val_bases, dataset_path=None, dataset_sha256=None):
    """Write split stats with enforcement confirmation."""
    train_phases = [str(r.get("phase", "")).strip().upper() for r in train_records]
    val_phases = [str(r.get("phase", "")).strip().upper() for r in val_records]
    before = Counter(phases_before)
    train_c = Counter(train_phases)
    val_c = Counter(val_phases)
    
    # Group base IDs by phase
    train_bases_by_phase = defaultdict(set)
    val_bases_by_phase = defaultdict(set)
    
    for r in train_records:
        bid = r.get("base_id") or r.get("sample_id", "")
        phase = str(r.get("phase", "")).strip().upper()
        if bid and phase in VALID_PHASES:
            train_bases_by_phase[phase].add(bid)
    
    for r in val_records:
        bid = r.get("base_id") or r.get("sample_id", "")
        phase = str(r.get("phase", "")).strip().upper()
        if bid and phase in VALID_PHASES:
            val_bases_by_phase[phase].add(bid)
    
    lines = [
        "Stage-08D Split Enforcement — Deterministic Base-Level Split",
        "=" * 70,
        "",
    ]
    if dataset_path is not None:
        lines.append(f"Dataset: {dataset_path}")
    if dataset_sha256 is not None:
        lines.append(f"Dataset SHA256: {dataset_sha256}")
    lines.extend([
        "",
        "Validation must contain at minimum (base-level):",
        "  ≥1 REF base",
        "  ≥2 CONF bases",
        "  ≥1 DES base",
        "  ≥1 MIX base",
        "  ≥1 CODE base",
        "",
        "All rows sharing the same base_id must remain in the same split.",
        "",
        "Before split (counts per phase, row-level):",
    ])
    for p in VALID_PHASES:
        lines.append(f"  {p}: {before.get(p, 0)}")
    lines.extend([
        "",
        f"Train: {len(train_records)} rows",
        "Train per phase:",
    ])
    for p in VALID_PHASES:
        lines.append(f"  {p}: {train_c.get(p, 0)}")
    lines.extend([
        "",
        "Train base IDs (grouped by phase):",
    ])
    for p in VALID_PHASES:
        bases = sorted(train_bases_by_phase[p])
        if bases:
            lines.append(f"  {p}: {', '.join(bases)}")
        else:
            lines.append(f"  {p}: (none)")
    lines.extend([
        "",
        f"Val: {len(val_records)} rows",
        "Val per phase:",
    ])
    for p in VALID_PHASES:
        lines.append(f"  {p}: {val_c.get(p, 0)}")
    lines.extend([
        "",
        "Val base IDs (grouped by phase):",
    ])
    for p in VALID_PHASES:
        bases = sorted(val_bases_by_phase[p])
        if bases:
            lines.append(f"  {p}: {', '.join(bases)}")
        else:
            lines.append(f"  {p}: (none)")
    lines.extend([
        "",
        "=" * 70,
        "SPLIT VALIDATION PASSED",
    ])
    
    out = SCRIPT_DIR / "logs" / "phase08D_split_stats_enforced.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write("\n".join(lines))
    
    return out


def run_selftest():
    """Synthetic records for CI: invalid phase fails, missing base_id fails, val base minimums enforced."""
    import os
    import subprocess
    import tempfile
    passed = 0
    failed = 0

    # Test 1: Invalid phase should fail (load_jsonl_records sys.exit(1) - run in subprocess)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({"input": "x", "output": "y", "phase": "INVALID", "base_id": "B1"}) + "\n")
        bad_path = f.name
    try:
        bad_dir = str(Path(bad_path).parent)
        r = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--dataset-dir", bad_dir, "--dataset", Path(bad_path).name],
            capture_output=True,
            text=True,
        )
        if r.returncode == 1:
            print("SELFTEST PASS: invalid phase fails")
            passed += 1
        else:
            print(f"SELFTEST FAIL: invalid phase should exit 1, got {r.returncode}")
            failed += 1
    finally:
        os.unlink(bad_path)

    # Test 2: Missing base_id should fail
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({"input": "x", "output": "y", "phase": "REF"}) + "\n")
        bad_path = f.name
    try:
        bad_dir = str(Path(bad_path).parent)
        r = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--dataset-dir", bad_dir, "--dataset", Path(bad_path).name],
            capture_output=True,
            text=True,
        )
        if r.returncode == 1:
            print("SELFTEST PASS: missing base_id fails")
            passed += 1
        else:
            print(f"SELFTEST FAIL: missing base_id should exit 1, got {r.returncode}")
            failed += 1
    finally:
        os.unlink(bad_path)

    # Test 3: Val base minimums enforce 2 CONF bases (need 2 CONF + 1 train, so 3 CONF total; others need 2 each)
    synth = []
    for bid, phase in [
        ("B1", "REF"), ("B7", "REF"),
        ("B2", "CONF"), ("B3", "CONF"), ("B8", "CONF"),
        ("B4", "DES"), ("B9", "DES"),
        ("B5", "MIX"), ("B10", "MIX"),
        ("B6", "CODE"), ("B11", "CODE"),
    ]:
        synth.append({"input": "x", "output": "y", "phase": phase, "base_id": bid})
    train_r, val_r, _, _, _ = balanced_base_split_phase08D(synth)
    val_conf_bases = len({r.get("base_id") or r.get("sample_id") for r in val_r if str(r.get("phase", "")).strip().upper() == "CONF"})
    if val_conf_bases >= 2:
        print("SELFTEST PASS: val has >= 2 CONF bases")
        passed += 1
    else:
        print(f"SELFTEST FAIL: val has {val_conf_bases} CONF bases, need >= 2")
        failed += 1

    print(f"\nSelftest: {passed} passed, {failed} failed")
    return failed == 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Stage-08D Split Enforcement")
    parser.add_argument("--selftest", action="store_true", help="Run synthetic selftest for CI")
    parser.add_argument("--dataset", default="golden_exemplars_v1_frozen.jsonl", help="Dataset filename")
    parser.add_argument("--dataset-dir", default=None, help="Override dataset directory (for selftest)")
    args = parser.parse_args()

    if args.selftest:
        ok = run_selftest()
        sys.exit(0 if ok else 1)

    print("Stage-08D Split Enforcement")
    print("=" * 50)

    dataset_dir = Path(args.dataset_dir) if args.dataset_dir else discover_dataset_dir()
    dataset_file = args.dataset
    dataset_path = dataset_dir / dataset_file
    print(f"Loading dataset from: {dataset_path}")

    if not dataset_path.exists():
        print(f"FATAL: Dataset file not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)

    dataset_sha256 = _compute_file_sha256(dataset_path)
    print(f"Dataset SHA256: {dataset_sha256[:16]}...")

    records = load_jsonl_records(dataset_dir, dataset_file=dataset_file)
    if not records:
        print(f"FATAL: No valid JSONL records in {dataset_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(records)} records")

    train_records, val_records, phases_before, base_to_indices, val_bases = balanced_base_split_phase08D(records)
    print(f"Split: {len(train_records)} train, {len(val_records)} val")

    print("\nEnforcing assertions...")

    if not assert_train_coverage(train_records):
        print("FATAL: Assert 1 failed — Train coverage violation", file=sys.stderr)
        sys.exit(1)
    print("✓ Assert 1 passed: Train has >0 rows for all phases")

    if not assert_val_coverage(val_records):
        print("FATAL: Assert 2 failed — Validation coverage violation", file=sys.stderr)
        sys.exit(1)
    print("✓ Assert 2 passed: Validation has >0 rows for all phases")

    if not assert_base_level_integrity(train_records, val_records, base_to_indices):
        print("FATAL: Assert 3 failed — Base-level split violation", file=sys.stderr)
        sys.exit(1)
    print("✓ Assert 3 passed: No base-level split leakage")

    train_bases_set = {r.get("base_id") or r.get("sample_id") for r in train_records}
    val_bases_set = {r.get("base_id") or r.get("sample_id") for r in val_records}
    train_phases = [str(r.get("phase", "")).strip().upper() for r in train_records]
    val_phases = [str(r.get("phase", "")).strip().upper() for r in val_records]
    bases_per_phase_train = {p: len({r.get("base_id") or r.get("sample_id") for r in train_records if str(r.get("phase", "")).strip().upper() == p}) for p in VALID_PHASES}
    bases_per_phase_val = {p: len({r.get("base_id") or r.get("sample_id") for r in val_records if str(r.get("phase", "")).strip().upper() == p}) for p in VALID_PHASES}
    rows_per_phase_train = dict(Counter(train_phases))
    rows_per_phase_val = dict(Counter(val_phases))

    manifest_file = write_split_manifest(
        dataset_path=str(dataset_path),
        dataset_sha256=dataset_sha256,
        total_rows=len(records),
        total_bases=len(base_to_indices),
        train_rows=len(train_records),
        val_rows=len(val_records),
        train_bases=train_bases_set,
        val_bases=val_bases_set,
        bases_per_phase_train=bases_per_phase_train,
        bases_per_phase_val=bases_per_phase_val,
        rows_per_phase_train=rows_per_phase_train,
        rows_per_phase_val=rows_per_phase_val,
    )
    print(f"Split manifest written to: {manifest_file}")

    stats_file = write_split_stats_enforced(
        train_records, val_records, phases_before, val_bases,
        dataset_path=str(dataset_path),
        dataset_sha256=dataset_sha256,
    )
    print(f"Split stats written to: {stats_file}")
    print("\n" + "=" * 50)
    print("SPLIT VALIDATION PASSED")
    print("=" * 50)
    print("\nTraining may proceed after manual confirmation.")
    print("No automatic training execution.")


if __name__ == "__main__":
    main()
