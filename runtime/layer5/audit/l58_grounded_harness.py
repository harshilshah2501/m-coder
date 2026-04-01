from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from runtime.layer5.audit.l58_dataset import GoldenCase, load_golden_cases, load_thresholds
from runtime.layer5.audit.l58_drift import DriftResult, evaluate_drifts
from runtime.layer5.audit.l58_evaluator import EvaluatedCase, PR6ProtectedMetrics, evaluate_cases
from runtime.layer5.audit.l58_perturbations import expand_cases_with_perturbations
from runtime.layer5.audit.l58_report import write_reports

_AUDIT_DIR = Path(__file__).resolve().parent
_FIXTURES_DIR = _AUDIT_DIR / "fixtures"
DEFAULT_GOLDEN = _FIXTURES_DIR / "l58_golden_queries.v1.json"
DEFAULT_THRESHOLDS = _FIXTURES_DIR / "l58_thresholds.v1.json"


@dataclass(frozen=True)
class L58HarnessResult:
    cases: List[EvaluatedCase]
    pr6: PR6ProtectedMetrics
    drift: DriftResult
    report_json: Path
    report_md: Path

    @property
    def passed(self) -> bool:
        return self.drift.passed


def _select_cases(cases: List[GoldenCase], suite: str) -> List[GoldenCase]:
    if suite == "full":
        return cases
    # smoke: keep base + no-match + one sentinel per flow
    by_flow = {}
    smoke: List[GoldenCase] = []
    for c in sorted(cases, key=lambda x: x.id):
        if c.perturbation.kind == "base":
            by_flow.setdefault(c.flow_type, c)
        if c.expectations.expect_no_match_honesty and c not in smoke:
            smoke.append(c)
    smoke.extend(by_flow.values())
    dedup = {c.id: c for c in smoke}
    return [dedup[k] for k in sorted(dedup.keys())]


def run_l58_harness(
    output_dir: Path,
    suite: str = "smoke",
    include_generated_perturbations: bool = True,
    dataset_path: Path = DEFAULT_GOLDEN,
    thresholds_path: Path = DEFAULT_THRESHOLDS,
) -> L58HarnessResult:
    cases = load_golden_cases(dataset_path)
    expanded = expand_cases_with_perturbations(cases, include_generated=include_generated_perturbations)
    selected = _select_cases(expanded, suite=suite)
    evaluated, pr6 = evaluate_cases(selected)
    thresholds = load_thresholds(thresholds_path)
    drift = evaluate_drifts(evaluated, pr6, thresholds)
    report_json, report_md = write_reports(evaluated, pr6, drift, output_dir=output_dir)
    return L58HarnessResult(
        cases=evaluated,
        pr6=pr6,
        drift=drift,
        report_json=report_json,
        report_md=report_md,
    )
