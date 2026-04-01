from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from runtime.layer5.audit.l58_dataset import GoldenCase
from runtime.layer5.index import build_file_index
from runtime.layer5.retrieval import LexicalRetrievalConfig, classify_file, retrieve_lexical
from runtime.layer5.retrieval.quality_gate import assess_evidence_quality
from runtime.layer5.workspace.identity import WorkspaceIdentity

_LAYER5_DIR = Path(__file__).resolve().parents[1]
_PR6_FIX_MANDATORY = _LAYER5_DIR / "retrieval" / "fixtures" / "pr6_mandatory_anchor_debug_queries.v1.json"
_PR6_FIX_AMBIG = _LAYER5_DIR / "retrieval" / "fixtures" / "pr6_ambiguous_debug_queries.v1.json"
_BUNDLED_ROOT = _LAYER5_DIR / "audit" / "fixture_noisy_aiops_workspace"

NOISE_CLASS_TO_BUCKET = {
    "logs": "logs",
    "tests": "test",
    "vendor_static": "vendor",
    "generated_metrics_data": "generated",
}
NOISE_BUCKETS = frozenset({"logs", "test", "vendor", "generated", "metrics", "docs_non_code"})


@dataclass(frozen=True)
class PR6ProtectedMetrics:
    total: int
    top1_hits: int
    top3_hits: int
    mean_first_relevant_rank: float
    mean_noise_dominance_top5: float
    hard_failures: List[str]


@dataclass(frozen=True)
class EvaluatedCase:
    case_id: str
    flow_type: str
    query: str
    ranked_paths: List[str]
    top1_owner_match: bool
    top3_anchor_hit: bool
    first_relevant_rank: Optional[int]
    noise_dominance_top5: float
    code_ratio_topk: float
    predicted_evidence_class: str
    evidence_class_match: bool
    no_match_honesty_ok: bool
    latency_ms: float
    hard_fail_reasons: List[str]
    warning_reasons: List[str]


def _resolve_workspace_root() -> Path:
    env = (os.environ.get("L58_AIOPS_ROOT") or os.environ.get("PR6_AIOPS_ROOT") or os.environ.get("MOTADATA_AIOPS_REPO_ROOT") or "").strip()
    if env:
        p = Path(env).resolve()
        if p.is_dir():
            return p
    return _BUNDLED_ROOT.resolve()


def _identity(root: Path) -> WorkspaceIdentity:
    root_s = str(root.resolve())
    return WorkspaceIdentity(
        canonical_root=root_s,
        identity_hash=WorkspaceIdentity.compute_identity_hash(root_s),
        original_input=root_s,
        path_type="posix",
        is_git_repo=False,
    )


def _first_relevant_rank(paths: Sequence[str], anchors: Sequence[str]) -> Optional[int]:
    aset = set(anchors)
    for i, p in enumerate(paths):
        if p in aset:
            return i + 1
    return None


def _noise_bucket_for_path(path: str) -> Optional[str]:
    cls = classify_file(path).file_class
    if cls in NOISE_CLASS_TO_BUCKET:
        return NOISE_CLASS_TO_BUCKET[cls]
    lowered = path.lower()
    if "/docs/" in lowered or lowered.endswith(".md"):
        return "docs_non_code"
    if "/metrics/" in lowered:
        return "metrics"
    return None


def _noise_ratio_top5(paths: Sequence[str]) -> float:
    top = list(paths[:5])
    if not top:
        return 0.0
    noise = sum(1 for p in top if _noise_bucket_for_path(p) in NOISE_BUCKETS)
    return noise / len(top)


def _code_ratio(paths: Sequence[str]) -> float:
    if not paths:
        return 0.0
    code_count = sum(
        1
        for p in paths
        if classify_file(p).file_class in {"core_aiops_code", "supporting_prod_code"}
    )
    return code_count / len(paths)


def _evidence_match(case: GoldenCase, predicted: str) -> bool:
    accepted = set(case.expected_evidence_class.accepted())
    if case.expectations.expect_no_match_honesty:
        return predicted == "NO_MATCH"
    # strict primary for critical STRONG cases
    if case.expected_evidence_class.primary == "STRONG" and case.expectations.must_hit_top1_owner:
        return predicted == "STRONG"
    return predicted in accepted


def evaluate_cases(cases: Iterable[GoldenCase], top_k: int = 8) -> tuple[List[EvaluatedCase], PR6ProtectedMetrics]:
    root = _resolve_workspace_root()
    idx = build_file_index(_identity(root))
    cfg = LexicalRetrievalConfig(include_score_diagnostics=True)

    evaluated: List[EvaluatedCase] = []
    for case in cases:
        start = time.perf_counter()
        result = retrieve_lexical(idx, case.query, top_k=top_k, config=cfg)
        elapsed_ms = (time.perf_counter() - start) * 1000
        ranked = [h.relative_path for h in result.hits]
        top1 = bool(ranked) and ranked[0] == case.expected_owner
        top3 = any(p in set(case.acceptable_anchors) for p in ranked[:3])
        first_rank = _first_relevant_rank(ranked, case.acceptable_anchors)
        noise_ratio = _noise_ratio_top5(ranked)
        code_ratio = _code_ratio(ranked)
        predicted = assess_evidence_quality(case.query, ranked).evidence_quality
        evidence_ok = _evidence_match(case, predicted)
        no_match_ok = (not case.expectations.expect_no_match_honesty) or (predicted == "NO_MATCH")

        hard: List[str] = []
        warn: List[str] = []
        if case.expectations.must_hit_top1_owner and not top1:
            hard.append("owner_miss_top1")
        if case.expectations.must_hit_top3_anchor and not top3:
            hard.append("anchor_miss_top3")
        if first_rank is None or first_rank > case.expectations.max_first_relevant_rank:
            hard.append("first_relevant_rank_regression")
        if noise_ratio > case.expectations.max_noise_dominance_top5:
            hard.append("noise_dominance_regression")
        if code_ratio < case.expectations.min_code_ratio_topk:
            warn.append("low_code_ratio")
        if not evidence_ok:
            hard.append("evidence_drift")
        if not no_match_ok:
            hard.append("no_match_honesty_failure")

        evaluated.append(
            EvaluatedCase(
                case_id=case.id,
                flow_type=case.flow_type,
                query=case.query,
                ranked_paths=ranked,
                top1_owner_match=top1,
                top3_anchor_hit=top3,
                first_relevant_rank=first_rank,
                noise_dominance_top5=noise_ratio,
                code_ratio_topk=code_ratio,
                predicted_evidence_class=predicted,
                evidence_class_match=evidence_ok,
                no_match_honesty_ok=no_match_ok,
                latency_ms=elapsed_ms,
                hard_fail_reasons=hard,
                warning_reasons=warn,
            )
        )

    return evaluated, evaluate_pr6_protected_subset(idx, cfg)


def _load_pr6_fixtures() -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for path in (_PR6_FIX_MANDATORY, _PR6_FIX_AMBIG):
        data = json.loads(path.read_text(encoding="utf-8"))
        out.extend(data["fixtures"])
    return out


def evaluate_pr6_protected_subset(index, cfg: LexicalRetrievalConfig) -> PR6ProtectedMetrics:
    fixtures = _load_pr6_fixtures()
    top1 = 0
    top3 = 0
    first_ranks: List[int] = []
    noise_ratios: List[float] = []
    failures: List[str] = []
    for row in fixtures:
        qid = str(row["id"])
        anchors = [str(x) for x in row["expected_anchor_paths"]]
        top_k = int(row["required_top_k"])
        result = retrieve_lexical(index, str(row["query"]), top_k=top_k, config=cfg)
        paths = [h.relative_path for h in result.hits]
        fr = _first_relevant_rank(paths, anchors)
        if fr is None:
            failures.append(f"{qid}:anchor_missing")
            fr = top_k + 1
        first_ranks.append(fr)
        if paths and paths[0] in set(anchors):
            top1 += 1
        if any(p in set(anchors) for p in paths[:3]):
            top3 += 1
        nr = _noise_ratio_top5(paths)
        noise_ratios.append(nr)
        if nr > 0.0:
            failures.append(f"{qid}:noise_nonzero")
        if fr != 1:
            failures.append(f"{qid}:first_rank_{fr}")

    n = len(fixtures)
    mean_rank = sum(first_ranks) / max(1, n)
    mean_noise = sum(noise_ratios) / max(1, n)
    if top1 != n:
        failures.append(f"pr6_top1_{top1}_of_{n}")
    if top3 != n:
        failures.append(f"pr6_top3_{top3}_of_{n}")
    if abs(mean_rank - 1.0) > 1e-9:
        failures.append(f"pr6_mean_rank_{mean_rank:.2f}")
    if abs(mean_noise - 0.0) > 1e-9:
        failures.append(f"pr6_mean_noise_{mean_noise:.2f}")
    return PR6ProtectedMetrics(
        total=n,
        top1_hits=top1,
        top3_hits=top3,
        mean_first_relevant_rank=mean_rank,
        mean_noise_dominance_top5=mean_noise,
        hard_failures=sorted(set(failures)),
    )
