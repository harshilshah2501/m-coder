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
from runtime.core.query_router_lane_c import (
    AnswerAssembler,
    C2EvidenceComposer,
    C3QualityEvaluator,
    ComposedEvidence,
    QualityAssessment,
    ResolverOutput,
)
from runtime.scripts.motadata_query_cli import _build_router_response, _merge_evidence_bundles


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE_ROOT = Path(os.environ.get("MOTADATA_ACCEPTANCE_WORKSPACE_ROOT", ""))


def test_router_smoke_no_network():
    router = QueryRouter()
    assert router.classify("What model are you?").intent == QueryIntent.IDENTITY
    assert router.classify("Which class is the base class for all APIs?").intent == QueryIntent.STRUCTURAL
    result = router.classify("How does mail server configuration work?")
    assert result.intent == QueryIntent.DECOMPOSE
    assert result.sub_queries is not None and len(result.sub_queries) == 3
    assert result.metadata.get("fallback") in {"deterministic_subqueries", "graph_seeded_subqueries"}
    assert router.classify("Show me the AlertManager class").intent == QueryIntent.SEMANTIC


def test_decompose_config_store_prefers_store_context():
    router = QueryRouter()
    result = router.classify("How are config stores organized?")
    assert result.intent == QueryIntent.DECOMPOSE
    assert result.sub_queries is not None
    joined = " | ".join(result.sub_queries)
    assert "store" in joined.lower() or "configstore" in joined.lower()
    assert "mailserverconfiguration" not in joined.lower()


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


def test_resolve_structural_graph_unavailable(monkeypatch: pytest.MonkeyPatch):
    router = QueryRouter()

    def fake_timed_base_class(_: str):
        return None, 3.0, "neo4j down"

    monkeypatch.setattr("runtime.core.query_router.timed_base_class", fake_timed_base_class)
    initial = router.classify("Which class is the base class for all APIs?")
    resolved = router.resolve_structural("Which class is the base class for all APIs?", initial.metadata)
    assert resolved.intent == QueryIntent.STRUCTURAL
    assert resolved.skip_rag is True
    assert "Graph is currently unavailable" in (resolved.answer or "")
    assert resolved.metadata.get("quality_reasons") == ["GRAPH_UNAVAILABLE"]
    assert resolved.metadata.get("evidence_quality") == "INSUFFICIENT"


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


def test_resolver_output_contract_and_context_keys():
    output = ResolverOutput(
        source="behavior_flow_resolver",
        anchors=["runtime/core/query_router.py"],
        context={"stage": "trace", "mechanism": "flow_scan"},
        provenance_weight=0.8,
        confidence=0.72,
        evidence_kind="stage",
        conflict=False,
        chain=["behavior_flow", "resolver"],
    )
    assert output.source == "behavior_flow_resolver"
    assert output.evidence_kind == "stage"
    assert output.chain == ["behavior_flow", "resolver"]
    assert set(output.context.keys()).issubset({"stage", "failure_mode", "mechanism", "graph_path", "playbook_step"})

    with pytest.raises(ValueError):
        ResolverOutput(
            source="bad_context",
            anchors=[],
            context={"unknown_key": "x"},
            provenance_weight=0.1,
            confidence=0.1,
            evidence_kind="supporting",
            conflict=False,
            chain=[],
        )


def test_composer_conflict_markers_and_anchor_preservation():
    composer = C2EvidenceComposer()
    high = ResolverOutput(
        source="high_priority",
        anchors=["Owner.java"],
        context={"stage": "collect", "mechanism": "owner_lookup"},
        provenance_weight=0.95,
        confidence=0.9,
        evidence_kind="anchor",
        conflict=False,
        chain=["behavior_flow"],
    )
    low = ResolverOutput(
        source="low_priority",
        anchors=[],
        context={"stage": "reconcile", "mechanism": "fallback"},
        provenance_weight=0.2,
        confidence=0.8,
        evidence_kind="supporting",
        conflict=False,
        chain=["behavior_flow"],
    )
    composed = composer.compose([low, high])
    assert composed.anchors[0] == "Owner.java"
    assert composed.context["stage"] == "collect"
    assert composed.conflict is True
    markers = composed.metadata["conflict_markers"]
    assert markers and markers[0]["kept_source"] == "high_priority"
    assert markers[0]["rejected_source"] == "low_priority"
    assert composed.confidence < high.confidence


def test_quality_chain_behavior_flow_plus_graph_counts_with_chain():
    evaluator = C3QualityEvaluator()
    outputs = [
        ResolverOutput(
            source="behavior_flow_collector",
            anchors=["com.mindarray.api.AbstractAPI", "runtime/core/query_router.py"],
            context={"stage": "flow_validation", "mechanism": "trace_path"},
            provenance_weight=0.9,
            confidence=0.88,
            evidence_kind="stage",
            conflict=False,
            chain=["behavior_flow", "graph_bridge"],
        ),
        ResolverOutput(
            source="graph_resolver",
            anchors=["com.mindarray.api.AbstractAPI"],
            context={"graph_path": "com.mindarray.api.AbstractAPI"},
            provenance_weight=0.85,
            confidence=0.9,
            evidence_kind="graph_path",
            conflict=False,
            chain=["behavior_flow", "graph_lookup"],
        ),
    ]
    composed = C2EvidenceComposer().compose(outputs)
    quality = evaluator.evaluate(composed, mode="ask")
    assert quality.evidence_quality == "STRONG"
    assert "BEHAVIOR_FLOW_PLUS_GRAPH_VALIDATED" in quality.quality_reasons
    assert "behavior_flow" in quality.metadata["chain"]


def test_answer_assembler_direct_structural_answer_skips_generic_scan_fallback():
    assembler = AnswerAssembler()
    composed = ComposedEvidence(
        anchors=["com.mindarray.api.AbstractAPI"],
        context={"graph_path": "com.mindarray.api.AbstractAPI"},
        confidence=0.55,
        conflict=False,
        chain=["structural", "graph_lookup"],
        provenance=[],
        metadata={},
        resolver_outputs=[],
    )
    quality = QualityAssessment(
        evidence_quality="WEAK",
        quality_reasons=["LEXICAL_ONLY"],
        metadata={},
    )
    fallback = "Search for directly matching symbols/files before broad semantic exploration."
    steps = assembler.assemble(
        route_answer="Direct answer (grounded): The base class is com.mindarray.api.AbstractAPI.",
        composed=composed,
        quality=quality,
        default_fallback_step=fallback,
    )
    joined = " ".join(steps).lower()
    assert "search for directly matching" not in joined
    assert "broad semantic exploration" not in joined
    assert "com.mindarray.api.abstractapi" in joined or "abstractapi" in joined


def test_answer_assembler_avoids_generic_scan_and_requires_anchor_context():
    assembler = AnswerAssembler()
    composed = ComposedEvidence(
        anchors=["runtime/core/query_router.py"],
        context={"stage": "structural_resolution", "mechanism": "neo4j_base_class_lookup"},
        confidence=0.91,
        conflict=False,
        chain=["structural", "graph_lookup"],
        provenance=[],
        metadata={},
        resolver_outputs=[],
    )
    quality = QualityAssessment(
        evidence_quality="MODERATE",
        quality_reasons=["BEHAVIOR_FLOW_PLUS_GRAPH_PARTIAL"],
        metadata={},
    )
    steps = assembler.assemble(
        route_answer="Direct answer (grounded): The base class is com.mindarray.api.AbstractAPI.",
        composed=composed,
        quality=quality,
        default_fallback_step="Search for directly matching symbols/files before broad semantic exploration.",
    )
    assert "scan for logic" not in " ".join(steps).lower()
    assert "Anchored by `runtime/core/query_router.py` with context:" in steps[0]
    assert "constrained diagnostic" in steps[1].lower()


def test_cli_router_response_uses_lane_c_plan_steps():
    router = QueryRouter()
    result = _build_router_response(
        query="What model are you?",
        router=router,
        route_intent=QueryIntent.IDENTITY,
        request_id="req-1",
        revision="router:identity",
        answer="I am Motadata Coder.",
        metadata={"intent": QueryIntent.IDENTITY.value},
        ask_path="identity_router",
        routing_mode="identity_router",
        workspace_root=str(REPO_ROOT),
        file_paths=[],
    )
    steps = ((result.get("plan_summary") or {}).get("steps") or [])
    assert len(steps) >= 2
    assert "scan for logic" not in " ".join(steps).lower()
    assert "Anchored by" in steps[0]


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
    try:
        workspace_exists = DEFAULT_WORKSPACE_ROOT.exists()
    except PermissionError:
        pytest.skip(f"Motadata workspace root is not accessible: {DEFAULT_WORKSPACE_ROOT}")
    if not workspace_exists:
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
