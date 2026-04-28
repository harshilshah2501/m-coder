from __future__ import annotations

from typing import Dict, List, Set, Tuple

from runtime.layer5.graph.models import CodeIntelligenceGraph


def _node_lookup(graph: CodeIntelligenceGraph) -> Dict[str, str]:
    return {n.id: n.label for n in graph.nodes}


def get_inheritance_chain(graph: CodeIntelligenceGraph, class_name: str) -> List[str]:
    labels = _node_lookup(graph)
    node = f"class::{class_name}"
    chain: List[str] = []
    visited: Set[str] = set()
    forward = graph.adjacency.get("forward", {})
    while node and node not in visited:
        visited.add(node)
        chain.append(labels.get(node, node))
        parents = list(forward.get(node, {}).get("EXTENDS", []))
        node = parents[0] if parents else ""
    return chain


def get_call_chain(graph: CodeIntelligenceGraph, method_id: str, max_hops: int = 3) -> List[str]:
    labels = _node_lookup(graph)
    node = method_id if method_id.startswith("method::") else f"method::{method_id}"
    forward = graph.adjacency.get("forward", {})
    paths: List[List[str]] = [[node]]
    finished: List[List[str]] = []
    while paths:
        path = paths.pop(0)
        current = path[-1]
        depth = len(path) - 1
        targets = sorted(set(forward.get(current, {}).get("CALLS", [])))
        if depth >= max_hops or not targets:
            finished.append(path)
            continue
        extended = False
        for target in targets:
            if target in path:
                continue
            paths.append(path + [target])
            extended = True
        if not extended:
            finished.append(path)

    # Keep unique path strings with deterministic ordering.
    rendered = sorted(
        {
            " -> ".join(labels.get(n, n) for n in path)
            for path in finished
            if path
        }
    )
    return rendered


def get_entrypoint_flow(graph: CodeIntelligenceGraph, route_or_handler: str) -> List[str]:
    labels = _node_lookup(graph)
    forward = graph.adjacency.get("forward", {})
    # Route/handler is resolved by prefix matching node label.
    entry_candidates = [
        n.id
        for n in graph.nodes
        if n.kind in ("entrypoint", "method") and route_or_handler.lower() in n.label.lower()
    ]
    if not entry_candidates:
        return []
    completed: Set[Tuple[str, ...]] = set()
    queue: List[List[str]] = [[entry] for entry in sorted(entry_candidates)]
    while queue:
        path = queue.pop(0)
        current = path[-1]
        if len(path) > 6:
            completed.add(tuple(path))
            continue
        invokes = sorted(set(forward.get(current, {}).get("ENTRYPOINT_INVOKES", [])))
        routes = sorted(set(forward.get(current, {}).get("REGISTERS_ROUTE", [])))
        targets = invokes or routes
        if not targets:
            completed.add(tuple(path))
            continue
        extended = False
        for nxt in targets:
            if nxt in path:
                continue
            queue.append(path + [nxt])
            extended = True
        if not extended:
            completed.add(tuple(path))
    return sorted(" -> ".join(labels.get(n, n) for n in path) for path in completed if path)


def get_concept_owners(graph: CodeIntelligenceGraph, concept_id: str) -> Dict[str, List[str]]:
    labels = _node_lookup(graph)
    concept_node = concept_id if concept_id.startswith("concept::") else f"concept::{concept_id}"
    forward = graph.adjacency.get("forward", {})
    owners = [labels.get(n, n) for n in forward.get(concept_node, {}).get("CONCEPT_OWNS", [])]
    collaborators = [
        labels.get(n, n)
        for n in forward.get(concept_node, {}).get("CONCEPT_COLLABORATES_WITH", [])
    ]
    return {"owners": owners, "collaborators": collaborators}

