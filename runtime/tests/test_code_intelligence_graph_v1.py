from __future__ import annotations

from pathlib import Path

from runtime.layer5.authority.code_index_models import (
    CallConfidence,
    CallEdge,
    ClassRecord,
    CodeIndex,
    EntryPointRecord,
    EntryPointType,
    FileRecord,
)
from runtime.layer5.authority.registry_loader import load_registry
from runtime.layer5.graph import (
    GraphBuilder,
    get_call_chain,
    get_concept_owners,
    get_entrypoint_flow,
    get_inheritance_chain,
    validate_determinism,
    validate_graph_integrity,
)


def _mini_index() -> CodeIndex:
    index = CodeIndex()
    index.files["src/main/java/com/mindarray/api/AbstractAPI.java"] = FileRecord(
        relative_path="src/main/java/com/mindarray/api/AbstractAPI.java",
        package="com.mindarray.api",
        module="api",
        classes=(ClassRecord(name="AbstractAPI", file_path="src/main/java/com/mindarray/api/AbstractAPI.java"),),
    )
    index.files["src/main/java/com/mindarray/api/MailServerConfiguration.java"] = FileRecord(
        relative_path="src/main/java/com/mindarray/api/MailServerConfiguration.java",
        package="com.mindarray.api",
        module="api",
        classes=(
            ClassRecord(
                name="MailServerConfiguration",
                file_path="src/main/java/com/mindarray/api/MailServerConfiguration.java",
                superclass="AbstractAPI",
                methods=("beforeUpdate",),
            ),
        ),
    )
    index.files["src/main/java/com/mindarray/api/APIServer.java"] = FileRecord(
        relative_path="src/main/java/com/mindarray/api/APIServer.java",
        package="com.mindarray.api",
        module="api",
        classes=(ClassRecord(name="APIServer", file_path="src/main/java/com/mindarray/api/APIServer.java", methods=("start",)),),
    )
    index.files["src/main/java/com/mindarray/api/SecondaryApiHandler.java"] = FileRecord(
        relative_path="src/main/java/com/mindarray/api/SecondaryApiHandler.java",
        package="com.mindarray.api",
        module="api",
        classes=(ClassRecord(name="SecondaryApiHandler", file_path="src/main/java/com/mindarray/api/SecondaryApiHandler.java", methods=("handle",)),),
    )
    index.call_edges.append(
        CallEdge(
            source_file="src/main/java/com/mindarray/api/APIServer.java",
            source_class="APIServer",
            source_method="start",
            target_class="MailServerConfiguration",
            target_method="beforeUpdate",
            confidence=CallConfidence.HIGH,
        )
    )
    index.call_edges.append(
        CallEdge(
            source_file="src/main/java/com/mindarray/api/APIServer.java",
            source_class="APIServer",
            source_method="start",
            target_class="SecondaryApiHandler",
            target_method="handle",
            confidence=CallConfidence.HIGH,
        )
    )
    index.entry_points.append(
        EntryPointRecord(
            entry_type=EntryPointType.REST_CONTROLLER,
            relative_path="src/main/java/com/mindarray/api/APIServer.java",
            class_name="APIServer",
            method_name="start",
            invokes=("MailServerConfiguration.beforeUpdate", "SecondaryApiHandler.handle"),
        )
    )
    index.build_indices()
    return index


def test_graph_builder_and_traversal_contracts():
    workspace = Path("/home/harshil/Harshil-PoCs/m-coder")
    registry = load_registry(workspace / "runtime/layer5/authority/product_authority_registry.yaml")
    builder = GraphBuilder(workspace)
    g1 = builder.build(_mini_index(), registry=registry)
    g2 = builder.build(_mini_index(), registry=registry)

    integrity = validate_graph_integrity(g1)
    assert integrity.passed, integrity.errors
    assert validate_determinism(g1, g2).passed

    inheritance = get_inheritance_chain(g1, "MailServerConfiguration")
    assert "MailServerConfiguration" in inheritance[0]
    assert "AbstractAPI" in inheritance

    flow = get_entrypoint_flow(g1, "APIServer.start")
    assert flow
    assert "APIServer.start" in flow[0]
    assert len(flow) >= 2
    assert any("SecondaryApiHandler.handle" in p for p in flow)
    assert any("MailServerConfiguration.beforeUpdate" in p for p in flow)

    call_chain = get_call_chain(g1, "APIServer.start")
    assert call_chain
    assert len(call_chain) >= 2
    assert any("MailServerConfiguration.beforeUpdate" in p for p in call_chain)
    assert any("SecondaryApiHandler.handle" in p for p in call_chain)

    owners = get_concept_owners(g1, "mail_server_configuration")
    assert "MailServerConfiguration" in ",".join(owners["owners"])


def test_eventbus_edges_are_bounded_regex_provenance(tmp_path: Path):
    src = tmp_path / "src/main/java/com/mindarray/eventbus"
    src.mkdir(parents=True, exist_ok=True)
    java_file = src / "UIActionEventHandler.java"
    java_file.write_text(
        (
            "package com.mindarray.eventbus;\n"
            "public class UIActionEventHandler {\n"
            "  public void start() {\n"
            "    eventBus.publish(\"ui.action\");\n"
            "    eventBus.consumer(\"ui.reply\");\n"
            "  }\n"
            "}\n"
        ),
        encoding="utf-8",
    )
    index = CodeIndex()
    rel = "src/main/java/com/mindarray/eventbus/UIActionEventHandler.java"
    index.files[rel] = FileRecord(
        relative_path=rel,
        package="com.mindarray.eventbus",
        module="eventbus",
        classes=(ClassRecord(name="UIActionEventHandler", file_path=rel, methods=("start",)),),
    )
    index.build_indices()

    builder = GraphBuilder(tmp_path)
    graph = builder.build(index, registry=None)
    ev_edges = [e for e in graph.edges if e.type in ("PUBLISHES_TO", "CONSUMES_FROM")]
    assert len(ev_edges) >= 2
    for edge in ev_edges:
        assert edge.attrs.get("confidence") == "bounded"
        assert edge.attrs.get("provenance.detail") == "regex_derived_eventbus_edge"

