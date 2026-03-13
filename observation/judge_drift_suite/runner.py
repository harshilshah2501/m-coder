"""
Suite runner — Judge Drift Regression Suite v1.1.

Loads case YAMLs, calls configurable Judge, normalizes verdicts, returns structured results only.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import yaml

from observation.judge_drift_suite.verdict_normalizer import normalize_verdict

_logger = logging.getLogger(__name__)

DEFAULT_JUDGE_VERSION = "1.0"
REQUIRED_KEYS = ("id", "phase", "stress_surface", "mutation_class", "input_prompt", "expected_verdict")
VALID_VERDICTS = ("PASS", "ESCALATE", "REFUSE")


def _log_structured(event: str, payload: dict[str, Any]) -> None:
    _logger.info("%s", {"event": event, **payload})


def _load_cases(cases_dir: Path) -> list[dict[str, Any]]:
    cases = []
    if not cases_dir.exists():
        return cases
    for path in sorted(cases_dir.glob("*.yaml")):
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                continue
            if all(data.get(k) is not None for k in REQUIRED_KEYS):
                if data.get("expected_verdict") in VALID_VERDICTS:
                    cases.append(data)
        except Exception:
            continue
    return cases


def run_suite(
    judge_fn: Callable[[str], str],
    cases_dir: Path | None = None,
    judge_version: str | None = None,
) -> dict[str, Any]:
    """
    Run all cases: load YAMLs, call judge_fn(prompt), normalize verdict, compare to expected.
    Returns { results: [...], summary: { total_cases, failures, distribution, judge_version } }.
    """
    if cases_dir is None:
        base = Path(__file__).resolve().parent
        cases_dir = base / "cases"
    version = judge_version or DEFAULT_JUDGE_VERSION
    cases = _load_cases(cases_dir)
    results = []
    dist_counts: dict[str, int] = {"PASS": 0, "ESCALATE": 0, "REFUSE": 0}
    for case in cases:
        prompt = case.get("input_prompt") or ""
        raw = judge_fn(prompt)
        actual = normalize_verdict(raw)
        expected = case.get("expected_verdict") or ""
        match = actual == expected
        results.append({
            "case_id": case.get("id", ""),
            "expected": expected,
            "actual": actual,
            "match": match,
            "judge_version": version,
            "phase": case.get("phase", ""),
            "guard": case.get("guard"),
            "stress_surface": case.get("stress_surface"),
            "mutation_class": case.get("mutation_class"),
        })
        if actual in dist_counts:
            dist_counts[actual] += 1
    total = len(results)
    failures = sum(1 for r in results if not r["match"])
    distribution = {}
    if total > 0:
        for k in ("PASS", "ESCALATE", "REFUSE"):
            distribution[k] = round(dist_counts[k] / total, 4)
    refusal_expected = [r for r in results if r["expected"] == "REFUSE"]
    if refusal_expected:
        refusal_correct = sum(1 for r in refusal_expected if r["actual"] == "REFUSE")
        refusal_accuracy = round(refusal_correct / len(refusal_expected), 4)
    else:
        refusal_accuracy = 1.0
    collision_cases = [r for r in results if r.get("phase") == "MIX"]
    if collision_cases:
        collision_correct = sum(1 for r in collision_cases if r["match"])
        collision_accuracy = round(collision_correct / len(collision_cases), 4)
    else:
        collision_accuracy = 1.0
    irreversible_pass_count = sum(
        1 for r in results
        if r["expected"] in ("REFUSE", "ESCALATE") and r["actual"] == "PASS"
    )
    summary = {
        "total_cases": total,
        "failures": failures,
        "distribution": distribution,
        "judge_version": version,
        "refusal_accuracy": refusal_accuracy,
        "collision_accuracy": collision_accuracy,
        "irreversible_pass_count": irreversible_pass_count,
    }
    _log_structured("run", {"total_cases": total, "failures": failures})
    return {"results": results, "summary": summary}
