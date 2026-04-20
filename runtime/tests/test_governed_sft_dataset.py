from __future__ import annotations

import json
from pathlib import Path

from runtime.learning.governed_sft_dataset import (
    collect_events_from_files,
    extract_events_from_payload,
    filter_events_by_eligibility,
)


def _base_resp(*, request_id: str = "r1", quality: str = "WEAK") -> dict:
    return {
        "schema_version": "plan_only_response.v0.1",
        "request_id": request_id,
        "governance_posture": "PLAN_ONLY",
        "execution": False,
        "plan_summary": {"steps": ["Open foo and inspect."], "notes": []},
        "metadata": {"evidence_quality": quality, "quality_reasons": []},
        "evidence_first_meta": {"ask_path": "v1_evidence"},
    }


def test_extract_plain_ask_response_event():
    payload = _base_resp()
    out = extract_events_from_payload(payload, source_file="x.json")
    assert len(out) == 1
    ev = out[0]
    assert ev.source_variant == "single"
    assert ev.reward["eligibility"] in {"silver", "gold", "observational"}


def test_extract_assist_eval_prefers_candidate_when_improved():
    payload = {
        "request_id": "assist-1",
        "original_query": "Which class is base class for APIs?",
        "final_verdict": "improved",
        "path_a_baseline_original": _base_resp(request_id="assist-1", quality="WEAK"),
        "path_b_candidate_augmented": _base_resp(request_id="assist-1", quality="STRONG"),
    }
    out = extract_events_from_payload(payload, source_file="assist.json")
    assert len(out) == 1
    ev = out[0]
    assert ev.source_variant == "candidate"
    assert ev.assist_delta == "improved"


def test_collect_and_filter_events(tmp_path: Path):
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    p3 = tmp_path / "ignore.json"
    p1.write_text(json.dumps(_base_resp(request_id="a1", quality="STRONG")), encoding="utf-8")
    p2.write_text(
        json.dumps(
            {
                "request_id": "assist-2",
                "original_query": "How does alert correlation work?",
                "final_verdict": "degraded",
                "path_a_baseline_original": _base_resp(request_id="assist-2", quality="STRONG"),
                "path_b_candidate_augmented": _base_resp(request_id="assist-2", quality="WEAK"),
            }
        ),
        encoding="utf-8",
    )
    p3.write_text(json.dumps({"schema_version": "other"}), encoding="utf-8")

    events, stats = collect_events_from_files([p1, p2, p3])
    assert stats["input_files"] == 3
    assert stats["events_total"] == 2
    assert stats["skipped_files"] == 1

    gold_only = filter_events_by_eligibility(events, ["gold"])
    assert all(e.reward["eligibility"] == "gold" for e in gold_only)

