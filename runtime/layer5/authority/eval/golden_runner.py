"""
Deterministic authority-layer evaluation (Phase 4).

Metrics (simple counters over golden cases):
- owner@1 / owner@3: primary owner file appears in entries rank 0 / within top 3
- distractor_error_rate: forbidden distractor file appears as if it were an owner in synthesis (always 0 target)
- authority_hit_rate: authority_resolution present when expected
- stale_authority_detected: authority_status == stale
- entry_trace_present: entry_trace key when required
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from runtime.ask_service.authority_synthesis import synthesize_authority_plan_steps
from runtime.context.contracts import (
    ContextBundle,
    ContextBundleLimits,
    ContextBundleProvenance,
    ContextItem,
)
from runtime.layer5.evidence.schema_validate import validate_evidence_bundle_dict


def _norm(p: str) -> str:
    return p.replace("\\", "/").strip().lower()


def _empty_bundle() -> ContextBundle:
    from datetime import datetime, timezone

    return ContextBundle(
        task_id="eval",
        revision="eval",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        items=[],
        limits=ContextBundleLimits(max_files=0, max_bytes=0, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="",
            selectors=["eval"],
            requested_files=[],
            symbol_hints=[],
        ),
    )


def _bundle_from_paths(paths: List[str]) -> ContextBundle:
    from datetime import datetime, timezone

    items: List[ContextItem] = []
    for p in paths:
        items.append(
            ContextItem(path=p, content="", byte_size=0, selection_reason="query_token_substring_anchor")
        )
    return ContextBundle(
        task_id="eval",
        revision="eval",
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        items=items,
        limits=ContextBundleLimits(max_files=len(items), max_bytes=0, truncated=False),
        provenance=ContextBundleProvenance(
            root_path="",
            selectors=["eval"],
            requested_files=paths,
            symbol_hints=[],
        ),
    )


@dataclass
class EvalReport:
    cases: int = 0
    owner_at_1: int = 0
    owner_at_3: int = 0
    authority_hits: int = 0
    authority_expected: int = 0
    stale_detected: int = 0
    stale_expected: int = 0
    entry_trace_ok: int = 0
    entry_trace_expected: int = 0
    distractor_violations: int = 0
    details: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "cases": self.cases,
            "owner_at_1_rate": self.owner_at_1 / max(1, self.cases),
            "owner_at_3_rate": self.owner_at_3 / max(1, self.cases),
            "authority_hit_rate": self.authority_hits / max(1, self.authority_expected or 1),
            "stale_authority_detection_rate": self.stale_detected / max(1, self.stale_expected or 1),
            "entry_trace_presence_rate": self.entry_trace_ok / max(1, self.entry_trace_expected or 1),
            "distractor_error_rate": self.distractor_violations / max(1, self.cases),
            "details": list(self.details),
        }


def evaluate_bundle_dict(
    bundle: Dict[str, Any],
    *,
    expect_authority: bool = False,
    expect_stale: bool = False,
    require_entry_trace: bool = False,
    query: str = "",
) -> Tuple[EvalReport, List[str]]:
    """Score one evidence bundle dict; returns report fragment and synthesis steps."""
    validate_evidence_bundle_dict(bundle)
    report = EvalReport()
    report.cases = 1

    entries = bundle.get("entries") or []
    paths = [str(e.get("relative_path") or "") for e in entries if isinstance(e, dict)]
    ar = bundle.get("authority_resolution")

    if expect_authority:
        report.authority_expected = 1
        if isinstance(ar, dict):
            report.authority_hits = 1

    po = (ar or {}).get("primary_owner") if isinstance(ar, dict) else None
    owner_file = str(po.get("file") or "") if isinstance(po, dict) else ""

    if owner_file and paths:
        no = _norm(owner_file)
        if _norm(paths[0]) == no:
            report.owner_at_1 = 1
        top3 = {_norm(p) for p in paths[:3]}
        if no in top3:
            report.owner_at_3 = 1

    if isinstance(ar, dict):
        if str(ar.get("authority_status") or "") == "stale":
            report.stale_detected = 1
        if expect_stale:
            report.stale_expected = 1
        et = ar.get("entry_trace")
        if require_entry_trace:
            report.entry_trace_expected = 1
            if isinstance(et, dict) and (et.get("path") or et.get("entry_point")):
                report.entry_trace_ok = 1

    b = _bundle_from_paths(paths)
    steps, meta = synthesize_authority_plan_steps(query, b, ar if isinstance(ar, dict) else None)
    text = " ".join(steps).lower()

    # Distractor guard: distractor path must not appear as co-owner / peer language
    if isinstance(ar, dict):
        for d in ar.get("forbidden_distractors") or []:
            if not isinstance(d, dict):
                continue
            df = str(d.get("file") or "")
            if not df:
                continue
            base = df.split("/")[-1].lower()
            # Disallow presenting as alternative owner
            bad_phrases = (
                "co-owner",
                "peer owner",
                "likely owner",
                "also likely",
                "alternative owner",
            )
            if base and any(p in text for p in bad_phrases) and base in text:
                report.distractor_violations += 1
                report.details.append(f"distractor_language_risk:{df}")

    return report, steps


def run_golden_cases(cases: List[Dict[str, Any]]) -> EvalReport:
    """Aggregate metrics over a list of case dicts with keys: bundle, expect_* , query."""
    agg = EvalReport()
    for c in cases:
        r, _ = evaluate_bundle_dict(
            c["bundle"],
            expect_authority=c.get("expect_authority", False),
            expect_stale=c.get("expect_stale", False),
            require_entry_trace=c.get("require_entry_trace", False),
            query=str(c.get("query") or ""),
        )
        agg.cases += r.cases
        agg.owner_at_1 += r.owner_at_1
        agg.owner_at_3 += r.owner_at_3
        agg.authority_hits += r.authority_hits
        agg.authority_expected += r.authority_expected
        agg.stale_detected += r.stale_detected
        agg.stale_expected += r.stale_expected
        agg.entry_trace_ok += r.entry_trace_ok
        agg.entry_trace_expected += r.entry_trace_expected
        agg.distractor_violations += r.distractor_violations
        agg.details.extend(r.details)
    return agg
