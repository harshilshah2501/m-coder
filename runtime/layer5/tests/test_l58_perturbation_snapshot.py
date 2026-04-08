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
    base_ids = [r.id for r in rows if r.perturbation.kind == "base"]
    expected_kinds = [
        "abbreviated_symbol",
        "package_omitted",
        "camelcase_split",
        "error_text_only",
        "typo_light_wording",
        "subsystem_alias_wording",
        "phrasing_shift",
    ]
    assert len(generated_ids) == len(base_ids) * len(expected_kinds)

    for base in base_ids:
        observed = [
            gid.split("::", 1)[1]
            for gid in generated_ids
            if gid.startswith(f"{base}::")
        ]
        assert observed == expected_kinds, f"{base}: generated kinds mismatch/order"
