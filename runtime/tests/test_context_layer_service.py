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

from runtime.context_layer_service.app import _normalize_workspace_root
from runtime.context_layer_service.evidence_api import export_evidence_bundle_dict

_REPO_ROOT = Path(__file__).resolve().parents[2]


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


def test_export_evidence_bundle_dict_empty_query_raises():
    with pytest.raises(ValueError):
        export_evidence_bundle_dict("/tmp", "   ")


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
        assert out.get("schema_hint") == "layer5.evidence_bundle.v1"
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
