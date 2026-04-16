"""
Phase 4 — Plan-Gate consumption, answer anchoring, distractor synthesis guard, eval wiring.
"""

from __future__ import annotations

from pathlib import Path

from runtime.ask_service.authority_synthesis import synthesize_authority_plan_steps
from runtime.ask_service.planner import PlanOnlyPlanner
from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)
from runtime.layer5.authority.authority_evidence import build_authority_resolution, match_concepts_for_query
from runtime.layer5.authority.eval.golden_runner import evaluate_bundle_dict
from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.evidence.schema_validate import validate_evidence_bundle_dict


REG = Path(__file__).resolve().parents[1] / "layer5" / "authority" / "product_authority_registry.yaml"


def _ctx(paths: list[str]) -> ContextBundle:
    from datetime import datetime, timezone

    items = [
        ContextItem(path=p, content="", byte_size=0, selection_reason="query_token_substring_anchor")
        for p in paths
    ]
    return ContextBundle(
        task_id="t",
        revision="t",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        items=items,
        limits=ContextBundleLimits(max_files=len(items), max_bytes=0, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="",
            selectors=["test"],
            requested_files=paths,
            symbol_hints=[],
        ),
    )


def test_schema_backward_compatible_golden_evidence():
    from runtime.tests.test_ask_v1_ingest import _load_golden_evidence

    ev = _load_golden_evidence()
    validate_evidence_bundle_dict(ev)


def test_anchored_synthesis_names_owner_and_control_flow():
    registry = load_registry(REG)
    ar = build_authority_resolution("incident deduplication", registry, None)
    assert ar is not None
    po = ar["primary_owner"]
    assert "DependencyQueryProcessor" in po["class"]
    steps, meta = synthesize_authority_plan_steps(
        "incident deduplication",
        _ctx([po["file"]]),
        ar,
    )
    blob = " ".join(steps).lower()
    assert po["class"].lower() in blob
    assert po["file"].lower() in blob
    assert "control flow" in blob or "dependencyqueryprocessor" in blob or "entry" in blob
    assert meta.get("anchor_mode") in ("anchored", "weak_or_stale")


def test_stale_candidate_uncertainty_language():
    registry = load_registry(REG)
    ar = build_authority_resolution("incident deduplication", registry, None)
    assert ar
    ar = dict(ar)
    ar["authority_status"] = "stale_candidate"
    ar["authority_confidence"] = "weak"
    steps, meta = synthesize_authority_plan_steps("q", _ctx([]), ar)
    text = " ".join(steps).lower()
    assert "provisional" in text or "stale_candidate" in text or "uncertain" in text or "verify" in text
    assert meta.get("uncertainty") is True


def test_distractor_high_rank_not_peer_owner():
    """Distractor may rank #2 lexically; synthesis must not present it as owner peer."""
    registry = load_registry(REG)
    ar = build_authority_resolution("incident deduplication", registry, None)
    assert ar
    distractor = "src/main/java/com/mindarray/aiops/AvailabilityCorrelationEngine.java"
    owner = ar["primary_owner"]["file"]
    paths = [distractor, owner]
    steps, meta = synthesize_authority_plan_steps("incident deduplication", _ctx(paths), ar)
    text = " ".join(steps).lower()
    assert "distractor" in text or "not owner" in text or "excluded" in text
    assert "peer owner" not in text
    assert "co-owner" not in text
    assert meta.get("distractor_suppressed") is True


def test_compound_query_separate_blocks():
    registry = load_registry(REG)
    mm = match_concepts_for_query("incident deduplication and alert correlation", registry)
    assert len(mm) >= 2
    ar = build_authority_resolution("incident deduplication and alert correlation", registry, None)
    assert ar and ar.get("compound") is True
    steps, _ = synthesize_authority_plan_steps(
        "incident deduplication and alert correlation",
        _ctx([]),
        ar,
    )
    text = " ".join(steps)
    assert "Additional concept" in text or "alert_correlation" in text.lower()


def test_planner_backward_compat_without_authority():
    p = PlanOnlyPlanner()
    b = _ctx(["a/b.py"])
    ps = p.plan(query="hello", bundle=b, authority_resolution=None)
    assert len(ps.steps) >= 1
    assert any("open" in s.lower() or "search" in s.lower() for s in ps.steps)


def test_planner_uses_authority_when_present():
    registry = load_registry(REG)
    ar = build_authority_resolution("alert correlation", registry, None)
    assert ar
    p = PlanOnlyPlanner()
    ps = p.plan(query="alert correlation", bundle=_ctx([ar["primary_owner"]["file"]]), authority_resolution=ar)
    assert any("Primary implementation owner" in s for s in ps.steps)


def test_alert_correlation_owner_method_is_schema_valid_when_present():
    """When YAML includes primary_owner.method, evidence JSON keeps it as a non-empty string."""
    registry = load_registry(REG)
    ar = build_authority_resolution("alert correlation", registry, None)
    assert ar is not None
    po = ar.get("primary_owner") or {}
    assert isinstance(po.get("method"), str)
    assert bool(str(po.get("method")).strip())
    for mc in ar.get("matched_concepts") or []:
        mpo = mc.get("primary_owner") or {}
        if "method" in mpo:
            assert isinstance(mpo.get("method"), str)
            assert bool(str(mpo.get("method")).strip())
    bundle = {
        "provisional": False,
        "schema_hint": "layer5.evidence_bundle.v1",
        "query_raw": "alert correlation",
        "query_tokens": ["alert", "correlation"],
        "top_k": 2,
        "index_schema_version": "layer5.file_index.v1",
        "workspace_identity_hash": "h",
        "canonical_root": "/",
        "a5_authority_note": (
            "Candidate order and retrieval_score come from A5 lexical retrieval only; "
            "A6 must not rescore or reorder based on snippets."
        ),
        "entries": [
            {
                "provisional": False,
                "rank": 0,
                "relative_path": ar["primary_owner"]["file"],
                "retrieval_score": 1,
                "retrieval_breakdown": {"path_substrings": 1, "basename_substrings": 0, "content_substrings": 0},
                "snippet": {
                    "text": "",
                    "start_line": 1,
                    "end_line": 1,
                    "start_byte_utf8": 0,
                    "end_byte_utf8": 0,
                    "anchor_line": 1,
                    "matched_tokens": [],
                    "selection_reason": "no_query_tokens_file_start",
                    "truncated_by_max_bytes": False,
                },
            }
        ],
        "authority_resolution": ar,
    }
    validate_evidence_bundle_dict(bundle)


def test_eval_runner_smoke():
    registry = load_registry(REG)
    ar = build_authority_resolution("incident deduplication", registry, None)
    bundle = {
        "provisional": False,
        "schema_hint": "layer5.evidence_bundle.v1",
        "query_raw": "x",
        "query_tokens": ["x"],
        "top_k": 2,
        "index_schema_version": "layer5.file_index.v1",
        "workspace_identity_hash": "",
        "canonical_root": "",
        "a5_authority_note": (
            "Candidate order and retrieval_score come from A5 lexical retrieval only; "
            "A6 must not rescore or reorder based on snippets."
        ),
        "entries": [
            {
                "provisional": False,
                "rank": 0,
                "relative_path": ar["primary_owner"]["file"],
                "retrieval_score": 1,
                "retrieval_breakdown": {"path_substrings": 1, "basename_substrings": 0, "content_substrings": 0},
                "snippet": {
                    "text": "",
                    "start_line": 1,
                    "end_line": 1,
                    "start_byte_utf8": 0,
                    "end_byte_utf8": 0,
                    "anchor_line": 1,
                    "matched_tokens": [],
                    "selection_reason": "no_query_tokens_file_start",
                    "truncated_by_max_bytes": False,
                },
            }
        ],
        "authority_resolution": ar,
    }
    r, steps = evaluate_bundle_dict(bundle, expect_authority=True, query="incident deduplication")
    assert r.owner_at_1 == 1
    assert steps


def test_feature_flag_off_preserves_lexical_order_in_enhancer():
    """Phase 3 contract: reranking OFF keeps lexical hit order (sanity for Phase 4)."""
    from runtime.layer5.authority.ranking_config import RankingConfig
    from runtime.layer5.authority.retrieval_integration import AuthorityRetrievalEnhancer
    from runtime.layer5.authority.registry_loader import load_registry
    from runtime.layer5.retrieval.models import RetrievalHit, RetrievalResult

    reg = load_registry(REG)
    enhancer = AuthorityRetrievalEnhancer(reg, None, RankingConfig(enable_authority_reranking=False))
    r = RetrievalResult(
        query_raw="test",
        query_tokens=("test",),
        top_k=2,
        hits=(
            RetrievalHit("a.java", 10, {"path_substrings": 10, "basename_substrings": 0, "content_substrings": 0}),
            RetrievalHit("b.java", 5, {"path_substrings": 5, "basename_substrings": 0, "content_substrings": 0}),
        ),
        index_schema_version="x",
        workspace_identity_hash="y",
    )
    ranked, ctx = enhancer.enhance(r, return_diagnostics=True)
    assert ranked[0].file_path == "a.java"
    assert ctx is None
