#!/usr/bin/env python3
"""
CI Guard: Layer-2 structural invariants.

FAIL if:
- any directory matches regex: stage[0-9]+
- any STAGE*.md exists inside ml/training/vendor/
- any .jsonl exists inside vendor/
- any dataset_manifest.json contains "/root/" absolute path
- compiler output path is not ml/training/generated/
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAINING = REPO_ROOT / "ml" / "training"
VENDOR = TRAINING / "vendor"
GENERATED = TRAINING / "generated"
STAGE_DIR_RE = re.compile(r"stage[0-9]+")


def main():
    errors = []

    # 1. No numeric stage dirs as direct children of ml/training.
    #    Stage-6 and Stage-08 live under pipeline/ (pipeline/stage6/, pipeline/stage08/).
    for p in TRAINING.iterdir():
        if p.is_dir() and STAGE_DIR_RE.search(p.name):
            errors.append(f"Numeric stage directory forbidden at ml/training root: ml/training/{p.name}")

    # 2. No STAGE*.md in vendor
    if VENDOR.exists():
        for p in VENDOR.rglob("STAGE*.md"):
            try:
                rel = p.relative_to(REPO_ROOT)
            except ValueError:
                rel = str(p)
            errors.append(f"STAGE*.md not allowed in vendor: {rel}")

    # 3. No .jsonl in vendor
    if VENDOR.exists():
        for p in VENDOR.rglob("*.jsonl"):
            try:
                rel = p.relative_to(REPO_ROOT)
            except ValueError:
                rel = str(p)
            errors.append(f".jsonl not allowed in vendor: {rel}")

    # 4. No /root/ in dataset_manifest.json
    for manifest in REPO_ROOT.rglob("dataset_manifest.json"):
        text = manifest.read_text(errors="ignore")
        if "/root/" in text:
            try:
                rel = manifest.relative_to(REPO_ROOT)
            except ValueError:
                rel = str(manifest)
            errors.append(f"Absolute path /root/ in manifest: {rel}")

    # 5. Compiler DEFAULT_OUT_DIR must be generated/
    compiler_py = REPO_ROOT / "ml" / "training" / "compiler" / "compile_stage7.py"
    if compiler_py.exists():
        text = compiler_py.read_text()
        if 'DEFAULT_OUT_DIR' in text and 'generated' not in text:
            errors.append("Compiler DEFAULT_OUT_DIR must point to generated/")
        if 'DEFAULT_OUT_DIR' in text and '/ "stage7"' in text:
            errors.append("Compiler must not use stage7/ as output path")

    if errors:
        print("FATAL: Structural violations.", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print("OK: Layer-2 structure valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
