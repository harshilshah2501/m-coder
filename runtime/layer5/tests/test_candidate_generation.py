"""Stage A v2: quota lanes, owner injection, debug locality, diagnostics."""

from __future__ import annotations

import tempfile
from pathlib import Path

from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.retrieval.lexical import global_lexical_sorted_hits
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


def test_stage_a_meta_present_and_pool_size():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    corr = root / "src/main/java/com/mindarray/aiops/correlation"
    for i in range(22):
        _touch(corr / f"Extra{i}.java", f"class Extra{i} {{ void correlation() {{}} }}\n")
    _touch(
        corr / "AlertCorrelationEngine.java",
        "public class AlertCorrelationEngine { void correlation() {} }\n",
    )
    _touch(root / "src/main/java/com/mindarray/aiops/api/Constants.java", "class Constants {}\n")
    idx = _idx_for(root)
    q = "AlertCorrelationEngine correlation"
    r = retrieve_lexical(idx, q, 4, LexicalRetrievalConfig(enable_stage_a_v2=True))
    assert r.stage_a_meta is not None
    assert len(r.stage_a_meta.get("candidates", [])) == 20
    tmp.cleanup()


def test_debug_includes_selected_file_in_stage_a_pool():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    corr = root / "src/main/java/com/mindarray/aiops/correlation"
    sel = "src/main/java/com/mindarray/aiops/correlation/Picked.java"
    for i in range(18):
        _touch(corr / f"Neighbor{i}.java", f"class Neighbor{i} {{}}\n")
    _touch(corr / "Picked.java", "public class Picked { void f() {} }\n")
    _touch(corr / "Other.java", "public class Other { void f() {} }\n")
    idx = _idx_for(root)
    r = retrieve_lexical(
        idx,
        "stack trace",
        4,
        LexicalRetrievalConfig(enable_stage_a_v2=True),
        task_type="EXPLAIN_DEBUG",
        selected_file=sel,
    )
    assert r.stage_a_meta is not None
    paths = [c["path"] for c in r.stage_a_meta["candidates"]]
    assert sel in paths
    local = sum(1 for c in r.stage_a_meta["candidates"] if c.get("lane") == "local_seed")
    assert local >= 10


def test_owner_injected_lane_when_authority_provides_primary():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    owner = "src/main/java/com/mindarray/aiops/correlation/OwnerFile.java"
    _touch(root / owner, "public class OwnerFile { void correlation() {} }\n")
    _touch(root / "src/main/java/com/mindarray/aiops/api/Constants.java", "class Constants {}\n")
    idx = _idx_for(root)
    auth = {"primary_owner": {"file": owner}}
    r = retrieve_lexical(
        idx,
        "correlation",
        4,
        LexicalRetrievalConfig(enable_stage_a_v2=True),
        task_type="general",
        authority_resolution=auth,
    )
    assert r.stage_a_meta is not None
    lanes = {c["path"]: c["lane"] for c in r.stage_a_meta["candidates"]}
    assert lanes.get(owner) == "owner_injected"


def test_stage_a_disabled_uses_global_lexical_path():
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(
        root / "src/main/java/com/mindarray/aiops/correlation/Z.java",
        "public class Z { void correlation() {} }\n",
    )
    idx = _idx_for(root)
    q = "correlation"
    off = retrieve_lexical(idx, q, 2, LexicalRetrievalConfig(enable_stage_a_v2=False))
    on = retrieve_lexical(idx, q, 2, LexicalRetrievalConfig(enable_stage_a_v2=True))
    assert off.stage_a_meta is None
    assert on.stage_a_meta is not None
    # Same top-k scoring basis (both use global scores); order should match for tiny fixture.
    assert [h.relative_path for h in off.hits] == [h.relative_path for h in on.hits]
    tmp.cleanup()


def test_generate_candidates_deterministic():
    from runtime.layer5.retrieval.candidate_generation import generate_candidates
    from runtime.layer5.retrieval.query import normalize_query

    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _touch(root / "a/Foo.java", "class Foo {}\n")
    _touch(root / "a/Bar.java", "class Bar {}\n")
    idx = _idx_for(root)
    q = "Foo"
    tok = normalize_query(q, min_token_len=2)
    scored = global_lexical_sorted_hits(idx, q, LexicalRetrievalConfig())
    a, _ = generate_candidates(
        index=idx,
        query=q,
        tokens=tok,
        task_type="general",
        selected_file=None,
        active_file=None,
        authority_resolution=None,
        full_lexical_sorted=scored,
        pool_size=20,
    )
    b, _ = generate_candidates(
        index=idx,
        query=q,
        tokens=tok,
        task_type="general",
        selected_file=None,
        active_file=None,
        authority_resolution=None,
        full_lexical_sorted=scored,
        pool_size=20,
    )
    assert [c.path for c in a] == [c.path for c in b]
    tmp.cleanup()
