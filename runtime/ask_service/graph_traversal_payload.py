from __future__ import annotations

import re
from collections import deque
from pathlib import Path
from typing import Any, Dict, Optional

from runtime.layer5.graph import (
    get_call_chain,
    get_concept_owners,
    get_entrypoint_flow,
    get_inheritance_chain,
    load_graph_artifacts,
    validate_graph_integrity,
)


def _runtime_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_graph_dir() -> Path:
    return _runtime_root() / ".cache" / "code_intelligence_graph"


def probe_code_intelligence_graph_availability(
    graph_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Non-throwing probe so clients can tell missing cache from empty traversal.
    """
    gdir = graph_dir or _default_graph_dir()
    if not gdir.exists():
        return {
            "artifact_status": "missing",
            "reason": "directory_not_found",
            "path_hint": str(gdir),
        }
    try:
        load_graph_artifacts(gdir)
        return {"artifact_status": "present", "path_hint": str(gdir)}
    except Exception as exc:
        return {
            "artifact_status": "missing",
            "reason": "load_failed",
            "detail": str(exc)[:240],
            "path_hint": str(gdir),
        }


def _is_structural_query(query: str) -> bool:
    q = (query or "").lower()
    return any(x in q for x in ("base class", "parent class", "extends", "implements"))


def _is_explain_query(query: str) -> bool:
    q = (query or "").lower()
    return any(x in q for x in ("how", "explain", "architecture", "work", "flow"))


def _is_debug_query(query: str, task_type: str) -> bool:
    q = (query or "").lower()
    return str(task_type or "").upper() == "EXPLAIN_DEBUG" or ("debug" in q or "why" in q)


def _is_discovery_query(query: str) -> bool:
    q = (query or "").lower()
    return ("find" in q or "list" in q or "all" in q) and ("class" in q or "classes" in q)


def _select_owner_class(authority_resolution: Optional[Dict[str, Any]], selected_file: str = "") -> str:
    if isinstance(authority_resolution, dict):
        po = authority_resolution.get("primary_owner")
        if isinstance(po, dict):
            cls = str(po.get("class") or "").strip()
            if cls:
                return cls
    if selected_file:
        name = Path(selected_file).stem
        if name:
            return name
    return ""


def _select_owner_method(authority_resolution: Optional[Dict[str, Any]], default: str = "start") -> str:
    if isinstance(authority_resolution, dict):
        po = authority_resolution.get("primary_owner")
        if isinstance(po, dict):
            method = str(po.get("method") or "").strip()
            if method:
                return method
    return default


def _select_concept_id(query: str, authority_resolution: Optional[Dict[str, Any]]) -> str:
    if isinstance(authority_resolution, dict):
        matched = authority_resolution.get("matched_concepts")
        if isinstance(matched, list) and matched:
            first = matched[0]
            if isinstance(first, dict):
                cid = str(first.get("concept_id") or "").strip()
                if cid:
                    return cid
    q = (query or "").lower()
    if "notification" in q:
        return "notification_dispatch"
    if "mail" in q:
        return "mail_server_configuration"
    if "api" in q:
        return "api_request_routing"
    return ""


def _node_maps(graph: Any) -> tuple[dict[str, Any], dict[str, str]]:
    nodes_by_id = {n.id: n for n in graph.nodes}
    labels_by_id = {n.id: n.label for n in graph.nodes}
    return nodes_by_id, labels_by_id


def _query_tokens(query: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (query or "").lower()) if len(t) >= 3}


def _extract_class_label(label: str) -> str:
    if "." in label:
        return label.split(".", 1)[0]
    return label


def _score_expanded_label(label: str, query_tokens: set[str]) -> int:
    low = label.lower()
    score = 0
    if any(tok in low for tok in query_tokens):
        score += 3
    for pattern in ("api", "config", "notification", "manager", "store", "handler"):
        if pattern in low:
            score += 1
    return score


def _expand_graph_context(
    graph: Any,
    *,
    query: str,
    seed_labels: list[str],
    max_nodes: int = 8,
    max_hops: int = 2,
) -> tuple[list[str], list[str]]:
    if not seed_labels:
        return [], []

    nodes_by_id, labels_by_id = _node_maps(graph)
    forward = graph.adjacency.get("forward", {})
    reverse = graph.adjacency.get("reverse", {})
    qtokens = _query_tokens(query)
    allowed = {
        "EXTENDS",
        "CALLS",
        "ENTRYPOINT_INVOKES",
        "REGISTERS_ROUTE",
        "CONCEPT_OWNS",
        "CONCEPT_COLLABORATES_WITH",
    }

    seed_ids: list[str] = []
    seed_labels_set = {s for s in seed_labels if s}
    for nid, label in labels_by_id.items():
        if label in seed_labels_set:
            seed_ids.append(nid)
            continue
        if any(seed and seed.lower() in label.lower() for seed in seed_labels_set):
            seed_ids.append(nid)
    if not seed_ids:
        return [], []

    visited: set[str] = set(seed_ids)
    queue: deque[tuple[str, int]] = deque((sid, 0) for sid in sorted(set(seed_ids)))
    candidate_edges: set[tuple[str, str, str]] = set()

    while queue:
        current, hops = queue.popleft()
        if hops >= max_hops:
            continue
        next_nodes: list[str] = []
        for etype in sorted(allowed):
            for dst in sorted(set(forward.get(current, {}).get(etype, []))):
                candidate_edges.add((current, etype, dst))
                next_nodes.append(dst)
            for src in sorted(set(reverse.get(current, {}).get(etype, []))):
                candidate_edges.add((src, etype, current))
                next_nodes.append(src)
        for nxt in sorted(set(next_nodes)):
            if nxt in visited:
                continue
            visited.add(nxt)
            queue.append((nxt, hops + 1))

    seed_class_labels = {_extract_class_label(labels_by_id[sid]) for sid in seed_ids if sid in labels_by_id}
    scored: list[tuple[int, str]] = []
    for nid in visited:
        node = nodes_by_id.get(nid)
        if node is None:
            continue
        if getattr(node, "kind", "") not in ("class", "method", "entrypoint", "concept"):
            continue
        label = labels_by_id.get(nid, nid)
        cls_label = _extract_class_label(label)
        score = _score_expanded_label(label, qtokens)
        if cls_label in seed_class_labels:
            score -= 2
        scored.append((score, label))

    selected: list[str] = []
    for _, label in sorted(scored, key=lambda x: (-x[0], x[1])):
        if label in seed_labels_set or label in selected:
            continue
        selected.append(label)
        if len(selected) >= max_nodes:
            break

    selected_set = set(selected) | seed_labels_set
    rendered_edges = sorted(
        {
            f"{labels_by_id.get(src, src)} -> {etype} -> {labels_by_id.get(dst, dst)}"
            for src, etype, dst in candidate_edges
            if labels_by_id.get(src, src) in selected_set and labels_by_id.get(dst, dst) in selected_set
        }
    )
    return selected, rendered_edges[: max_nodes * 2]


def build_graph_traversal_payload(
    *,
    query: str,
    task_type: str,
    authority_resolution: Optional[Dict[str, Any]] = None,
    selected_file: str = "",
    graph_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build optional, additive graph traversal payload for Ask responses.

    Returns None when graph artifacts are unavailable/invalid or when no relevant
    traversal signal is found for the query intent.
    """
    gdir = graph_dir or _default_graph_dir()
    try:
        graph, manifest = load_graph_artifacts(gdir)
    except Exception:
        return None

    integrity = validate_graph_integrity(graph)
    if not integrity.passed:
        return None

    owner_class = _select_owner_class(authority_resolution, selected_file=selected_file)
    owner_method = _select_owner_method(authority_resolution)
    method_key = f"{owner_class}.{owner_method}" if owner_class else ""
    route_hint = method_key or selected_file or owner_class

    inheritance: list[str] = []
    flow_paths: list[str] = []
    call_paths: list[str] = []
    concepts: Dict[str, Any] = {}
    expanded_nodes: list[str] = []
    expanded_edges: list[str] = []

    if _is_structural_query(query) and owner_class:
        inheritance = get_inheritance_chain(graph, owner_class)
    if _is_explain_query(query) and route_hint:
        flow_paths = get_entrypoint_flow(graph, route_hint)
    if _is_debug_query(query, task_type) and method_key:
        call_paths = get_call_chain(graph, method_key)
    if _is_discovery_query(query) or "notification" in (query or "").lower():
        concept_id = _select_concept_id(query, authority_resolution)
        if concept_id:
            concepts = get_concept_owners(graph, concept_id)
            concepts["concept_id"] = concept_id

    seed_labels = []
    if owner_class:
        seed_labels.append(owner_class)
    if method_key:
        seed_labels.append(method_key)
    seed_labels.extend(inheritance[:2])
    seed_labels.extend([p.split("->")[0].strip() for p in flow_paths[:2] if p])
    seed_labels.extend(list(concepts.get("owners") or [])[:2])
    seed_labels.extend(list(concepts.get("collaborators") or [])[:2])
    expanded_nodes, expanded_edges = _expand_graph_context(graph, query=query, seed_labels=seed_labels)

    # Minimal additive signal only; avoid noisy empty payloads.
    if not any([inheritance, flow_paths, call_paths, concepts, expanded_nodes]):
        return None

    return {
        "inheritance": inheritance,
        "flow_paths": flow_paths,
        "call_paths": call_paths,
        "concepts": concepts,
        # Backward-compatible convenience keys used by existing shaper path.
        "inheritance_chain": inheritance,
        "entrypoint_flow": flow_paths,
        "call_chain": call_paths,
        "owners": list(concepts.get("owners") or []),
        "collaborators": list(concepts.get("collaborators") or []),
        "expanded_nodes": expanded_nodes,
        "expanded_edges": expanded_edges,
        "graph_schema_version": str(manifest.get("schema_version") or ""),
        "graph_content_hash": str(manifest.get("content_hash") or ""),
    }

