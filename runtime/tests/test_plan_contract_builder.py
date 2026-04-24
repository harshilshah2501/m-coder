from __future__ import annotations

from runtime.ask_service.plan_contract_builder import build_plan_contract_v1
from runtime.plan_contract.v1_validate import validate_plan_contract_v1


def _evidence_with_owner() -> dict:
    return {
        "entries": [
            {"relative_path": "src/core/alerts.py"},
            {"relative_path": "src/core/rules.py"},
        ],
        "authority_resolution": {
            "primary_owner": {"file": "src/core/alerts.py"},
        },
    }


def test_build_plan_contract_valid_when_metadata_is_sufficient() -> None:
    result = build_plan_contract_v1(
        query="Where is alert enrichment implemented?",
        plan_steps=["Inspect owner class", "Verify call chain", "Propose bounded change"],
        metadata={
            "evidence_quality": "STRONG",
            "intent_type": "GENERAL_INTENT",
            "quality_reasons": ["OWNER_ANCHOR_RECOVERY"],
        },
        evidence_bundle=_evidence_with_owner(),
    )
    assert result.omission_reason is None
    assert isinstance(result.plan_contract, dict)
    assert result.plan_contract["schema_version"] == "plan_contract.v1"
    assert result.plan_contract["risk_class"] == "medium"
    assert result.plan_contract["approval_posture"] == "advisory_only"
    assert validate_plan_contract_v1(result.plan_contract) == []


def test_build_plan_contract_insufficient_evidence_still_truthful_when_possible() -> None:
    result = build_plan_contract_v1(
        query="in this system",
        plan_steps=[],
        metadata={
            "evidence_quality": "INSUFFICIENT",
            "intent_type": "GENERAL_INTENT",
            "quality_reasons": ["NO_RELEVANT_HITS"],
        },
        evidence_bundle={"entries": []},
    )
    assert result.omission_reason is None
    assert isinstance(result.plan_contract, dict)
    assert result.plan_contract["risk_class"] == "insufficient_evidence"
    assert result.plan_contract["approval_posture"] == "defer"
    assert result.plan_contract["affected_files"] == []
    assert validate_plan_contract_v1(result.plan_contract) == []


def test_build_plan_contract_omits_when_required_metadata_missing() -> None:
    result = build_plan_contract_v1(
        query="Where is sync implemented?",
        plan_steps=["Read file"],
        metadata={
            # missing evidence_quality on purpose
            "intent_type": "GENERAL_INTENT",
            "quality_reasons": ["OWNER_ANCHOR_RECOVERY"],
        },
        evidence_bundle=_evidence_with_owner(),
    )
    assert result.plan_contract is None
    assert result.omission_reason == "missing_metadata:evidence_quality"
