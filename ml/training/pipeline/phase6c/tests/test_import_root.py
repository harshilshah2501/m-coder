"""Assert phase6c resolves to canonical root (stage6/stage6c)."""
from __future__ import annotations

import pytest

# Canonical root: stage6/stage6c (ml/training/pipeline/stage6/stage6c)
CANONICAL_ROOT_PREFIX = "stage6"
CANONICAL_SUBPATH = "stage6c"


def test_canonical_gates_module_path() -> None:
    """phase6c.reporting.gates must resolve to stage6.stage6c.reporting.gates."""
    from stage6.stage6c.reporting import gates as canonical_gates

    path = canonical_gates.__file__ or ""
    assert CANONICAL_ROOT_PREFIX in path, f"gates __file__ must contain {CANONICAL_ROOT_PREFIX}: {path}"
    assert CANONICAL_SUBPATH in path, f"gates __file__ must contain {CANONICAL_SUBPATH}: {path}"


def test_canonical_render_module_path() -> None:
    """phase6c.reporting.render must resolve to stage6.stage6c.reporting.render."""
    from stage6.stage6c.reporting import render as canonical_render

    path = canonical_render.__file__ or ""
    assert CANONICAL_ROOT_PREFIX in path, f"render __file__ must contain {CANONICAL_ROOT_PREFIX}: {path}"
    assert CANONICAL_SUBPATH in path, f"render __file__ must contain {CANONICAL_SUBPATH}: {path}"


def test_phase6c_forwards_to_canonical() -> None:
    """phase6c.reporting.gates and render must forward to stage6.stage6c implementation."""
    from stage6.stage6c.reporting import gates as canonical_gates
    from stage6.stage6c.reporting import render as canonical_render

    import phase6c.reporting.gates as fwd_gates
    import phase6c.reporting.render as fwd_render

    assert fwd_gates.normalize_model_id is canonical_gates.normalize_model_id
    assert fwd_render.write_summary_json is canonical_render.write_summary_json
