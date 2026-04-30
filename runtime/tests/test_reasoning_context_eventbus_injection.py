from __future__ import annotations

import json
from pathlib import Path

from runtime.ask_service import reasoning_context as rc_mod


def _write_eventbus_map(path: Path) -> None:
    payload = {
        "schema_version": "motadata_wiring_map.v1",
        "map_type": "eventbus_topology",
        "nodes": [],
        "edges": [
            {
                "edge_type": "PUBLISHES_TO_ADDRESS",
                "address": "change.notification",
                "address_kind": "runtime",
                "confidence": "bounded",
                "evidence": {"file": "A.java", "class": "A", "method": "m1", "line": 10},
            },
            {
                "edge_type": "CONSUMES_FROM_ADDRESS",
                "address": "change.notification",
                "address_kind": "runtime",
                "confidence": "bounded",
                "evidence": {"file": "B.java", "class": "B", "method": "m2", "line": 20},
            },
            {
                "edge_type": "PUBLISHES_TO_ADDRESS",
                "address": "test.integration",
                "address_kind": "test",
                "confidence": "bounded",
                "evidence": {"file": "T.java", "class": "T", "method": "t", "line": 5},
            },
            {
                "edge_type": "PUBLISHES_TO_ADDRESS",
                "address": "websocket.client.registered",
                "address_kind": "websocket",
                "confidence": "bounded",
                "evidence": {"file": "W.java", "class": "W", "method": "w", "line": 7},
            },
        ],
        "unknowns": [
            {
                "unknown_type": "DYNAMIC_ADDRESS",
                "raw_token": "EVENT_X + host",
                "reason": "dynamic",
                "source": {"file": "U.java", "class": "U", "method": "__unresolved_static_or_lambda_context__", "line": 12},
            }
        ],
        "validation_summary": {
            "resolved_address_count": 3,
            "unresolved_address_count": 0,
            "dynamic_address_count": 1,
            "confidence_distribution": {"bounded": 4, "unknown": 1},
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_event_query_injects_eventbus_context(monkeypatch, tmp_path: Path):
    p = tmp_path / "eventbus_topology_mapping.v1.json"
    _write_eventbus_map(p)
    monkeypatch.setattr(rc_mod, "_EVENTBUS_TOPOLOGY_CACHE_FILE", p)
    out = rc_mod.build_reasoning_context(query="Which event triggers notification dispatch?", evidence_bundle={}, graph_traversal={})
    eb = out.get("eventbus_context") or {}
    assert eb
    assert len(eb.get("addresses", [])) <= 3
    assert len(eb.get("producers", [])) <= 3
    assert len(eb.get("consumers", [])) <= 3
    assert any(a.get("address") == "change.notification" for a in eb.get("addresses", []))


def test_api_architecture_query_does_not_inject(monkeypatch, tmp_path: Path):
    p = tmp_path / "eventbus_topology_mapping.v1.json"
    _write_eventbus_map(p)
    monkeypatch.setattr(rc_mod, "_EVENTBUS_TOPOLOGY_CACHE_FILE", p)
    out = rc_mod.build_reasoning_context(query="Explain the API layer architecture.", evidence_bundle={}, graph_traversal={})
    assert out.get("eventbus_context") == {}


def test_notification_query_excludes_test_control_by_default(monkeypatch, tmp_path: Path):
    p = tmp_path / "eventbus_topology_mapping.v1.json"
    _write_eventbus_map(p)
    monkeypatch.setattr(rc_mod, "_EVENTBUS_TOPOLOGY_CACHE_FILE", p)
    out = rc_mod.build_reasoning_context(query="How are notification events triggered?", evidence_bundle={}, graph_traversal={})
    eb = out.get("eventbus_context") or {}
    addrs = {a.get("address") for a in eb.get("addresses", [])}
    assert "test.integration" not in addrs


def test_dynamic_unknowns_exposed_for_debug(monkeypatch, tmp_path: Path):
    p = tmp_path / "eventbus_topology_mapping.v1.json"
    _write_eventbus_map(p)
    monkeypatch.setattr(rc_mod, "_EVENTBUS_TOPOLOGY_CACHE_FILE", p)
    out = rc_mod.build_reasoning_context(
        query="Debug event failure: unresolved dynamic address in notification path",
        evidence_bundle={},
        graph_traversal={},
    )
    eb = out.get("eventbus_context") or {}
    assert eb.get("unknowns"), "Debug-like query should include unknowns"


def test_caps_enforced_total_nodes(monkeypatch, tmp_path: Path):
    p = tmp_path / "eventbus_topology_mapping.v1.json"
    payload = {
        "schema_version": "motadata_wiring_map.v1",
        "map_type": "eventbus_topology",
        "edges": [],
        "unknowns": [],
        "validation_summary": {},
    }
    for i in range(20):
        payload["edges"].append(
            {
                "edge_type": "PUBLISHES_TO_ADDRESS" if i % 2 == 0 else "CONSUMES_FROM_ADDRESS",
                "address": f"runtime.addr.{i}",
                "address_kind": "runtime",
                "confidence": "bounded",
                "evidence": {"file": "X.java", "class": "X", "method": f"m{i}", "line": i + 1},
            }
        )
    p.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(rc_mod, "_EVENTBUS_TOPOLOGY_CACHE_FILE", p)
    out = rc_mod.build_reasoning_context(query="event producer consumer map", evidence_bundle={}, graph_traversal={})
    eb = out.get("eventbus_context") or {}
    n = len(eb.get("addresses", [])) + len(eb.get("producers", [])) + len(eb.get("consumers", []))
    assert n <= 10


def test_notification_publish_consume_prefers_exact_pair(monkeypatch, tmp_path: Path):
    p = tmp_path / "eventbus_topology_mapping.v1.json"
    payload = {
        "schema_version": "motadata_wiring_map.v1",
        "map_type": "eventbus_topology",
        "edges": [
            {
                "edge_type": "PUBLISHES_TO_ADDRESS",
                "address": "notification.paired",
                "address_kind": "runtime",
                "confidence": "bounded",
                "evidence": {"file": "N1.java", "class": "NotificationEngine", "method": "start", "line": 11},
            },
            {
                "edge_type": "CONSUMES_FROM_ADDRESS",
                "address": "notification.paired",
                "address_kind": "runtime",
                "confidence": "bounded",
                "evidence": {
                    "file": "N2.java",
                    "class": "LocalEventChangeNotificationHandler",
                    "method": "handle",
                    "line": 12,
                },
            },
            {
                "edge_type": "PUBLISHES_TO_ADDRESS",
                "address": "notification.unpaired",
                "address_kind": "runtime",
                "confidence": "bounded",
                "evidence": {"file": "N3.java", "class": "NotificationEngine", "method": "emit", "line": 13},
            },
        ],
        "unknowns": [],
        "validation_summary": {},
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(rc_mod, "_EVENTBUS_TOPOLOGY_CACHE_FILE", p)
    out = rc_mod.build_reasoning_context(
        query="Which components publish or consume notification events?",
        evidence_bundle={},
        graph_traversal={},
    )
    eb = out.get("eventbus_context") or {}
    addrs = {a.get("address") for a in eb.get("addresses", [])}
    assert "notification.paired" in addrs
    assert any(x.get("address") == "notification.paired" for x in eb.get("producers", []))
    assert any(x.get("address") == "notification.paired" for x in eb.get("consumers", []))
