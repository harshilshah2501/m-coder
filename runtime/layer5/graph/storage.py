from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from runtime.layer5.graph.builder import graph_content_hash
from runtime.layer5.graph.models import CodeIntelligenceGraph, GraphEdge, GraphNode


def write_graph_artifacts(graph: CodeIntelligenceGraph, output_dir: Path) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "code_intelligence_graph.v1.jsonl"
    manifest_path = output_dir / "code_intelligence_graph.v1.manifest.json"
    adjacency_path = output_dir / "code_intelligence_graph.v1.adjacency.json"

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as fh:
        for node in graph.nodes:
            fh.write(json.dumps({"record_type": "node", **node.to_dict()}, sort_keys=True) + "\n")
        for edge in graph.edges:
            fh.write(json.dumps({"record_type": "edge", **edge.to_dict()}, sort_keys=True) + "\n")

    adjacency_path.write_text(
        json.dumps(graph.adjacency, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": graph.schema_version,
        "graph_version": graph.graph_version,
        "generated_at": graph.generated_at,
        "repo_identity": graph.repo_identity,
        "extractor_identity": graph.extractor_identity,
        "stats": graph.stats,
        "content_hash": graph_content_hash(graph),
        "diagnostics": graph.diagnostics,
        "artifacts": {
            "jsonl": jsonl_path.name,
            "adjacency": adjacency_path.name,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"jsonl": jsonl_path, "manifest": manifest_path, "adjacency": adjacency_path}


def load_graph_artifacts(output_dir: Path) -> Tuple[CodeIntelligenceGraph, Dict[str, Any]]:
    jsonl_path = output_dir / "code_intelligence_graph.v1.jsonl"
    manifest_path = output_dir / "code_intelligence_graph.v1.manifest.json"
    adjacency_path = output_dir / "code_intelligence_graph.v1.adjacency.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    adjacency = json.loads(adjacency_path.read_text(encoding="utf-8"))

    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("record_type") == "node":
            nodes.append(
                GraphNode(
                    id=str(row["id"]),
                    kind=str(row["kind"]),
                    label=str(row["label"]),
                    attrs=dict(row.get("attrs") or {}),
                )
            )
        elif row.get("record_type") == "edge":
            edges.append(
                GraphEdge(
                    id=str(row["id"]),
                    src=str(row["src"]),
                    type=str(row["type"]),
                    dst=str(row["dst"]),
                    attrs=dict(row.get("attrs") or {}),
                )
            )
    graph = CodeIntelligenceGraph(
        schema_version=str(manifest.get("schema_version", "code_intelligence_graph.v1")),
        graph_version=str(manifest.get("graph_version", "1.0.0")),
        generated_at=str(manifest.get("generated_at", "")),
        repo_identity=dict(manifest.get("repo_identity") or {}),
        extractor_identity=dict(manifest.get("extractor_identity") or {}),
        stats=dict(manifest.get("stats") or {}),
        nodes=nodes,
        edges=edges,
        adjacency=adjacency,
        diagnostics=dict(manifest.get("diagnostics") or {}),
    )
    return graph, manifest

