from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, MutableMapping


@dataclass(frozen=True)
class GraphNode:
    id: str
    kind: str
    label: str
    attrs: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "attrs": dict(self.attrs),
        }


@dataclass(frozen=True)
class GraphEdge:
    id: str
    src: str
    type: str
    dst: str
    attrs: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "src": self.src,
            "type": self.type,
            "dst": self.dst,
            "attrs": dict(self.attrs),
        }


@dataclass
class CodeIntelligenceGraph:
    schema_version: str = "code_intelligence_graph.v1"
    graph_version: str = "1.0.0"
    generated_at: str = ""
    repo_identity: MutableMapping[str, Any] = field(default_factory=dict)
    extractor_identity: MutableMapping[str, Any] = field(default_factory=dict)
    stats: MutableMapping[str, int] = field(default_factory=dict)
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    adjacency: MutableMapping[str, Any] = field(default_factory=dict)
    diagnostics: MutableMapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "graph_version": self.graph_version,
            "generated_at": self.generated_at,
            "repo_identity": dict(self.repo_identity),
            "extractor_identity": dict(self.extractor_identity),
            "stats": dict(self.stats),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "adjacency": dict(self.adjacency),
            "diagnostics": dict(self.diagnostics),
        }

