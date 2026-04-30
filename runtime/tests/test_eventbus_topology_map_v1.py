from __future__ import annotations

from pathlib import Path

from runtime.layer5.graph.eventbus_topology_map import build_eventbus_topology_map


def test_eventbus_topology_map_extracts_publish_consume_and_join(tmp_path: Path):
    src = tmp_path / "src/main/java/com/mindarray/eventbus"
    src.mkdir(parents=True, exist_ok=True)
    pub = src / "Publisher.java"
    con = src / "Consumer.java"
    pub.write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "public class Publisher {",
                "  public void start() {",
                "    eventBus().publish(\"event.alpha\", payload);",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    con.write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "public class Consumer {",
                "  public void start() {",
                "    eventBus().consumer(\"event.alpha\");",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    rel_files = [
        "src/main/java/com/mindarray/eventbus/Publisher.java",
        "src/main/java/com/mindarray/eventbus/Consumer.java",
    ]
    out = build_eventbus_topology_map(workspace_root=tmp_path, relative_files=rel_files, repo_identity={})
    assert out["map_type"] == "eventbus_topology"
    types = {e["edge_type"] for e in out["edges"]}
    assert "PUBLISHES_TO_ADDRESS" in types
    assert "CONSUMES_FROM_ADDRESS" in types
    assert "PUBLISHES_TO_CONSUMER" in types
    assert out["validation_summary"]["edge_count"] >= 3
    assert out["validation_summary"]["unknown_count"] == 0
    assert out["validation_summary"]["bad_method_name_count"] == 0


def test_eventbus_topology_map_emits_unknown_for_dynamic_address(tmp_path: Path):
    src = tmp_path / "src/main/java/com/mindarray/eventbus"
    src.mkdir(parents=True, exist_ok=True)
    java_file = src / "DynamicPublisher.java"
    java_file.write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "public class DynamicPublisher {",
                "  public void run() {",
                "    eventBus().publish(topicName, payload);",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    rel = "src/main/java/com/mindarray/eventbus/DynamicPublisher.java"
    out = build_eventbus_topology_map(workspace_root=tmp_path, relative_files=[rel], repo_identity={})
    assert out["edges"] == []
    assert out["unknowns"], "Expected unresolved address unknown"
    unknown = out["unknowns"][0]
    assert unknown["unknown_type"] == "DYNAMIC_ADDRESS"
    assert unknown["source"]["file"] == rel
    assert unknown["source"]["line"] == 4


def test_eventbus_constants_resolution_with_static_import(tmp_path: Path):
    base = tmp_path / "src/main/java/com/mindarray"
    ev = base / "eventbus"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "EventBusConstants.java").write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "public class EventBusConstants {",
                "  public static final String EVENT_AGENT = \"event.agent\";",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    (ev / "EventSender.java").write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "import static com.mindarray.eventbus.EventBusConstants.EVENT_AGENT;",
                "public class EventSender {",
                "  public void send() {",
                "    eventBus().send(EVENT_AGENT, payload);",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    rel_files = [
        "src/main/java/com/mindarray/eventbus/EventBusConstants.java",
        "src/main/java/com/mindarray/eventbus/EventSender.java",
    ]
    out = build_eventbus_topology_map(workspace_root=tmp_path, relative_files=rel_files, repo_identity={})
    assert any(e.get("address") == "event.agent" for e in out["edges"])
    assert out["validation_summary"]["unknown_count"] == 0


def test_method_attribution_constructor_generic_lambda_if_nested(tmp_path: Path):
    src = tmp_path / "src/main/java/com/mindarray/eventbus"
    src.mkdir(parents=True, exist_ok=True)
    java = src / "ComplexHandler.java"
    java.write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "public class ComplexHandler {",
                "  public ComplexHandler() {",
                "    eventBus().publish(\"runtime.bootstrap\", payload);",
                "  }",
                "  public java.util.Map<String,String> buildMap() {",
                "    if (flag) { eventBus().send(\"runtime.map\", data); }",
                "    list.forEach(x -> eventBus().publish(\"runtime.lambda\", x));",
                "    call(eventBus().request(\"runtime.nested\", x));",
                "    return new java.util.HashMap<>();",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    rel = "src/main/java/com/mindarray/eventbus/ComplexHandler.java"
    out = build_eventbus_topology_map(workspace_root=tmp_path, relative_files=[rel], repo_identity={})
    methods = {e["evidence"]["method"] for e in out["edges"] if isinstance(e.get("evidence"), dict)}
    assert "ComplexHandler" in methods
    assert "buildMap" in methods
    assert "if" not in methods
    assert "File" not in methods
    assert "JsonObject" not in methods
    assert out["validation_summary"]["bad_method_name_count"] == 0


def test_address_kind_classification(tmp_path: Path):
    src = tmp_path / "src/main/java/com/mindarray/eventbus"
    src.mkdir(parents=True, exist_ok=True)
    java = src / "Kinds.java"
    java.write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "public class Kinds {",
                "  public void run() {",
                "    eventBus().publish(\"test.integration\", p);",
                "    eventBus().publish(\"EVENT_AGENT\", p);",
                "    eventBus().publish(\"websocket.client.registered\", p);",
                "    eventBus().publish(\"runtime.notification\", p);",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    rel = "src/main/java/com/mindarray/eventbus/Kinds.java"
    out = build_eventbus_topology_map(workspace_root=tmp_path, relative_files=[rel], repo_identity={})
    kinds = {e["address"]: e.get("address_kind") for e in out["edges"]}
    assert kinds["test.integration"] == "test"
    assert kinds["EVENT_AGENT"] == "control"
    assert kinds["websocket.client.registered"] == "websocket"
    assert kinds["runtime.notification"] == "runtime"


def test_ignores_javadoc_and_line_comments_for_eventbus_patterns(tmp_path: Path):
    src = tmp_path / "src/main/java/com/mindarray/eventbus"
    src.mkdir(parents=True, exist_ok=True)
    java = src / "CommentNoise.java"
    java.write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "public class CommentNoise {",
                "  /**",
                "   * Example: eventBus().send(\"fake.comment.addr\", msg);",
                "   */",
                "  public void run() {",
                "    // eventBus().publish(\"fake.inline.addr\", msg);",
                "    eventBus().publish(\"runtime.real.addr\", msg);",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    rel = "src/main/java/com/mindarray/eventbus/CommentNoise.java"
    out = build_eventbus_topology_map(workspace_root=tmp_path, relative_files=[rel], repo_identity={})
    addrs = {e["address"] for e in out["edges"]}
    assert "runtime.real.addr" in addrs
    assert "fake.comment.addr" not in addrs
    assert "fake.inline.addr" not in addrs
    assert out["validation_summary"]["bad_method_name_count"] == 0


def test_unresolved_symbol_for_static_initializer_or_field_context(tmp_path: Path):
    src = tmp_path / "src/main/java/com/mindarray/eventbus"
    src.mkdir(parents=True, exist_ok=True)
    java = src / "StaticCtx.java"
    java.write_text(
        "\n".join(
            [
                "package com.mindarray.eventbus;",
                "public class StaticCtx {",
                "  static {",
                "    eventBus().publish(\"runtime.static.ctx\", payload);",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    rel = "src/main/java/com/mindarray/eventbus/StaticCtx.java"
    out = build_eventbus_topology_map(workspace_root=tmp_path, relative_files=[rel], repo_identity={})
    edge = out["edges"][0]
    assert edge["evidence"]["method"] == "__unresolved_static_or_lambda_context__"
    assert out["validation_summary"]["bad_method_name_count"] == 0

