from __future__ import annotations

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

    # Minimal additive signal only; avoid noisy empty payloads.
    if not any([inheritance, flow_paths, call_paths, concepts]):
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
        "graph_schema_version": str(manifest.get("schema_version") or ""),
        "graph_content_hash": str(manifest.get("content_hash") or ""),
    }

