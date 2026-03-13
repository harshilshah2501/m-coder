#!/usr/bin/env python
"""
Guardrail: prevent nested archive directories under the canonical archive/ root.
"""

from __future__ import annotations

import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = REPO_ROOT / "archive"


def main() -> int:
    if not ARCHIVE_ROOT.exists():
        return 0

    offending: list[pathlib.Path] = []

    for path in ARCHIVE_ROOT.rglob("*"):
        if path.is_dir() and path.name.startswith("archive"):
            rel = path.relative_to(REPO_ROOT)
            if rel != pathlib.Path("archive"):
                offending.append(rel)

    if offending:
        sys.stderr.write(
            "Nested archive-like directories detected under archive/ (forbidden):\n"
        )
        for rel in sorted(offending):
            sys.stderr.write(f"  - {rel}\n")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

