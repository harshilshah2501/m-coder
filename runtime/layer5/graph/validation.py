from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from runtime.layer5.graph.builder import graph_content_hash
from runtime.layer5.graph.models import CodeIntelligenceGraph


@dataclass
class GraphValidationResult:
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_graph_integrity(graph: CodeIntelligenceGraph) -> GraphValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    if graph.schema_version != "code_intelligence_graph.v1":
        errors.append(f"unexpected schema_version={graph.schema_version}")
    if not graph.nodes:
        errors.append("graph contains no nodes")
    node_ids: Set[str] = {n.id for n in graph.nodes}
    if len(node_ids) != len(graph.nodes):
        errors.append("duplicate node ids detected")

    edge_ids: Set[str] = set()
    for e in graph.edges:
        if e.id in edge_ids:
            errors.append(f"duplicate edge id={e.id}")
        edge_ids.add(e.id)
        if e.src not in node_ids:
            errors.append(f"dangling edge src={e.src}")
        if e.dst not in node_ids:
            errors.append(f"dangling edge dst={e.dst}")

    if not graph.adjacency:
        warnings.append("adjacency map missing")
    if graph.stats.get("node_count", -1) != len(graph.nodes):
        warnings.append("stats.node_count mismatch")
    if graph.stats.get("edge_count", -1) != len(graph.edges):
        warnings.append("stats.edge_count mismatch")

    return GraphValidationResult(passed=not errors, errors=errors, warnings=warnings)


def validate_determinism(graph_a: CodeIntelligenceGraph, graph_b: CodeIntelligenceGraph) -> GraphValidationResult:
    h1 = graph_content_hash(graph_a)
    h2 = graph_content_hash(graph_b)
    if h1 == h2:
        return GraphValidationResult(passed=True)
    return GraphValidationResult(
        passed=False,
        errors=[f"determinism mismatch: hash_a={h1} hash_b={h2}"],
    )

