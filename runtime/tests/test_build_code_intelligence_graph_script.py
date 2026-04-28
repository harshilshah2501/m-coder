from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from runtime.scripts import build_code_intelligence_graph as cig_script


def test_resolve_registry_path_falls_back_on_permission_error():
    workspace_root = Path("/root/Harshil-PoCs/Motadata")
    rel = "runtime/layer5/authority/product_authority_registry.yaml"

    with patch("pathlib.Path.exists", side_effect=PermissionError("denied")):
        out = cig_script._resolve_registry_path(rel, workspace_root)

    assert str(out).endswith(rel)
    assert str(out).startswith(str(cig_script._project_root()))

