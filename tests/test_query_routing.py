from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from runtime.core.query_router import QueryIntent, QueryRouter
from runtime.scripts.motadata_query_cli import _merge_evidence_bundles


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE_ROOT = Path(os.environ.get("MOTADATA_ACCEPTANCE_WORKSPACE_ROOT", "/root/Harshil-PoCs/Motadata"))


def test_router_smoke_no_network():
    router = QueryRouter()
    assert router.classify("What model are you?").intent == QueryIntent.IDENTITY
    assert router.classify("Which class is the base class for all APIs?").intent == QueryIntent.STRUCTURAL
    result = router.classify("How does mail server configuration work?")
    assert result.intent == QueryIntent.DECOMPOSE
    assert result.sub_queries is not None and len(result.sub_queries) == 3
    assert result.metadata.get("fallback") in {"deterministic_subqueries", "graph_seeded_subqueries"}
    assert router.classify("Show me the AlertManager class").intent == QueryIntent.SEMANTIC


def test_resolve_structural_graph_hit(monkeypatch: pytest.MonkeyPatch):
    router = QueryRouter()

    def fake_timed_base_class(_: str):
        return (
            {
                "name": "AbstractAPI",
                "qualified_name": "com.mindarray.api.AbstractAPI",
                "file_path": "/tmp/AbstractAPI.java",
            },
            2.5,
        )

    monkeypatch.setattr("runtime.core.query_router.timed_base_class", fake_timed_base_class)
    initial = router.classify("Which class is the base class for all APIs?")
    resolved = router.resolve_structural("Which class is the base class for all APIs?", initial.metadata)
    assert resolved.intent == QueryIntent.STRUCTURAL
    assert resolved.answer is not None
    assert "com.mindarray.api.AbstractAPI" in resolved.answer
    assert resolved.metadata["graph_query_ms"] == 2.5


def test_merge_evidence_bundles_dedupes_and_preserves_router_metadata():
    bundle_a = {
        "workspace_identity_hash": "hash-1",
        "entries": [
            {"relative_path": "src/A.java", "retrieval_score": 8, "rank": 0},
            {"relative_path": "src/B.java", "retrieval_score": 5, "rank": 1},
        ],
    }
    bundle_b = {
        "workspace_identity_hash": "hash-1",
        "entries": [
            {"relative_path": "src/B.java", "retrieval_score": 9, "rank": 0},
            {"relative_path": "src/C.java", "retrieval_score": 4, "rank": 1},
        ],
        "authority_resolution": {"authority_status": "validated"},
    }

    merged = _merge_evidence_bundles(
        "How does mail server configuration work?",
        [bundle_a, bundle_b],
        top_k=4,
        sub_queries=["q1", "q2", "q3"],
    )
    entries = merged["entries"]
    assert [entry["relative_path"] for entry in entries[:3]] == ["src/B.java", "src/A.java", "src/C.java"]
    assert merged["fusion_diagnostics"]["router"]["intent"] == "decompose"
    assert merged["authority_resolution"]["authority_status"] == "validated"


def _healthcheck(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, OSError):
        return False


def _neo4j_reachable(host: str = "127.0.0.1", port: int = 7687) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def _run_cli(query: str, out_path: Path, reward_path: Path) -> tuple[dict, dict, subprocess.CompletedProcess[str]]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    cmd = [
        sys.executable,
        str(REPO_ROOT / "runtime" / "scripts" / "motadata_query_cli.py"),
        "--workspace-root",
        str(DEFAULT_WORKSPACE_ROOT),
        "--query",
        query,
        "--out",
        str(out_path),
        "--with-reward",
        "--reward-out",
        str(reward_path),
    ]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, text=True, capture_output=True, timeout=300)
    if proc.returncode != 0:
        raise AssertionError(f"CLI failed for query {query!r}: {proc.stderr}\n{proc.stdout}")
    return (
        json.loads(out_path.read_text(encoding="utf-8")),
        json.loads(reward_path.read_text(encoding="utf-8")),
        proc,
    )


@pytest.mark.integration
def test_cli_acceptance_routing_all_three_pass():
    if not DEFAULT_WORKSPACE_ROOT.exists():
        pytest.skip(f"Motadata workspace root not found: {DEFAULT_WORKSPACE_ROOT}")
    if not _healthcheck("http://127.0.0.1:8091/healthz") or not _healthcheck("http://127.0.0.1:8089/healthz"):
        pytest.skip("Context Layer or Plan-Gate service is not running locally")
    if not _neo4j_reachable():
        pytest.skip("Neo4j is not reachable locally")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)

        t1_resp, t1_reward, _ = _run_cli(
            "Which class is the base class for all APIs?",
            tmp_root / "t1.json",
            tmp_root / "t1.reward.json",
        )
        assert (t1_resp.get("metadata") or {}).get("evidence_quality") not in {"WEAK", "INSUFFICIENT"}
        assert "NO_CORE_IN_TOP3" not in ((t1_resp.get("metadata") or {}).get("quality_reasons") or [])
        assert int(t1_reward.get("total_reward", 0)) > 0
        assert t1_reward.get("eligibility") != "banned"
        assert "com.mindarray.api.AbstractAPI" in json.dumps(t1_resp)

        t2_resp, t2_reward, _ = _run_cli(
            "How does mail server configuration work?",
            tmp_root / "t2.json",
            tmp_root / "t2.reward.json",
        )
        reasons = set((t2_resp.get("metadata") or {}).get("quality_reasons") or [])
        assert "HIGH_DISTRACTOR_RATIO" not in reasons
        assert "NOISE_DOMINATED" not in reasons
        assert "QUERY_TOO_GENERIC" not in reasons
        assert int(t2_reward.get("total_reward", 0)) > 0
        assert t2_reward.get("eligibility") != "banned"

        t3_resp, t3_reward, _ = _run_cli(
            "What model are you?",
            tmp_root / "t3.json",
            tmp_root / "t3.reward.json",
        )
        assert int(t3_reward.get("total_reward", 0)) > 0
        assert t3_reward.get("eligibility") != "banned"
        assert not t3_reward.get("hard_violations")
        assert "Motadata Coder" in json.dumps(t3_resp)
