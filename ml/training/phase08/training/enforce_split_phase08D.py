#!/usr/bin/env python3
"""
Phase-08D Split Enforcement — Hard Assertions Before Training

Validates deterministic base-level split with structural coverage invariants.
Aborts if any invariant fails. Does NOT start training.
"""
from pathlib import Path
import json
import sys
from collections import Counter, defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
VALID_PHASES = {"REF", "CONF", "DES", "MIX", "CODE"}

# Phase-08D: Validation must contain at minimum
BALANCED_VAL_SPEC = {"REF": 1, "CONF": 2, "DES": 1, "MIX": 1, "CODE": 1}


def discover_dataset_dir():
    local = SCRIPT_DIR / "dataset"
    if local.exists():
        jsonl_files = list(local.glob("*.jsonl"))
        if jsonl_files:
            return local
    canonical = SCRIPT_DIR.parent / "datasets" / "sft"
    if canonical.exists():
        jsonl_files = list(canonical.glob("*.jsonl"))
        if jsonl_files:
            return canonical
    return SCRIPT_DIR / "dataset"


def load_jsonl_records(dataset_dir, dataset_file=None):
    records = []
    if dataset_file:
        paths = [dataset_dir / dataset_file] if (dataset_dir / dataset_file).exists() else []
    else:
        paths = sorted(dataset_dir.glob("*.jsonl"))
    for path in paths:
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not all(k in obj for k in ("input", "output", "phase")):
                    continue
                records.append(obj)
    return records


def _base_id_and_phase(rec):
    base_id = rec.get("base_id") or rec.get("sample_id") or ""
    phase = str(rec.get("phase", "")).strip().upper()
    if phase not in VALID_PHASES:
        phase = "MIX"
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
            f.write("Phase-08D Split Enforcement — FAILED\n")
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
    
    base_ids = list(base_to_indices.keys())
    train_records = [records[i] for b in base_ids for i in base_to_indices[b] if b not in val_bases]
    val_records = [records[i] for b in base_ids for i in base_to_indices[b] if b in val_bases]
    phases_before = [str(r.get("phase", "")).strip().upper() for r in records]
    for i, p in enumerate(phases_before):
        if p not in VALID_PHASES:
            phases_before[i] = "MIX"
    return train_records, val_records, phases_before, base_to_indices, val_bases


def write_failure_log(error_lines):
    """Write failure message to log file."""
    out = SCRIPT_DIR / "logs" / "phase08D_split_stats_enforced.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write("Phase-08D Split Enforcement — FAILED\n")
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


def write_split_stats_enforced(train_records, val_records, phases_before, val_bases):
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
        "Phase-08D Split Enforcement — Deterministic Base-Level Split",
        "=" * 70,
        "",
        "Validation must contain at minimum:",
        "  ≥1 REF base",
        "  ≥2 CONF bases",
        "  ≥1 DES base",
        "  ≥1 MIX base",
        "  ≥1 CODE base",
        "",
        "All rows sharing the same base_id must remain in the same split.",
        "",
        "Before split (counts per phase, row-level):",
    ]
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


def main():
    print("Phase-08D Split Enforcement")
    print("=" * 50)
    
    dataset_dir = discover_dataset_dir()
    dataset_file = "golden_exemplars_v1_phase08C.jsonl"
    print(f"Loading dataset from: {dataset_dir / dataset_file}")
    
    records = load_jsonl_records(dataset_dir, dataset_file=dataset_file)
    if not records:
        print(f"FATAL: No valid JSONL records in {dataset_dir / dataset_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(records)} records")
    
    # Perform split
    train_records, val_records, phases_before, base_to_indices, val_bases = balanced_base_split_phase08D(records)
    print(f"Split: {len(train_records)} train, {len(val_records)} val")
    
    # Hard Assertions
    print("\nEnforcing assertions...")
    
    # Assert 1: Train coverage
    if not assert_train_coverage(train_records):
        print("FATAL: Assert 1 failed — Train coverage violation", file=sys.stderr)
        sys.exit(1)
    print("✓ Assert 1 passed: Train has >0 rows for all phases")
    
    # Assert 2: Validation coverage
    if not assert_val_coverage(val_records):
        print("FATAL: Assert 2 failed — Validation coverage violation", file=sys.stderr)
        sys.exit(1)
    print("✓ Assert 2 passed: Validation has >0 rows for all phases")
    
    # Assert 3: Base-level integrity
    if not assert_base_level_integrity(train_records, val_records, base_to_indices):
        print("FATAL: Assert 3 failed — Base-level split violation", file=sys.stderr)
        sys.exit(1)
    print("✓ Assert 3 passed: No base-level split leakage")
    
    # Write stats
    stats_file = write_split_stats_enforced(train_records, val_records, phases_before, val_bases)
    print(f"\nSplit stats written to: {stats_file}")
    print("\n" + "=" * 50)
    print("SPLIT VALIDATION PASSED")
    print("=" * 50)
    print("\nTraining may proceed after manual confirmation.")
    print("No automatic training execution.")


if __name__ == "__main__":
    main()
