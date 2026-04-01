from __future__ import annotations

from pathlib import Path

from runtime.layer5.audit.l58_dataset import load_golden_cases
from runtime.layer5.audit.l58_perturbations import generate_deterministic_variants


_AUDIT_DIR = Path(__file__).resolve().parents[1] / "audit"
_DATASET = _AUDIT_DIR / "fixtures" / "l58_golden_queries.v1.json"


def test_l58_generated_perturbation_snapshot_ids_order_count() -> None:
    rows = load_golden_cases(_DATASET)
    generated = generate_deterministic_variants(rows)
    generated_ids = [r.id for r in generated]
    expected_ids = [
        "l58.ask.topology.where.base::abbreviated_symbol",
        "l58.ask.topology.where.base::package_omitted",
        "l58.ask.topology.where.base::camelcase_split",
        "l58.ask.topology.where.base::typo_light_wording",
        "l58.ask.topology.where.base::phrasing_shift",
        "l58.code.metrics.parser.target.base::abbreviated_symbol",
        "l58.code.metrics.parser.target.base::package_omitted",
        "l58.code.metrics.parser.target.base::camelcase_split",
        "l58.code.metrics.parser.target.base::typo_light_wording",
        "l58.code.metrics.parser.target.base::phrasing_shift",
        "l58.debug.correlation.duplicate.base::abbreviated_symbol",
        "l58.debug.correlation.duplicate.base::package_omitted",
        "l58.debug.correlation.duplicate.base::camelcase_split",
        "l58.debug.correlation.duplicate.base::typo_light_wording",
        "l58.debug.correlation.duplicate.base::phrasing_shift",
        "l58.plan.ingestion.impact.base::abbreviated_symbol",
        "l58.plan.ingestion.impact.base::package_omitted",
        "l58.plan.ingestion.impact.base::camelcase_split",
        "l58.plan.ingestion.impact.base::typo_light_wording",
        "l58.plan.ingestion.impact.base::phrasing_shift",
    ]
    assert generated_ids == expected_ids
    assert len(generated_ids) == 20
