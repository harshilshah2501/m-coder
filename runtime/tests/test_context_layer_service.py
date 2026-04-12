from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from runtime.context_layer_service.app import (
    _effective_export_workspace,
    _heuristic_unique_motadata_under_home,
    _normalize_workspace_root,
)
from runtime.context_layer_service.evidence_api import export_evidence_bundle_dict
from runtime.context_layer_service.workspace_index_cache import WorkspaceIndexCache
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, retrieve_lexical
from runtime.layer5.workspace.resolver import ResolverConfig, WorkspaceResolver

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_effective_export_workspace_substitutes_roaming_when_env_set(tmp_path, monkeypatch):
    monkeypatch.setenv("MOTADATA_ROOT", str(tmp_path))
    roaming = "/mnt/c/Users/X/AppData/Roaming/JetBrains/IntelliJIdea2026.1/projects/ac852201fe776dbecf4a042e9084f9c8f10c20de"
    w, sub = _effective_export_workspace(roaming)
    assert sub is True
    assert Path(w).resolve() == Path(tmp_path).resolve()


def test_effective_export_workspace_noop_for_real_path(tmp_path):
    w, sub = _effective_export_workspace(str(tmp_path))
    assert sub is False
    assert w == str(tmp_path)


def test_heuristic_unique_motadata_under_home_single(tmp_path):
    (tmp_path / "someuser" / "Projects" / "Motadata").mkdir(parents=True)
    w = _heuristic_unique_motadata_under_home(tmp_path)
    assert w == str((tmp_path / "someuser" / "Projects" / "Motadata").resolve())


def test_heuristic_unique_motadata_under_home_ambiguous(tmp_path):
    for u in ("a", "b"):
        (tmp_path / u / "Projects" / "Motadata").mkdir(parents=True)
    assert _heuristic_unique_motadata_under_home(tmp_path) == ""


def test_effective_export_workspace_heuristic_projects_motadata(tmp_path, monkeypatch):
    monkeypatch.delenv("MOTADATA_ROOT", raising=False)
    monkeypatch.delenv("MOTADATA_CONTEXT_LAYER_DEFAULT_WORKSPACE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "Projects" / "Motadata").mkdir(parents=True)
    roaming = "/mnt/c/Users/X/AppData/Roaming/JetBrains/IntelliJIdea2026.1/projects/ac852201fe776dbecf4a042e9084f9c8f10c20de"
    w, sub = _effective_export_workspace(roaming)
    assert sub is True
    assert Path(w).resolve() == (tmp_path / "Projects" / "Motadata").resolve()


def test_normalize_workspace_root_wsl_bridge():
    if os.name != "posix":
        pytest.skip("WSL bridge mapping applies on POSIX only")
    assert (
        _normalize_workspace_root("/mnt/wsl.localhost/Ubuntu-24.04/home/harshil/Projects/Motadata")
        == "/home/harshil/Projects/Motadata"
    )


def test_export_evidence_bundle_dict_minimal_workspace(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    d = export_evidence_bundle_dict(str(tmp_path), "hello", top_k=4)
    assert d.get("schema_hint") == "layer5.evidence_bundle.v1"
    assert isinstance(d.get("entries"), list)


def test_export_evidence_bundle_dict_reuses_file_index_and_adapter(tmp_path):
    """Batch callers can pass pre-built index + adapter to avoid repeated full scans."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    from runtime.layer5.authority.code_index_adapter import create_adapter
    from runtime.layer5.authority.code_index_builder import build_index
    from runtime.layer5.index import build_file_index
    from runtime.layer5.workspace.identity import WorkspaceIdentity

    root_s = str(tmp_path.resolve())
    ident = WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=False,
    )
    idx = build_file_index(ident)
    adapter = None
    try:
        adapter = create_adapter(code_index=build_index(tmp_path))
    except Exception:
        pass
    d = export_evidence_bundle_dict(
        root_s,
        "hello",
        top_k=4,
        file_index=idx,
        authority_adapter=adapter,
    )
    assert d.get("schema_hint") == "layer5.evidence_bundle.v1"
    assert isinstance(d.get("entries"), list)


def test_export_evidence_bundle_dict_empty_query_raises():
    with pytest.raises(ValueError):
        export_evidence_bundle_dict("/tmp", "   ")


def test_export_evidence_bundle_dict_index_cache_second_request_hits(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    cache = WorkspaceIndexCache(max_keys=4, ttl_sec=0.0)
    m1: dict = {}
    m2: dict = {}
    root_s = str(tmp_path.resolve())
    d1 = export_evidence_bundle_dict(
        root_s,
        "hello",
        top_k=4,
        index_cache=cache,
        index_cache_metrics=m1,
    )
    d2 = export_evidence_bundle_dict(
        root_s,
        "hello",
        top_k=4,
        index_cache=cache,
        index_cache_metrics=m2,
    )
    assert d1.get("schema_hint") == "layer5.evidence_bundle.v1"
    assert d2.get("schema_hint") == "layer5.evidence_bundle.v1"
    assert m1.get("index_cache_hit") is False
    assert m2.get("index_cache_hit") is True
    assert m2.get("file_index_build_ms") == 0.0
    assert m2.get("code_index_build_ms") == 0.0


def test_export_identity_same_snapshot_local_and_export_match(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    root_s = str(tmp_path.resolve())

    resolver = WorkspaceResolver(ResolverConfig())
    identity, err = resolver.resolve(root_s)
    assert err is None
    assert identity is not None

    idx = build_file_index(identity)
    local = retrieve_lexical(idx, "hello", 4, LexicalRetrievalConfig())

    cache = WorkspaceIndexCache(max_keys=4, ttl_sec=0.0)
    m1: dict = {}
    m2: dict = {}
    exported_1 = export_evidence_bundle_dict(
        root_s,
        "hello",
        top_k=4,
        index_cache=cache,
        index_cache_metrics=m1,
    )
    exported_2 = export_evidence_bundle_dict(
        root_s,
        "hello",
        top_k=4,
        index_cache=cache,
        index_cache_metrics=m2,
    )

    assert exported_1.get("workspace_snapshot_hash") == local.workspace_snapshot_hash
    assert exported_1.get("workspace_snapshot_source") == local.workspace_snapshot_source
    assert exported_1.get("workspace_is_dirty") == local.workspace_is_dirty
    assert exported_2.get("workspace_snapshot_hash") == exported_1.get("workspace_snapshot_hash")
    assert m1.get("index_cache_hit") is False
    assert m2.get("index_cache_hit") is True


def test_export_identity_changes_when_snapshot_changes_and_cache_miss(tmp_path):
    (tmp_path / "src").mkdir()
    target = tmp_path / "src" / "foo.py"
    target.write_text("def hello():\n    return 1\n", encoding="utf-8")
    root_s = str(tmp_path.resolve())

    cache = WorkspaceIndexCache(max_keys=4, ttl_sec=0.0)
    m1: dict = {}
    b1 = export_evidence_bundle_dict(
        root_s,
        "hello",
        top_k=4,
        index_cache=cache,
        index_cache_metrics=m1,
    )
    assert m1.get("index_cache_hit") is False

    target.write_text("def hello():\n    return 2\n", encoding="utf-8")

    m2: dict = {}
    b2 = export_evidence_bundle_dict(
        root_s,
        "hello",
        top_k=4,
        index_cache=cache,
        index_cache_metrics=m2,
    )
    assert b1.get("workspace_snapshot_hash") != b2.get("workspace_snapshot_hash")
    assert m2.get("index_cache_hit") is False


def test_export_identity_git_dirty_bypasses_cache_and_marks_dirty(tmp_path):
    if subprocess.run(["git", "--version"], capture_output=True, text=True).returncode != 0:
        pytest.skip("git not available")

    root_s = str(tmp_path.resolve())
    subprocess.run(["git", "init"], cwd=root_s, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=root_s, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=root_s, check=True, capture_output=True)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.py"], cwd=root_s, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root_s, check=True, capture_output=True, text=True)

    # Dirty working tree after HEAD commit.
    (tmp_path / "a.py").write_text("x = 2\n", encoding="utf-8")

    cache = WorkspaceIndexCache(max_keys=4, ttl_sec=0.0)
    m1: dict = {}
    m2: dict = {}
    b1 = export_evidence_bundle_dict(
        root_s,
        "x",
        top_k=2,
        index_cache=cache,
        index_cache_metrics=m1,
    )
    b2 = export_evidence_bundle_dict(
        root_s,
        "x",
        top_k=2,
        index_cache=cache,
        index_cache_metrics=m2,
    )

    assert b1.get("workspace_is_dirty") is True
    assert b1.get("workspace_snapshot_source") == "git_head_dirty_manifest_v1"
    assert b2.get("workspace_is_dirty") is True
    assert m1.get("index_cache_hit") is False
    assert m2.get("index_cache_hit") is False


def test_export_reproducible_for_fixed_snapshot(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("def hello():\n    return 7\n", encoding="utf-8")
    root_s = str(tmp_path.resolve())

    b1 = export_evidence_bundle_dict(root_s, "hello", top_k=4)
    b2 = export_evidence_bundle_dict(root_s, "hello", top_k=4)

    assert b1.get("workspace_snapshot_hash") == b2.get("workspace_snapshot_hash")
    assert b1.get("entries") == b2.get("entries")


def test_export_no_cache_path_unchanged_behavior(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.py").write_text("def hello():\n    pass\n", encoding="utf-8")
    root_s = str(tmp_path.resolve())

    d1 = export_evidence_bundle_dict(root_s, "hello", top_k=4)
    d2 = export_evidence_bundle_dict(root_s, "hello", top_k=4)
    assert d1.get("schema_hint") == "layer5.evidence_bundle.v1"
    assert d2.get("schema_hint") == "layer5.evidence_bundle.v1"
    assert isinstance(d1.get("entries"), list)
    assert isinstance(d2.get("entries"), list)


def test_context_layer_http_export_evidence(tmp_path):
    port = random.randint(30000, 49151)
    env = os.environ.copy()
    env["CONTEXT_LAYER_PORT"] = str(port)
    proc = subprocess.Popen(
        [sys.executable, "-m", "runtime.context_layer_service"],
        cwd=str(_REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        base = f"http://127.0.0.1:{port}"
        for _ in range(50):
            try:
                req = urllib.request.Request(f"{base}/healthz", method="GET")
                with urllib.request.urlopen(req, timeout=1) as r:
                    if r.status == 200:
                        hz = json.loads(r.read().decode("utf-8"))
                        assert hz.get("status") == "ok"
                        assert "package_version" in hz
                        break
            except (urllib.error.URLError, OSError):
                time.sleep(0.1)
        else:
            proc.terminate()
            pytest.fail("Context Layer did not become ready")

        vreq = urllib.request.Request(f"{base}/version", method="GET")
        with urllib.request.urlopen(vreq, timeout=5) as vr:
            vj = json.loads(vr.read().decode("utf-8"))
        assert vj.get("package") == "motadata-context-layer"
        assert vj.get("evidence_schema_hint") == "layer5.evidence_bundle.v1"

        (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
        body = json.dumps({"workspace_root": str(tmp_path), "query": "x", "top_k": 2}).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/v1/export_evidence",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            assert r.status == 200
            out = json.loads(r.read().decode("utf-8"))
        resolver = WorkspaceResolver(ResolverConfig())
        identity, err = resolver.resolve(str(tmp_path))
        assert err is None
        assert identity is not None
        idx = build_file_index(identity)
        local = retrieve_lexical(idx, "x", 2, LexicalRetrievalConfig())
        assert out.get("schema_hint") == "layer5.evidence_bundle.v1"
        assert isinstance(out.get("workspace_snapshot_hash"), str)
        assert out.get("workspace_snapshot_hash")
        assert out.get("workspace_snapshot_hash") == local.workspace_snapshot_hash
        assert out.get("workspace_snapshot_source") == local.workspace_snapshot_source
        assert out.get("workspace_is_dirty") == local.workspace_is_dirty
        assert len(out.get("entries") or []) >= 1

        bad_body = json.dumps(
            {"workspace_root": "/nonexistent_workspace_motadata_xyz_12345", "query": "x", "top_k": 2}
        ).encode("utf-8")
        bad_req = urllib.request.Request(
            f"{base}/v1/export_evidence",
            data=bad_body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as ei:
            urllib.request.urlopen(bad_req, timeout=30)
        assert ei.value.code == 422
        err = json.loads(ei.value.read().decode("utf-8"))
        assert err.get("failure_class") == "workspace_export_failed"
        assert err.get("error") == "export_failed"
    finally:
        proc.terminate()
        proc.wait(timeout=5)
