#!/usr/bin/env python
"""
Guardrail: prevent authored exemplar Phases trees under the ML namespace.

We enforce that no `ml/training/sft/exemplars/Phases/**` tree exists as an
authored location. Training should consume exemplars only from the _build
mirror: `ml/training/_build/exemplars/**`.
"""

from __future__ import annotations

import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FORBIDDEN = REPO_ROOT / "ml" / "training" / "sft" / "exemplars" / "Phases"


def main() -> int:
    if FORBIDDEN.exists():
        sys.stderr.write(
            "Forbidden exemplar Phases tree detected under ml/:\n"
            f"  - {FORBIDDEN.relative_to(REPO_ROOT)}\n"
            "Training must consume exemplars only from "
            "`ml/training/_build/exemplars/**`.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

