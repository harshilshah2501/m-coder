from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("javalang")
pytest.importorskip("neo4j")

from tools.ast_indexer.ingest_java_graph import (
    JavaClassRecord,
    _build_eventbus_indexes,
    _build_metric_rows,
    _extract_eventbus_constants,
    _extract_file_anchors,
    extract_eventbus_address_constants,
)


def _record(name: str, qualified_name: str, file_path: str) -> JavaClassRecord:
    return JavaClassRecord(
        class_name=name,
        qualified_name=qualified_name,
        package="com.mindarray.aiops",
        top_package="aiops",
        extends=None,
        implements=(),
        is_abstract=False,
        is_interface=False,
        file_path=file_path,
        imports=(),
    )


def test_lane_b_anchor_categories_and_eventbus_relations(tmp_path: Path) -> None:
    source = """
        package com.mindarray.aiops;
        class EventBusConstants {
            public static final String ALERT_TOPIC = "event.aiops.alert";
        }
        class Publisher {
            void wire(Object router, Object vertx, Object eventBus) {
                vertx.deployVerticle("com.mindarray.Verticle");
                router.get("/alerts").handler(ctx -> {});
                eventBus.publish(EventBusConstants.ALERT_TOPIC, "payload");
                registerIntegration("pagerduty");
                config().getString("smtp.host");
            }
        }
        class Consumer {
            void wire(Object eventBus) {
                eventBus.consumer(EventBusConstants.ALERT_TOPIC, msg -> {});
            }
        }
    """
    file_path = str((tmp_path / "Sample.java").resolve())
    constants = _extract_eventbus_constants(source, file_path)
    by_key, by_ref, unique_by_field = _build_eventbus_indexes(constants)
    anchors, publishers_by_address, consumers_by_address = _extract_file_anchors(
        source=source,
        file_path=file_path,
        file_records=[
            _record("EventBusConstants", "com.mindarray.aiops.EventBusConstants", file_path),
            _record("Publisher", "com.mindarray.aiops.Publisher", file_path),
            _record("Consumer", "com.mindarray.aiops.Consumer", file_path),
        ],
        by_key=by_key,
        by_ref=by_ref,
        unique_by_field=unique_by_field,
    )

    categories = {anchor.category for anchor in anchors}
    assert "VERTICLE_REGISTRATION" in categories
    assert "API_ROUTE_REGISTRATION" in categories
    assert "EVENTBUS_CONSUMER_REGISTRATION" in categories
    assert "EVENTBUS_PUBLISH_ANCHOR" in categories
    assert "INTEGRATION_REGISTRATION" in categories
    assert "CONFIG_ACCESS_ANCHOR" in categories

    assert publishers_by_address["event.aiops.alert"] == {"com.mindarray.aiops.Publisher"}
    assert consumers_by_address["event.aiops.alert"] == {"com.mindarray.aiops.Consumer"}


def test_extract_eventbus_address_constants_is_stable_and_machine_readable(tmp_path: Path) -> None:
    java_root = tmp_path / "src"
    java_root.mkdir(parents=True)
    java_file = java_root / "Constants.java"
    java_file.write_text(
        """
        package com.mindarray.eventbus;
        class EventBusConstants {
            public static final String B_TOPIC = "event.b";
            public static final String A_TOPIC = "event.a";
        }
        """,
        encoding="utf-8",
    )

    rows = extract_eventbus_address_constants(java_root)
    assert [row["key"] for row in rows] == sorted(row["key"] for row in rows)
    assert rows[0]["key"].endswith(".A_TOPIC")
    assert rows[0]["value"] == "event.a"
    assert set(rows[0]) == {"key", "value", "class_qualified_name", "field_name", "file_path"}


def test_metric_rows_include_anchor_categories_and_edge_types() -> None:
    anchor_counts = {
        "VERTICLE_REGISTRATION": 3,
        "EVENTBUS_CONSUMER_REGISTRATION": 2,
        "API_ROUTE_REGISTRATION": 1,
        "EVENTBUS_PUBLISH_ANCHOR": 4,
        "INTEGRATION_REGISTRATION": 5,
        "CONFIG_ACCESS_ANCHOR": 6,
    }
    edge_counts = {"PUBLISHES_TO_CONSUMER": 7, "CONSUMES_EVENTBUS": 2}
    rows = _build_metric_rows(state_key="java_ast", anchor_counts=anchor_counts, edge_type_counts=edge_counts)
    keyed = {row["metricKey"]: row for row in rows}

    assert "java_ast:anchor:VERTICLE_REGISTRATION" in keyed
    assert "java_ast:anchor:EVENTBUS_CONSUMER_REGISTRATION" in keyed
    assert "java_ast:anchor:API_ROUTE_REGISTRATION" in keyed
    assert keyed["java_ast:edge:PUBLISHES_TO_CONSUMER"]["count"] == 7
