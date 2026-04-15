"""
Gate: anchored Motadata-style asks must resolve authority, inject owner in Stage A,
and place primary owner in lexical top-3 when that file exists in the workspace index.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from runtime.layer5.authority.authority_evidence import (
    build_authority_resolution,
    match_concepts_for_query,
)
from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.retrieval.effective_intent import resolve_lexical_task_type
from runtime.layer5.retrieval.path_resolve import paths_match_workspace, resolve_owner_path_in_index
from runtime.layer5.workspace.identity import WorkspaceIdentity


def _touch(p: Path, text: str = "x") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _idx_for(root: Path):
    ident = WorkspaceIdentity(
        canonical_root=str(root.resolve()),
        identity_hash=WorkspaceIdentity.compute_identity_hash(str(root.resolve())),
        original_input=str(root.resolve()),
        path_type="posix",
        is_git_repo=False,
    )
    return build_file_index(ident)


def test_resolve_owner_path_falls_back_when_registry_path_stale():
    """Registry YAML path may not match index layout; basename + class disambiguate."""
    path_set = {
        "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java",
    }
    stale = "motadata/legacy/removed/AlertCorrelationEngine.java"
    r = resolve_owner_path_in_index(
        stale,
        path_set,
        owner_class="AlertCorrelationEngine",
    )
    assert r == "motadata/src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"


def test_match_concepts_finds_alert_correlation_by_class_name():
    reg_path = (
        Path(__file__).resolve().parents[1]
        / "authority"
        / "product_authority_registry.yaml"
    )
    registry = load_registry(reg_path)
    q = "Explain AlertCorrelationEngine behavior in production"
    hits = match_concepts_for_query(q, registry)
    assert hits, "expected registry match via primary_owner class name"
    assert hits[0][0].name == "alert_correlation"


def test_motadata_prefix_drift_owner_in_top3_and_stage_a_injection():
    """
    Registry uses ``motadata/...`` while the synthetic index omits that prefix —
    owner injection + top-3 correction must still align.
    """
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    owner_rel = (
        "src/main/java/com/mindarray/aiops/correlation/AlertCorrelationEngine.java"
    )
    _touch(
        root / owner_rel,
        "public class AlertCorrelationEngine { void run() {} }\n",
    )
    for i in range(18):
        _touch(
            root
            / f"src/main/java/com/mindarray/aiops/correlation/Noise{i}.java",
            f"class Noise{i} {{ void correlation() {{}} }}\n",
        )
    _touch(
        root / "src/main/java/com/mindarray/api/APIServer.java",
        "class APIServer {}\n",
    )
    idx = _idx_for(root)

    reg_path = (
        Path(__file__).resolve().parents[1]
        / "authority"
        / "product_authority_registry.yaml"
    )
    registry = load_registry(reg_path)
    q = "How does alert correlation work"
    ar = build_authority_resolution(q, registry, None)
    assert ar is not None
    po = ar["primary_owner"]
    assert po["file"].endswith("AlertCorrelationEngine.java")

    lex_task = resolve_lexical_task_type("general", q, ar)
    assert lex_task == "CODE"

    r = retrieve_lexical(
        idx,
        q,
        8,
        LexicalRetrievalConfig(enable_stage_a_v2=True),
        task_type=lex_task,
        authority_resolution=ar,
    )
    assert r.stage_a_meta is not None
    inj = r.stage_a_meta.get("lanes_sizes", {}).get("owner_injected", 0)
    assert inj >= 1

    top_paths = [h.relative_path for h in r.hits[:3]]
    assert any(paths_match_workspace(po["file"], p) for p in top_paths)

    tmp.cleanup()
