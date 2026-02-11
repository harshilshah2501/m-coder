#!/usr/bin/env python
"""
Guardrail: ensure governance YAML does NOT appear under docs/.

We intentionally scope this to known governance naming patterns so that
unrelated YAML (e.g., debug fixtures) can still live under docs/archive/.
"""

from __future__ import annotations

import pathlib
import sys


DOCS_ROOT = pathlib.Path(__file__).resolve().parents[2] / "docs"

GOVERNANCE_PATTERNS = (
    "Phase-06-Exit-Criteria",
    "Phase-06-Closure",
    "Validation-Ledger-Entry",
    "RU-AIOPS-",
    "RU-SO-",
    "AI-SURF-",
    "SO-SURF-",
    "CONF-0",
    "DES-0",
    "MIX-0",
)


def main() -> int:
    if not DOCS_ROOT.exists():
        return 0

    offending: list[pathlib.Path] = []

    for path in DOCS_ROOT.rglob("*.yaml"):
        rel = path.relative_to(DOCS_ROOT)
        name = rel.name
        if any(pat in name for pat in GOVERNANCE_PATTERNS):
            offending.append(rel)

    if offending:
        sys.stderr.write(
            "Governance-style YAML files found under docs/ (forbidden):\n"
        )
        for rel in sorted(offending):
            sys.stderr.write(f"  - docs/{rel}\n")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

