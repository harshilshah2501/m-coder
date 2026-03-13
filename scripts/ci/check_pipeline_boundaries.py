#!/usr/bin/env python3
"""
CI Guard: Fail if any file path contains ml/training/src/sources/Motadata/stage

Prevents pipeline stage artifacts from being placed under the vendor mirror.
Layer-2 pipeline components belong in ml/training/pipeline/.
"""
import sys
from pathlib import Path

FORBIDDEN_PATTERN = "ml/training/src/sources/Motadata/stage"
REPO_ROOT = Path(__file__).resolve().parents[2]


def main():
    violations = []
    for path in REPO_ROOT.rglob("*"):
        if path.is_file():
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                continue
            rel_str = str(rel).replace("\\", "/")
            if FORBIDDEN_PATTERN in rel_str:
                violations.append(rel_str)

    if violations:
        print("FATAL: Pipeline boundary violation.", file=sys.stderr)
        print(f"No files may contain '{FORBIDDEN_PATTERN}'", file=sys.stderr)
        for v in sorted(violations):
            print(f"  - {v}", file=sys.stderr)
        sys.exit(1)

    print("OK: No pipeline artifacts under vendor mirror.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
