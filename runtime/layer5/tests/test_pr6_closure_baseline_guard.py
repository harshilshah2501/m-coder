from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, classify_file, retrieve_lexical
from runtime.layer5.workspace.identity import WorkspaceIdentity


_LAYER5 = Path(__file__).resolve().parents[1]
_FIX_MANDATORY = _LAYER5 / "retrieval" / "fixtures" / "pr6_mandatory_anchor_debug_queries.v1.json"
_FIX_AMBIG = _LAYER5 / "retrieval" / "fixtures" / "pr6_ambiguous_debug_queries.v1.json"
_REQUIRED_DIAG_FIELDS = {
    "content",
    "code_intent",
    "owner_evidence_score",
    "direct_owner_alignment",
    "basename_specificity",
    "support_file_demotion",
    "generic_facade_content_trimmed",
    "topic_focus_supporting_content_trimmed",
    "generic_integration_demotion",
    "ingestion_log_parser_demotion",
    "duplicate_incident_core_boost",
    "total",
}


def _resolve_real_repo_root() -> Path:
    env = (os.environ.get("PR6_AIOPS_ROOT") or os.environ.get("MOTADATA_AIOPS_REPO_ROOT") or "").strip()
    if not env:
        pytest.skip("PR6 closure guard requires PR6_AIOPS_ROOT or MOTADATA_AIOPS_REPO_ROOT.")
    p = Path(env).resolve()
    if not p.is_dir():
        pytest.skip(f"PR6 closure guard root missing: {p}")
    return p


def _identity(root: Path) -> WorkspaceIdentity:
    root_s = str(root.resolve())
    return WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=False,
    )


def _load_queries() -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for label, path in (("mandatory", _FIX_MANDATORY), ("ambiguous", _FIX_AMBIG)):
        data = json.loads(path.read_text(encoding="utf-8"))
        for fixture in data["fixtures"]:
            row = dict(fixture)
            row["_fixture_group"] = label
            out.append(row)
    return out


def _first_anchor_rank(paths: List[str], anchors: List[str]) -> Optional[int]:
    aset = set(anchors)
    for i, p in enumerate(paths):
        if p in aset:
            return i + 1
    return None


def _noise_ratio_top5(paths: List[str]) -> float:
    top = paths[:5]
    if not top:
        return 0.0
    noise = sum(
        1
        for p in top
        if classify_file(p).file_class in {"tests", "logs", "vendor_static", "generated_metrics_data"}
    )
    return noise / len(top)


def test_pr6_closure_baseline_metrics_and_diagnostics() -> None:
    root = _resolve_real_repo_root()
    idx = build_file_index(_identity(root))
    cfg = LexicalRetrievalConfig(include_score_diagnostics=True)
    queries = _load_queries()

    top1_hits = 0
    top3_hits = 0
    first_ranks: List[int] = []
    noise_ratios: List[float] = []

    for q in queries:
        qid = str(q["id"])
        query = str(q["query"])
        anchors = [str(x) for x in q["expected_anchor_paths"]]
        top_k = int(q["required_top_k"])
        result = retrieve_lexical(idx, query, top_k=top_k, config=cfg)
        paths = [h.relative_path for h in result.hits]

        fr = _first_anchor_rank(paths, anchors)
        assert fr is not None, f"{qid}: no anchor found in top-k"
        assert fr == 1, f"{qid}: first relevant rank regressed to {fr}"
        first_ranks.append(fr)

        if paths and paths[0] in set(anchors):
            top1_hits += 1
        if any(p in set(anchors) for p in paths[:3]):
            top3_hits += 1

        nr = _noise_ratio_top5(paths)
        noise_ratios.append(nr)
        assert nr == 0.0, f"{qid}: noise dominance regressed to {nr:.2f}"

        assert result.hits, f"{qid}: empty retrieval hits"
        d = result.hits[0].diagnostics or {}
        missing = sorted(_REQUIRED_DIAG_FIELDS.difference(d.keys()))
        assert not missing, f"{qid}: missing diagnostics fields {missing}"

    n = len(queries)
    assert top1_hits == n, f"top-1 regressed: {top1_hits}/{n}"
    assert top3_hits == n, f"top-3 regressed: {top3_hits}/{n}"
    assert abs((sum(first_ranks) / n) - 1.0) < 1e-9
    assert abs((sum(noise_ratios) / n) - 0.0) < 1e-9
