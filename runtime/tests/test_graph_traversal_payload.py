from __future__ import annotations

from pathlib import Path

from runtime.ask_service.graph_traversal_payload import build_graph_traversal_payload
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
from runtime.layer5.graph import GraphBuilder, write_graph_artifacts


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
    index.entry_points.append(
        EntryPointRecord(
            entry_type=EntryPointType.REST_CONTROLLER,
            relative_path="src/main/java/com/mindarray/api/APIServer.java",
            class_name="APIServer",
            method_name="start",
            invokes=("MailServerConfiguration.beforeUpdate",),
        )
    )
    index.build_indices()
    return index


def test_build_graph_traversal_payload_optional_and_additive(tmp_path: Path):
    workspace = Path("/home/harshil/Harshil-PoCs/m-coder")
    registry = load_registry(workspace / "runtime/layer5/authority/product_authority_registry.yaml")
    graph = GraphBuilder(workspace).build(_mini_index(), registry=registry)
    out_dir = tmp_path / "graph"
    write_graph_artifacts(graph, out_dir)

    payload = build_graph_traversal_payload(
        query="Explain the API layer architecture.",
        task_type="general",
        authority_resolution={
            "primary_owner": {"class": "APIServer", "method": "start"},
            "matched_concepts": [{"concept_id": "api_request_routing"}],
        },
        graph_dir=out_dir,
    )
    assert payload is not None
    assert payload.get("flow_paths")
    assert payload.get("graph_schema_version") == "code_intelligence_graph.v1"

    missing = build_graph_traversal_payload(
        query="Explain the API layer architecture.",
        task_type="general",
        authority_resolution=None,
        graph_dir=tmp_path / "missing",
    )
    assert missing is None

