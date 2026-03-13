"""
Stage-7 forwarding package — discoverability only.

Stage-7 responsibilities are implemented in:
  - compiler/compile_stage7.py (doctrine → JSONL)
  - stage6/stage6c/freeze/ (freeze orchestration, gates, manifest)

This package only re-exports; no new logic.
"""
from __future__ import annotations

# Compiler (doctrine → JSONL)
try:
    from compiler.compile_stage7 import compile_doctrine
except ImportError:
    compile_doctrine = None  # type: ignore[misc, assignment]

# Freeze orchestration
try:
    from stage6.stage6c.freeze import (
        RunFreezeResult,
        evaluate_freeze_gates,
        run_freeze,
    )
except ImportError:
    RunFreezeResult = None  # type: ignore[misc, assignment]
    evaluate_freeze_gates = None  # type: ignore[misc, assignment]
    run_freeze = None  # type: ignore[misc, assignment]

__all__ = [
    "compile_doctrine",
    "RunFreezeResult",
    "evaluate_freeze_gates",
    "run_freeze",
]
