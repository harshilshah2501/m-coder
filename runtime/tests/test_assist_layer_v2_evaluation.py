from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from runtime.assist_layer.evaluation.batch_runner import run_assist_eval_batch
from runtime.assist_layer.evaluation.evaluator import evaluate_assist_v2
from runtime.assist_layer.evaluation.policy import generate_confidence_policy
from runtime.assist_layer.evaluation.scorer import score_comparison


def _mk_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()
    (repo_root / "src" / "retry.py").write_text("def retrieve_config():\n    return 'ok'\n", encoding="utf-8")
    (repo_root / "README.md").write_text("retry config notes\n", encoding="utf-8")
    return repo_root


def _base_ask_request(repo_root: Path, query: str) -> dict:
    return {
        "schema_version": "ask_request.v0.1",
        "request_id": "assist-v2-eval-test",
        "timestamp_utc": "2026-04-10T12:00:00Z",
        "repo_root": str(repo_root),
        "revision": "test-rev",
        "query": query,
        "task_type": "general",
        "selected_file": "src/retry.py",
        "client_context": {"diagnostics_labels": ["eval"]},
        "trace_id": "trace-assist-v2-eval-test",
    }


def test_identical_query_noop_verdict_same(tmp_path: Path):
    repo_root = _mk_repo(tmp_path)
    req = _base_ask_request(repo_root, "Where is retry logic implemented?")

    out = evaluate_assist_v2(req, output_root=tmp_path / "artifacts", run_id="noop", persist_artifact=True)

    assert out["final_verdict"] == "same"
    assert out["comparison"]["evidence_quality"]["exact_match"] is True
    artifact = Path(out["artifact_path"])
    assert artifact.exists()
    loaded = json.loads(artifact.read_text(encoding="utf-8"))
    assert loaded["run_id"] == "noop"


def test_safe_transform_verdict_same_or_improved(tmp_path: Path):
    repo_root = _mk_repo(tmp_path)
    req = _base_ask_request(repo_root, "Where   is retrive cfg??")

    out = evaluate_assist_v2(req, output_root=tmp_path / "artifacts", run_id="tx", persist_artifact=False)

    assert out["assist_metadata"]["transform_codes_applied"]
    assert out["final_verdict"] in {"same", "improved", "degraded_minor", "degraded_major"}


def test_forced_mismatch_detects_degraded():
    comparison = {
        "files": {
            "baseline_count": 3,
            "candidate_count": 2,
            "overlap_ratio": 0.1,
            "exact_match": False,
        },
        "selectors_used": {
            "baseline_count": 2,
            "candidate_count": 1,
            "overlap_ratio": 0.2,
            "exact_match": False,
        },
        "plan_steps": {
            "baseline_count": 4,
            "candidate_count": 3,
            "exact_match": False,
        },
        "evidence_quality": {
            "baseline": "STRONG",
            "candidate": "WEAK",
            "exact_match": False,
        },
        "core_flags": {
            "governance_posture_equal": True,
            "execution_equal": True,
            "routing_mode_equal": True,
        },
    }

    verdict, reasons = score_comparison(comparison)
    assert verdict == "degraded_major"
    assert reasons


def test_severity_classification_same_and_minor_and_major():
    improved_cmp = {
        "files": {"overlap_ratio": 0.9, "exact_match": False},
        "selectors_used": {"exact_match": True},
        "plan_steps": {"exact_match": False, "normalized_equal": True},
        "evidence_quality": {"baseline": "WEAK", "candidate": "STRONG"},
        "core_flags": {
            "governance_posture_equal": True,
            "execution_equal": True,
            "routing_mode_equal": True,
        },
        "output_equivalence": {"key_fields_equal": False},
    }
    v_improved, _ = score_comparison(improved_cmp)
    assert v_improved == "improved"

    same_cmp = {
        "files": {"overlap_ratio": 1.0, "exact_match": True},
        "selectors_used": {"exact_match": True},
        "plan_steps": {"exact_match": True, "normalized_equal": True},
        "evidence_quality": {"baseline": "WEAK", "candidate": "WEAK"},
        "core_flags": {
            "governance_posture_equal": True,
            "execution_equal": True,
            "routing_mode_equal": True,
        },
        "output_equivalence": {"key_fields_equal": True},
    }
    v_same, _ = score_comparison(same_cmp)
    assert v_same == "same"

    minor_cmp = {
        "files": {"overlap_ratio": 0.3, "exact_match": False},
        "selectors_used": {"exact_match": True},
        "plan_steps": {"exact_match": False, "normalized_equal": True},
        "evidence_quality": {"baseline": "WEAK", "candidate": "WEAK"},
        "core_flags": {
            "governance_posture_equal": True,
            "execution_equal": True,
            "routing_mode_equal": True,
        },
        "output_equivalence": {"key_fields_equal": True},
    }
    v_minor, _ = score_comparison(minor_cmp)
    assert v_minor == "degraded_minor"

    major_cmp = {
        "files": {"overlap_ratio": 0.8, "exact_match": False},
        "selectors_used": {"exact_match": True},
        "plan_steps": {"exact_match": True, "normalized_equal": True},
        "evidence_quality": {"baseline": "STRONG", "candidate": "WEAK"},
        "core_flags": {
            "governance_posture_equal": True,
            "execution_equal": True,
            "routing_mode_equal": True,
        },
        "output_equivalence": {"key_fields_equal": True},
    }
    v_major, _ = score_comparison(major_cmp)
    assert v_major == "degraded_major"


def test_shadow_only_no_http_dependency(tmp_path: Path, monkeypatch):
    repo_root = _mk_repo(tmp_path)
    req = _base_ask_request(repo_root, "Where is retry logic implemented?")

    def _blocked(*_args, **_kwargs):
        raise RuntimeError("HTTP should not be used")

    monkeypatch.setattr(urllib.request, "urlopen", _blocked)
    out = evaluate_assist_v2(req, output_root=tmp_path / "artifacts", run_id="shadow-only", persist_artifact=False)
    assert out["final_verdict"] in {"same", "improved", "degraded_minor", "degraded_major"}


def test_batch_runner_writes_summary_and_policy(tmp_path: Path):
    repo_root = _mk_repo(tmp_path)
    dataset = {
        "schema_version": "assist_eval_dataset.v1",
        "entries": [
            {"id": "d1", "category": "clean_control", "query": "Where is retry logic implemented?", "note": "clean"},
            {"id": "d2", "category": "typo_normalization", "query": "Where   is retrive cfg??", "note": "typo+abbr"},
            {"id": "d3", "category": "ambiguous_query", "query": "engine", "note": "ambiguous"},
        ],
    }
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")

    out = run_assist_eval_batch(
        repo_root=str(repo_root),
        revision="test-rev",
        dataset_path=dataset_path,
        output_root=tmp_path / "batch_artifacts",
        run_prefix="t",
    )

    summary_path = Path(out["summary_path"])
    policy_path = Path(out["policy_path"])
    assert summary_path.exists()
    assert policy_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["total_runs"] == 3
    assert "degraded_minor_count" in summary
    assert "degraded_major_count" in summary
    assert summary["counts_by_transform_code"]
    assert summary["counts_by_query_category"]


def test_policy_generation_deterministic_shape():
    summary = {
        "total_runs": 10,
        "counts_by_transform_code": {
            "normalize_typo_light": {"total": 5, "improved": 2, "same": 3, "degraded_minor": 0, "degraded_major": 0},
            "expand_static_abbreviation": {"total": 5, "improved": 0, "same": 2, "degraded_minor": 2, "degraded_major": 1},
        },
        "counts_by_query_category": {
            "garbage_or_fragment": {"total": 4, "improved": 0, "same": 1, "degraded_minor": 1, "degraded_major": 2}
        },
    }
    runs = [
        {"final_verdict": "same"},
        {"final_verdict": "improved"},
        {"final_verdict": "degraded_minor"},
        {"final_verdict": "degraded_major"},
    ]
    policy = generate_confidence_policy(summary, runs)

    assert policy["schema_version"] == "assist_confidence_policy.v1"
    assert "safe_transforms" in policy
    assert "caution_transforms" in policy
    assert "blocked_transforms_or_conditions" in policy
    assert "degradation_thresholds" in policy
