from __future__ import annotations

import pytest

from runtime.intelligence.schema import IntelligenceSchemaError, validate_behavior_flows_document


def _base_behavior_doc() -> dict:
    return {
        "schema_version": "intelligence.behavior_flows.v1",
        "behavior_flows": [
            {
                "behavior_id": "sample_behavior",
                "summary": "Sample",
                "priority": "P1",
                "stages": [
                    {
                        "name": "stage_one",
                        "mechanisms": [
                            {
                                "type": "EVENTBUS",
                                "address": "event.sample",
                                "source_symbol": "SamplePublisher.publish",
                            }
                        ],
                    }
                ],
                "data_transformations": [
                    {"input": "raw", "operation": "normalize", "output": "normalized"}
                ],
                "known_failure_modes": [
                    {"symptom": "Missing payload", "diagnostic_files": ["runtime/sample.py"]}
                ],
                "query_aliases": [{"alias": "sample behavior", "match_strategy": "exact"}],
            }
        ],
    }


def test_strict_mechanism_validation_forbids_irrelevant_fields() -> None:
    doc = _base_behavior_doc()
    doc["behavior_flows"][0]["stages"][0]["mechanisms"][0]["type"] = "DIRECT_CALL"
    with pytest.raises(IntelligenceSchemaError, match="not allowed for type=DIRECT_CALL"):
        validate_behavior_flows_document(doc)


def test_store_config_bound_requires_config_key() -> None:
    doc = _base_behavior_doc()
    doc["behavior_flows"][0]["stages"][0]["mechanisms"][0] = {
        "type": "STORE",
        "store_class": "ConfigStore",
        "config_bound": True,
        "target_symbol": "ConfigStore.read",
    }
    with pytest.raises(IntelligenceSchemaError, match="config_key"):
        validate_behavior_flows_document(doc)


def test_fuzzy_alias_requires_guardrails() -> None:
    doc = _base_behavior_doc()
    doc["behavior_flows"][0]["query_aliases"] = [
        {"alias": "sample fuzzy", "match_strategy": "fuzzy"}
    ]
    with pytest.raises(IntelligenceSchemaError, match="fuzzy_guardrails"):
        validate_behavior_flows_document(doc)
