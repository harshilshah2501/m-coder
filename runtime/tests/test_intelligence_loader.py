from __future__ import annotations

from pathlib import Path

import yaml

from runtime.intelligence.loader import load_intelligence
from runtime.intelligence.normalize import normalize_behavior_flows_document


def _behavior_doc_with_eventbus(address: str) -> dict:
    return {
        "schema_version": "intelligence.behavior_flows.v1",
        "behavior_flows": [
            {
                "behavior_id": "loader_behavior",
                "summary": "Loader behavior",
                "priority": "P1",
                "eventbus_addresses": {
                    "publishes": ["event.authored.should.not.win"],
                    "consumes": ["event.authored.should.not.win"],
                },
                "stages": [
                    {
                        "name": "publish",
                        "mechanisms": [
                            {
                                "type": "EVENTBUS",
                                "address": address,
                                "source_symbol": "Publisher.emit",
                                "target_symbol": "Consumer.handle",
                            }
                        ],
                    }
                ],
                "known_failure_modes": [
                    {
                        "symptom": "No handler receives payload",
                        "diagnostic_files": ["runtime/loader_behavior.py"],
                    }
                ],
                "query_aliases": [{"alias": "loader behavior", "match_strategy": "exact"}],
            }
        ],
    }


def _playbooks_doc() -> dict:
    return {
        "schema_version": "intelligence.convention_playbooks.v1",
        "convention_playbooks": [
            {
                "playbook_id": "loader_playbook",
                "summary": "Loader summary",
                "required_steps": [
                    {
                        "order": 1,
                        "action": "Do thing",
                        "verification": "Check thing",
                        "file_template": "runtime/tests/test_intelligence_loader.py",
                    }
                ],
            }
        ],
    }


def test_derived_eventbus_precedence_over_authored_compatibility() -> None:
    raw = _behavior_doc_with_eventbus("event.derived.wins")
    normalized, _warnings = normalize_behavior_flows_document(raw)
    behavior = normalized["behavior_flows"][0]

    assert behavior["eventbus_addresses"]["publishes"] == ["event.derived.wins"]
    assert behavior["eventbus_addresses"]["consumes"] == ["event.derived.wins"]


def test_warning_emitted_on_unresolved_address() -> None:
    raw = _behavior_doc_with_eventbus("event.not.in.constants")
    _normalized, warnings = normalize_behavior_flows_document(
        raw,
        extracted_eventbus_constants={"event.known"},
    )

    assert warnings
    assert warnings[0].code == "UNRESOLVED_EVENTBUS_ADDRESS"
    assert warnings[0].address == "event.not.in.constants"


def test_loader_behavior_reads_validates_and_normalizes(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "intelligence"
    docs_dir.mkdir(parents=True)

    behavior_path = docs_dir / "behavior_flows.yaml"
    playbooks_path = docs_dir / "convention_playbooks.yaml"

    behavior_path.write_text(
        yaml.safe_dump(_behavior_doc_with_eventbus("event.loader.ok"), sort_keys=False),
        encoding="utf-8",
    )
    playbooks_path.write_text(
        yaml.safe_dump(_playbooks_doc(), sort_keys=False),
        encoding="utf-8",
    )

    bundle = load_intelligence(tmp_path, extracted_eventbus_constants={"event.loader.ok"})

    behavior = bundle.behavior_flows["behavior_flows"][0]
    assert behavior["eventbus_addresses"]["publishes"] == ["event.loader.ok"]
    assert behavior["eventbus_addresses"]["consumes"] == ["event.loader.ok"]
    assert bundle.warnings == []
    assert bundle.convention_playbooks["convention_playbooks"][0]["playbook_id"] == "loader_playbook"
