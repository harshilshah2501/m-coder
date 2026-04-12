from __future__ import annotations

from runtime.layer5.evidence.usefulness_metrics import bundle_usefulness_metrics


def test_bundle_usefulness_metrics_empty():
    assert bundle_usefulness_metrics([])["entry_count"] == 0
    assert bundle_usefulness_metrics("bad")["entry_count"] == 0  # type: ignore[arg-type]


def test_bundle_usefulness_metrics_scores_and_anchors():
    entries = [
        {
            "rank": 1,
            "relative_path": "logs/a.log",
            "retrieval_score": 3,
            "snippet": {"selection_reason": "no_query_token_in_body_file_start"},
        },
        {
            "rank": 0,
            "relative_path": "src/main/java/com/mindarray/aiops/Foo.java",
            "retrieval_score": 9,
            "snippet": {"selection_reason": "query_token_substring_anchor"},
        },
    ]
    m = bundle_usefulness_metrics(entries)
    assert m["entry_count"] == 2
    assert m["top1_retrieval_score"] == 9
    assert m["retrieval_score_spread"] == 6
    assert m["retrieval_score_sum"] == 12
    assert m["snippet_anchor_hits"] == 1
    assert m["snippet_non_anchor_hits"] == 1
    assert m["noise_class_entry_count"] >= 1
    assert "header_anchor_rate" in m and "domain_anchor_rate" in m
