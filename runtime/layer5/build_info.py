"""
Process-level build identity for HTTP ``/version`` (Plan-Gate, Context Layer).

Set ``M_CODER_REPO_ROOT`` and ``M_CODER_GIT_COMMIT`` from launchers, or fall back to
``git rev-parse`` / filesystem location of this package.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

# m-coder repo root (directory containing ``runtime/``)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def repo_root() -> str:
    env = (os.environ.get("M_CODER_REPO_ROOT") or "").strip()
    return env if env else str(_REPO_ROOT)


def git_commit_short() -> Optional[str]:
    env = (os.environ.get("M_CODER_GIT_COMMIT") or "").strip()
    if env:
        return env
    try:
        r = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if r.returncode == 0 and (r.stdout or "").strip():
            return (r.stdout or "").strip()
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


def module_file(module: str) -> Optional[str]:
    """Resolved import path for debugging (which copy of Layer-5 is loaded)."""
    try:
        import importlib

        m = importlib.import_module(module)
        f = getattr(m, "__file__", None)
        return str(f) if f else None
    except Exception:
        return None


def layer5_build_info() -> Dict[str, Any]:
    """Fields for evidence-export / retrieval debugging."""
    out: Dict[str, Any] = {
        "repo_root": repo_root(),
        "git_commit": git_commit_short(),
    }
    s = module_file("runtime.layer5.evidence.snippet")
    if s:
        out["layer5_snippet_py"] = s
    lx = module_file("runtime.layer5.retrieval.lexical")
    if lx:
        out["layer5_lexical_py"] = lx
    v1 = module_file("runtime.ask_service.v1_ingest")
    if v1:
        out["ask_v1_ingest_py"] = v1
    return out
