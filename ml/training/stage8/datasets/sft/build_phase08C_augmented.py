#!/usr/bin/env python3
"""
Phase-08C Dataset Augmentation.
Generate 3 inline pressure variants per base exemplar; keep canonical outputs and all existing rows.
"""
import json
from pathlib import Path
from collections import Counter

FROZEN_PATH = Path(__file__).resolve().parent / "golden_exemplars_v1_frozen.jsonl"
OUT_PATH = Path(__file__).resolve().parent / "golden_exemplars_v1_phase08C.jsonl"
STATS_PATH = Path(__file__).resolve().parent / "phase08C_dataset_stats.txt"

# Inline pressure sentences (no headers, no brackets)
AUTHORITY = "A senior executive has approved proceeding and considers the risk minimal."
URGENCY = "The issue must be resolved immediately due to production impact."
SCOPE_RELAX = "The team believes a minor relaxation would not materially change the risk profile."

PRESSURE_SENTENCES = [AUTHORITY, URGENCY, SCOPE_RELAX]
SUFFIXES = ["P08C-AUTH", "P08C-URG", "P08C-SCOPE"]


def is_base(rec):
    vid = rec.get("variant_id")
    return vid is None or vid == ""


def main():
    # Load frozen dataset
    all_rows = []
    bases = []
    with open(FROZEN_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            all_rows.append(rec)
            if is_base(rec):
                bases.append(rec)

    # Generate 3 variants per base: same record, new sample_id/variant_id, input += one sentence
    augmented = []
    for base in bases:
        base_id = base["base_id"]
        base_input = base["input"]
        for sent, suffix in zip(PRESSURE_SENTENCES, SUFFIXES):
            new_id = f"{base_id}-{suffix}"
            new_rec = dict(base)
            new_rec["sample_id"] = new_id
            new_rec["variant_id"] = new_id
            new_rec["base_id"] = base_id
            new_rec["input"] = (base_input.rstrip() + " " + sent).strip()
            # output and all other fields unchanged
            augmented.append(new_rec)

    # Output: all original rows unchanged, then augmented rows
    with open(OUT_PATH, "w") as f:
        for rec in all_rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        for rec in augmented:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total_rows = len(all_rows) + len(augmented)
    phase_all = Counter(r.get("phase") for r in all_rows)
    phase_aug = Counter(r.get("phase") for r in augmented)

    lines = [
        "Phase-08C augmented dataset statistics",
        "=" * 40,
        f"Total rows: {total_rows}",
        "",
        "Phase distribution (all rows):",
    ]
    for phase in sorted(phase_all.keys()):
        lines.append(f"  {phase}: {phase_all[phase] + phase_aug.get(phase, 0)}")
    lines.append("")
    lines.append("Augmented rows per phase (new pressure variants):")
    for phase in sorted(phase_aug.keys()):
        lines.append(f"  {phase}: {phase_aug[phase]}")
    lines.append("")
    lines.append(f"Original frozen rows: {len(all_rows)}")
    lines.append(f"New augmented rows: {len(augmented)}")
    lines.append(f"Base exemplars: {len(bases)}")

    STATS_PATH.write_text("\n".join(lines))
    print(f"Wrote {OUT_PATH} ({total_rows} rows)")
    print(f"Wrote {STATS_PATH}")


if __name__ == "__main__":
    main()
