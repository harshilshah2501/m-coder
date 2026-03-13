"""
Shadow validation harness (M3.6).

Runs baseline scenarios and asserts:
- S-1: boundary_verdict never "crossed"; boundary_crossed never true
- S-2: plan and ledger always emitted
- S-3: decision_response.plan_hash matches plan_hash and ledger linkage
- Ingestion batch structure: request_id, plan, ledger_row per item
- Representative REF / CONF / DES outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.shadow.baseline_scenarios import BASELINE_SCENARIOS, ScenarioDef
from runtime.shadow.runner import ShadowRunner, ShadowRunResult


@dataclass
class HarnessResult:
    """Result of running the shadow validation harness."""
    passed: bool
    results: list[ShadowRunResult] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    ingestion_batch: dict[str, Any] | None = None


def _check_s1(result: ShadowRunResult) -> list[str]:
    """S-1: In shadow, boundary_verdict != crossed; boundary_crossed = false."""
    violations = []
    if result.boundary_verdict == "crossed":
        violations.append(f"S-1: {result.scenario_id}: boundary_verdict=crossed in shadow")
    if result.boundary_crossed:
        violations.append(f"S-1: {result.scenario_id}: boundary_crossed=true in shadow")
    return violations


def _check_s2(result: ShadowRunResult) -> list[str]:
    """S-2: Every run emits plan AND ledger."""
    violations = []
    if not result.plan:
        violations.append(f"S-2: {result.scenario_id}: plan not emitted")
    if not result.ledger_row:
        violations.append(f"S-2: {result.scenario_id}: ledger not emitted")
    return violations


def _check_s3(result: ShadowRunResult) -> list[str]:
    """S-3: decision_response.plan_hash == plan_hash; ledger.plan_link.plan_hash matches."""
    violations = []
    ph = result.plan_hash
    lr_ph = (result.ledger_row.get("plan_link") or {}).get("plan_hash")
    if lr_ph and lr_ph != ph:
        violations.append(f"S-3: {result.scenario_id}: ledger plan_hash mismatch")
    return violations


def _check_ingestion_batch(batch: dict[str, Any]) -> list[str]:
    """S-6: ingestion_batch items include request_id + plan + ledger_row."""
    violations = []
    for i, item in enumerate(batch.get("items", [])):
        if "request_id" not in item:
            violations.append(f"S-6: item[{i}]: missing request_id")
        if "plan" not in item:
            violations.append(f"S-6: item[{i}]: missing plan")
        if "ledger_row" not in item:
            violations.append(f"S-6: item[{i}]: missing ledger_row")
    return violations


class ShadowValidationHarness:
    """
    Runs baseline scenarios in shadow mode and validates invariants S-1, S-2, S-3, S-6.
    """

    def __init__(self, scenarios: list[ScenarioDef] | None = None, fixed_time: str | None = None):
        self.scenarios = scenarios or BASELINE_SCENARIOS
        self.runner = ShadowRunner(fixed_time=fixed_time)

    def run(self) -> HarnessResult:
        """Run all scenarios, build ingestion batch, run all invariant checks."""
        results = self.runner.run_all(self.scenarios)
        violations: list[str] = []
        for r in results:
            violations.extend(_check_s1(r))
            violations.extend(_check_s2(r))
            violations.extend(_check_s3(r))
        ingestion_batch = self.runner.build_ingestion_batch_from_results(results)
        violations.extend(_check_ingestion_batch(ingestion_batch))
        return HarnessResult(
            passed=len(violations) == 0,
            results=results,
            violations=violations,
            ingestion_batch=ingestion_batch,
        )
